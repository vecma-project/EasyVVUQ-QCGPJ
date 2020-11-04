from enum import Enum
from tempfile import mkdtemp

import os
import easyvvuq as uq
from qcg.pilotjob.api.job import Jobs
from qcg.pilotjob.api.manager import LocalManager

from eqi.core.task import TaskType
from eqi.core.submit_order import SubmitOrder


class Executor:
    """Integrates EasyVVUQ and QCG-PilotJob Manager

    Executor allows to process the most demanding operations of EasyVVUQ in parallel
    using QCG-PilotJob.

    """
    def __init__(self, campaign, config_file=None):
        self._qcgpjm = None
        self._campaign = campaign
        self._tasks = {}
        self._qcgpj_tempdir = "."
        self._config_file = None

        self._qcgpj_tempdir = mkdtemp(None, ".qcgpj-", self._campaign.campaign_dir)
        print("Campaign dir:" + self._campaign.campaign_dir)
        print("QCG-PJ temp dir:" + self._qcgpj_tempdir)

        if config_file:
            self._config_file = config_file
            print("EQI config file for tasks (from param): " + self._config_file)
        elif 'EQI_CONFIG' in os.environ:
            self._config_file = os.environ['EQI_CONFIG']
            print("EQI config file for tasks (from environment variable): " + self._config_file)

        """
        Parameters
        ----------
        campaign: easyvvuq.Campaign
            The campaign object that will be processed by QCG-PilotJob.
            It has to be previously initialised.
        config_file: str, optional
            The path to config file being sourced in a prelude of each of QCG-PilotJob tasks.
        """

    def create_manager(self,
                       resources=None,
                       reserve_core=False,
                       log_level='debug'):
        """Creates new QCG-PilotJob Manager and sets is as the Executor's engine.

        Parameters
        ----------
        resources : str, optional
            The resources to use. If specified forces usage of Local mode of QCG-PilotJob Manager.
            The format is compliant with the NODES format of QCG-PilotJob, i.e.:
            [node_name:]cores_on_node[,node_name2:cores_on_node][,...].
            Eg. to run on 4 cores regardless the node use `resources="4"`
            to run on 2 cores of node_1 and on 3 cores of node_2 use `resources="node_1:2,node_2:3"`
        reserve_core : bool, optional
            If True reserves a core for QCG-PilotJob Manager instance,
            by default QCG-PilotJob Manager shares a core with computing tasks
            Parameters.
        log_level : str, optional
            Logging level for QCG-PilotJob Manager (for both service and client part).

        Returns
        -------
        None

        """

        # ---- QCG PILOT JOB INITIALISATION ---
        log_level = log_level.upper()

        try:
            service_log_level = ServiceLogLevel[log_level].value
        except KeyError:
            service_log_level = ServiceLogLevel.DEBUG.value

        try:
            client_log_level = ClientLogLevel[log_level].value
        except KeyError:
            client_log_level = ClientLogLevel.DEBUG.value

        client_conf = {'log_file': self._qcgpj_tempdir + '/api.log', 'log_level': client_log_level}

        common_args = ['--log', service_log_level,
                       '--wd', self._qcgpj_tempdir]

        args = common_args

        if resources:
            args.append('--nodes')
            args.append(str(resources))

        if reserve_core:
            args.append('--system-core')

        # create QCGPJ Manager (service part)
        self._qcgpjm = LocalManager(args, client_conf)

    def set_manager(self, qcgpjm):
        """Sets existing QCG-PilotJob Manager as the Executor's engine

        Parameters
        ----------
        qcgpjm : qcg.pilotjob.api.manager.Manager
            Existing instance of a QCG-PilotJob Manager

        Returns
        -------
        None

        """
        self._qcgpjm = qcgpjm

        print("Available resources:\n%s\n" % str(self._qcgpjm.resources()))

    def add_task(self, task):
        """
        Add a task to execute with QCG PJ

        Parameters
        ----------
        task: Task
            The task that will be added to the execution workflow

        Returns
        -------
        None

        """
        self._tasks[task.get_name()] = task

    def run(self, submit_order=SubmitOrder.RUN_ORIENTED):
        """ Executes demanding parts of EasyVVUQ campaign with QCG-PilotJob

        A user may choose the preferred execution scheme for the given scenario.

        Parameters
        ----------
        submit_order: SubmitOrder
            EasyVVUQ tasks submission order

        Returns
        -------
        None
        """
        # ---- EXECUTION ---
        # Execute encode -> execute for each run using QCG-PJ
        self.__submit_jobs(self._campaign, submit_order)

        # wait for completion of all PJ tasks
        self._qcgpjm.wait4all()

        print("Syncing state of campaign after execution of PJ")

        def update_status(run_id, run_data):
            self._campaign.campaign_db.set_run_statuses([run_id], uq.constants.Status.ENCODED)

        self._campaign.call_for_each_run(update_status, status=uq.constants.Status.NEW)

    def print_resources_info(self):
        """ Displays resources assigned to QCG-PilotJob Manager
        """
        print("Available resources:\n%s\n" % str(self._qcgpjm.resources()))

    def terminate_manager(self):
        """ Terminates QCG-PilotJob Manager
        """

        self._qcgpjm.finish()
        self._qcgpjm.kill_manager_process()
        self._qcgpjm.cleanup()

    def _get_encoding_task(self, campaign, run):

        task = self._tasks.get(TaskType.ENCODING)
        requirements = task.get_requirements()
        model = task.get_model()

        key = run[0]

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
                "model": model,
                "exec": 'easyvvuq_encode',
                "args": enc_args,
                "wd": self._qcgpj_tempdir,
                "stdout": self._qcgpj_tempdir + '/encode_' + key + '.stdout',
                "stderr": self._qcgpj_tempdir + '/encode_' + key + '.stderr'
            }
        }

        if self._config_file:
            encode_task["execution"].update({"env": {"EQI_CONFIG": self._config_file}})

        if requirements:
            encode_task.update(requirements.get_resources())

        return encode_task

    def _get_exec_task(self, campaign, run):

        task = self._tasks.get(TaskType.EXECUTION)
        application = task.get_params().get("application")
        requirements = task.get_requirements()
        model = task.get_model()

        key = run[0]
        run_dir = run[1]['run_dir']

        exec_args = [
            run_dir,
            'easyvvuq_app',
            application
        ]

        execute_task = {
            "name": 'execute_' + key,
            "execution": {
                "model": model,
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "wd": self._qcgpj_tempdir,
                "stdout": self._qcgpj_tempdir + '/execute_' + key + '.stdout',
                "stderr": self._qcgpj_tempdir + '/execute_' + key + '.stderr'
            },
            "dependencies": {
                "after": ["encode_" + key]
            }
        }

        if self._config_file:
            execute_task["execution"].update({"env": {"EQI_CONFIG": self._config_file}})

        if requirements:
            execute_task.update(requirements.get_resources())

        return execute_task

    def _get_encoding_and_exec_task(self, campaign, run):

        task = self._tasks.get(TaskType.ENCODING_AND_EXECUTION)
        application = task.get_params().get("application")
        requirements = task.get_requirements()
        model = task.get_model()

        key = run[0]
        run_dir = run[1]['run_dir']

        args = [
            campaign.db_type,
            campaign.db_location,
            'FALSE',
            campaign.campaign_name,
            campaign._active_app_name,
            key,

            run_dir,
            'easyvvuq_app',
            application
        ]

        encode_execute_task = {
            "name": 'encode_execute_' + key,
            "execution": {
                "model": model,
                "exec": 'easyvvuq_encode_execute',
                "args": args,
                "wd": self._qcgpj_tempdir,
                "stdout": self._qcgpj_tempdir + '/encode_execute_' + key + '.stdout',
                "stderr": self._qcgpj_tempdir + '/encode_execute_' + key + '.stderr'
            }
        }

        if self._config_file:
            encode_execute_task["execution"].update({"env": {"EQI_CONFIG": self._config_file}})

        if requirements:
            encode_execute_task.update(requirements.get_resources())

        return encode_execute_task

    def _get_exec_only_task(self, campaign, run):

        task = self._tasks.get(TaskType.EXECUTION)
        application = task.get_params().get("application")
        requirements = task.get_requirements()
        model = task.get_model()

        key = run[0]
        run_dir = run[1]['run_dir']

        exec_args = [
            run_dir,
            'easyvvuq_app',
            application
        ]

        execute_task = {
            "name": 'execute_' + key,
            "execution": {
                "model": model,
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "wd": self._qcgpj_tempdir,
                "stdout": self._qcgpj_tempdir + '/execute_' + key + '.stdout',
                "stderr": self._qcgpj_tempdir + '/execute_' + key + '.stderr'
            }
        }

        if self._config_file:
            execute_task["execution"].update({"env": {"EQI_CONFIG": self._config_file}})

        if requirements:
            execute_task.update(requirements.get_resources())

        return execute_task

    def __submit_jobs(self, campaign, submit_order):

        sampler = campaign._active_sampler_id

        print("Starting submission of tasks to QCG-PilotJob Manager")
        if submit_order == SubmitOrder.RUN_ORIENTED_CONDENSED:
            for run in campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().addStd(self._get_encoding_and_exec_task(campaign, run)))

        elif submit_order == SubmitOrder.RUN_ORIENTED:
            for run in campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().add_std(self._get_encoding_task(campaign, run)))
                self._qcgpjm.submit(Jobs().add_std(self._get_exec_task(campaign, run)))

        elif submit_order == SubmitOrder.PHASE_ORIENTED:
            for run in campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().add_std(self._get_encoding_task(campaign, run)))
            for run in campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().add_std(self._get_exec_task(campaign, run)))

        elif submit_order == SubmitOrder.EXEC_ONLY:
            for run in campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().add_std(self._get_exec_only_task(campaign, run)))


class ServiceLogLevel(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class ClientLogLevel(Enum):
    INFO = "info"
    DEBUG = "debug"
