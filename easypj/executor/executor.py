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
    def __init__(self):
        self._qcgpjm = None
        self._encoding_params = None
        self._exec_params = None

    def set_manager(self, qcgpjm):
        """Sets existing QCG Pilot Job Manager as the Executor's engine

        Parameters
        ----------
        qcgpjm : qcg.appscheduler.api.manager.Manager

        Returns
        -------
        None

        """

        self._qcgpjm = qcgpjm
        print("Available resources:\n%s\n" % str(self._qcgpjm.resources()))

    def create_manager(self, dir=".", resources=None, reserve_core=False):
        """Creates new QCG Pilot Job Manager and sets is as the Executor's engine

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
            Parameters

        Returns
        -------
        None

        """
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

    def configure_encoding_task(self, encoding_params):
        """
        Configures encoding task of EasyVVUQ execution with QCG PJ

        Parameters
        ----------
        encoding_params: encoding_params


        Returns
        -------
        None

        """
        self._encoding_params = encoding_params

    def configure_execution_task(self, exec_params):
        """
        Configures execution task of EasyVVUQ execution with QCG PJ

        Parameters
        ----------
        exec_params: exec_params


        Returns
        -------
        None

        """
        self._exec_params = exec_params

    def _get_encoding_task(self, campaign, run):

        key = run[0]

        enc_cores = 1

        if self._encoding_params:
            enc_cores = self._encoding_params.cores

        enc_args = [
            campaign.db_type,
            campaign.db_location,
            'FALSE',
            campaign.campaign_name,
            campaign._active_app_name,
            key
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

        return encode_task

    def _get_exec_task(self, campaign, run):

        exec_app = self._exec_params.app
        exec_cores = self._exec_params.cores

        key = run[0]
        run_dir = run[1]['run_dir']

        exec_args = [
            run_dir,
            'easyvvuq_app',
            exec_app
        ]

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

        return execute_task

    def run(self, campaign):
        """ Executes demanding parts of EasyVVUQ campaign with QCG Pilot Job

        A user may choose the preferred execution scheme for the given scenario.

        campaign : easyvvuq.campaign
            The campaign object that would be processed. It has to be previously initialised.
        """
        # ---- EXECUTION ---

        # Execute encode -> execute for each run using QCG-PJ
        print("Starting submission of tasks to QCG Pilot Job Manager")
        for run in campaign.list_runs():
            self._qcgpjm.submit(Jobs().addStd(self._get_encoding_task(campaign, run)))
            self._qcgpjm.submit(Jobs().addStd(self._get_exec_task(campaign, run)))

        # wait for completion of all PJ tasks and terminate the PJ manager
        self._qcgpjm.wait4all()
        self._qcgpjm.finish()
        self._qcgpjm.stopManager()
        self._qcgpjm.cleanup()

        print("Syncing state of campaign after execution of PJ")

        def update_status(run_id, run_data):
            campaign.campaign_db.set_run_statuses([run_id], uq.constants.Status.ENCODED)

        campaign.call_for_each_run(update_status, status=uq.constants.Status.NEW)
