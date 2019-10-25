from tempfile import mkdtemp

import easyvvuq as uq
from qcg.appscheduler.api.job import Jobs
from qcg.appscheduler.api.manager import LocalManager


class Executor:
    """Integrates EasyVVUQ and QCG Pilot Job manager

    Executor allows to process the most demanding operations of EasyVVUQ in parallel
    using QCG Pilot Job.


    Parameters
    ----------
    dir : str
        The path to the directory where Executor should init QCG Pilot Job Manager.
        Inside dir a subdirectory for workdir of QCG PJ manager will be created
    resources : str, optional
        The resources to use. If specified forces usage of Local mode of QCG Pilot Job Manager.
        The format is compliant with the NODES format of QCG Pilot Job, i.e.:
        [node_name:]cores_on_node[,node_name2:cores_on_node][,...].
        Eg. to run on 4 cores regardless the node use `resources="4"`
        to run on 2 cores of node_1 and on 3 cores of node_2 use `resources="node_1:2,node_2:3"`
    reserve_core : bool, optional
        If True reserves a core for QCG Pilot Job manager instance,
        by default QCG Pilot Job Manager shares a core with computing tasks

    """
    def __init__(self, dir=".", resources=None, reserve_core=False):
        self._dir = dir
        self._qcgpjm = None

        # ---- QCG PILOT JOB INITIALISATION ---
        # set QCG-PJ temp directory
        qcgpj_tempdir = mkdtemp(None, ".qcgpj-", dir)

        # switch on debugging of QCGPJ API (client part)
        client_conf = {'log_file': qcgpj_tempdir + '/api.log', 'log_level': 'DEBUG'}

        common_args = ['--log', 'debug',
                       '--wd', qcgpj_tempdir]

        args = common_args

        if resources:
            args.append('--nodes', str(resources))

        if reserve_core:
            args.append('--system-core')

        # create QCGPJ Manager (service part)
        self._qcgpjm = LocalManager(args, client_conf)

        print("Available resources:\n%s\n" % str(self._qcgpjm.resources()))

    def run(self, campaign, exec_params, encoding_params=None):
        """ Executes demanding parts of EasyVVUQ campaign with QCG Pilot Job

        A user may choose the preferred execution scheme for the given scenario.

        campaign : easyvvuq.campaign
            The campaign object that would be processed. It has to be previously initialised.
        encoding_params : encoding_params, optional
            The parameters for the encoding task
        exec_params : exec_params
            The parameters for the execution task
        """
        # ---- EXECUTION ---
        exec_app = exec_params.app
        exec_cores = exec_params.cores
        enc_cores = 1

        if encoding_params:
            enc_cores = encoding_params.cores

        # Execute encode -> execute for each run using QCG-PJ
        print("Starting submission of tasks to QCG Pilot Job Manager")
        for run in campaign.list_runs():

            key = run[0]
            run_dir = run[1]['run_dir']

            enc_args = [
                campaign.db_type,
                campaign.db_location,
                'FALSE',
                campaign.campaign_name,
                campaign._active_app_name,
                key
            ]

            exec_args = [
                run_dir,
                'easyvvuq_app',
                exec_app
            ]

            encode_task = {
                "name": 'encode_' + key,
                "execution": {
                    "exec": 'easyvvuq_encode',
                    "args": enc_args,
                    "wd": campaign.campaign_dir,
                    "stdout": campaign.campaign_dir + '/encode_' + key + '.stdout',
                    "stderr": campaign.campaign_dir + '/encode_' + key + '.stderr'
                },
                "resources": {
                    "numCores": {
                        "exact": enc_cores
                    }
                }
            }

            execute_task = {
                "name": 'execute_' + key,
                "execution": {
                    "exec": 'easyvvuq_execute',
                    "args": exec_args,
                    "wd": campaign.campaign_dir,
                    "stdout": campaign.campaign_dir + '/execute_' + key + '.stdout',
                    "stderr": campaign.campaign_dir + '/execute_' + key + '.stderr'
                },
                "resources": {
                    "numCores": {
                        "exact": exec_cores
                    }
                },
                "dependencies": {
                    "after": ["encode_" + key]
                }
            }

            self._qcgpjm.submit(Jobs().addStd(encode_task))
            self._qcgpjm.submit(Jobs().addStd(execute_task))

        # wait for completion of all PJ tasks and terminate the PJ manager
        self._qcgpjm.wait4all()
        self._qcgpjm.finish()
        self._qcgpjm.stopManager()
        self._qcgpjm.cleanup()

        print("Syncing state of campaign after execution of PJ")

        def update_status(run_id, run_data):
            campaign.campaign_db.set_run_statuses([run_id], uq.constants.Status.ENCODED)

        campaign.call_for_each_run(update_status, status=uq.constants.Status.NEW)
