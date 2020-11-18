from enum import Enum
from tempfile import mkdtemp
from glob import glob

import json
import os

import easyvvuq as uq
from qcg.pilotjob.api.job import Jobs
from qcg.pilotjob.api.manager import LocalManager

from eqi.core.task import TaskType
from eqi.core.submit_order import SubmitOrder

EQI_STATE_FILE_NAME = '.eqi_state.json'


class Executor:
    """Integrates EasyVVUQ and QCG-PilotJob Manager

    Executor allows to process the most demanding operations of EasyVVUQ in parallel
    using QCG-PilotJob.

    """

    def __init__(self, campaign, config_file=None):
        self._qcgpjm = None
        self._campaign = campaign
        self._tasks = {}
        self._eqi_dir = "."
        self._config_file = None

        print("Campaign dir: " + self._campaign.campaign_dir)

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
                       resume=True,
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
        resume: bool, optional
            By default EQI will try to resume not completed workflow of QCG-PJ tasks from the point where
            it was previously stopped. If this is not intended this parameter should be set to False.
        log_level : str, optional
            Logging level for QCG-PilotJob Manager (for both service and client part).

        Returns
        -------
        None

        """

        # ---- QCG PILOT JOB INITIALISATION ---

        if resume:
            resume = self.__try_to_prepare_resume()

        if resume:
            print("EQI resuming in dir: " + self._eqi_dir)
        else:
            self._eqi_dir = mkdtemp(None, ".eqi-", self._campaign.campaign_dir)
            print("EQI starting in dir: " + self._eqi_dir)

        # Establish logging levels
        log_level = log_level.upper()

        try:
            service_log_level = ServiceLogLevel[log_level].value
        except KeyError:
            service_log_level = ServiceLogLevel.DEBUG.value

        try:
            client_log_level = ClientLogLevel[log_level].value
        except KeyError:
            client_log_level = ClientLogLevel.DEBUG.value

        # Prepare input arguments for QCG-PJM
        client_conf = {'log_file': self._eqi_dir + '/api.log', 'log_level': client_log_level}

        common_args = ['--log', service_log_level,
                       '--wd', self._eqi_dir]

        args = common_args

        if resources:
            args.append('--nodes')
            args.append(str(resources))

        if reserve_core:
            args.append('--system-core')

        if resume:
            args.append('--resume')
            args.append(self._eqi_dir)

        # create QCGPJ Manager (service part)
        self._qcgpjm = LocalManager(args, client_conf)

        # if we resuming QCG-PJM, we need to wait for completion of previously submitted tasks
        if resume:
            print("Waiting on completion of resumed workflow")
            self.__wait_and_sync()

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
        self.__submit_jobs(submit_order)
        self.__wait_and_sync()

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
                "wd": self._eqi_dir,
                "stdout": self._eqi_dir + '/encode_' + key + '.stdout',
                "stderr": self._eqi_dir + '/encode_' + key + '.stderr'
            }
        }

        self.__fill_task_with_common_params(encode_task, task.get_requirements())

        return encode_task

    def _get_encoding_task_iterative(self, campaign, run_max, run_min=0):

        task = self._tasks.get(TaskType.ENCODING)
        model = task.get_model()

        key = "Run_${it}"

        enc_args = [
            campaign.db_type,
            campaign.db_location,
            'FALSE',
            campaign.campaign_name,
            campaign._active_app_name,
            key
        ]

        encode_task = {
            "name": "encode",
            "iteration": {"stop": run_max + 1, "start": run_min},
            "execution": {
                "model": model,
                "exec": 'easyvvuq_encode',
                "args": enc_args,
                "wd": self._eqi_dir,
                "stdout": f"{self._eqi_dir}/encode_{key}.stdout",
                "stderr": f"{self._eqi_dir}/encode_{key}.stderr"
            }
        }

        self.__fill_task_with_common_params(encode_task, task.get_requirements())

        return encode_task

    def _get_exec_task(self, campaign, run):

        task = self._tasks.get(TaskType.EXECUTION)
        application = task.get_params().get("application")
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
                "wd": self._eqi_dir,
                "stdout": self._eqi_dir + '/execute_' + key + '.stdout',
                "stderr": self._eqi_dir + '/execute_' + key + '.stderr'
            },
            "dependencies": {
                "after": ["encode_" + key]
            }
        }

        self.__fill_task_with_common_params(execute_task, task.get_requirements())

        return execute_task

    def _get_exec_task_iterative(self, campaign, run_max, run_min=0):

        task = self._tasks.get(TaskType.EXECUTION)
        application = task.get_params().get("application")
        model = task.get_model()

        key = "Run_${it}"
        run_dir = f"{campaign.campaign_dir}/runs/{key}"

        exec_args = [
            run_dir,
            'easyvvuq_app',
            application
        ]

        execute_task = {
            "name": "execute",
            "iteration": {"stop": run_max + 1, "start": run_min},
            "execution": {
                "model": model,
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "wd": self._eqi_dir,
                "stdout": f"{self._eqi_dir}/execute_{key}.stdout",
                "stderr": f"{self._eqi_dir}/execute_{key}.stderr"
            },
            "dependencies": {
                "after": ["encode"]
            }
        }

        self.__fill_task_with_common_params(execute_task, task.get_requirements())

        return execute_task

    def _get_encoding_and_exec_task(self, campaign, run):

        task = self._tasks.get(TaskType.ENCODING_AND_EXECUTION)
        application = task.get_params().get("application")
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
                "wd": self._eqi_dir,
                "stdout": self._eqi_dir + '/encode_execute_' + key + '.stdout',
                "stderr": self._eqi_dir + '/encode_execute_' + key + '.stderr'
            }
        }

        self.__fill_task_with_common_params(encode_execute_task, task.get_requirements())

        return encode_execute_task

    def _get_encoding_and_exec_task_iterative(self, campaign, run_max, run_min=0):

        task = self._tasks.get(TaskType.ENCODING_AND_EXECUTION)
        application = task.get_params().get("application")
        model = task.get_model()

        key = "Run_${it}"
        run_dir = f"{campaign.campaign_dir}/runs/{key}"

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
            "name": 'encode_execute',
            "iteration": {"stop": run_max + 1, "start": run_min},
            "execution": {
                "model": model,
                "exec": 'easyvvuq_encode_execute',
                "args": args,
                "wd": self._eqi_dir,
                "stdout": f"{self._eqi_dir}/encode_execute_{key}.stdout",
                "stderr": f"{self._eqi_dir}/encode_execute_{key}.stderr"
            }
        }

        self.__fill_task_with_common_params(encode_execute_task, task.get_requirements())

        return encode_execute_task

    def _get_exec_only_task(self, campaign, run):

        task = self._tasks.get(TaskType.EXECUTION)
        application = task.get_params().get("application")
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
                "wd": self._eqi_dir,
                "stdout": self._eqi_dir + '/execute_' + key + '.stdout',
                "stderr": self._eqi_dir + '/execute_' + key + '.stderr'
            }
        }

        self.__fill_task_with_common_params(execute_task, task.get_requirements())
        return execute_task

    def _get_exec_only_task_iterative(self, campaign, run_max, run_min=0):

        task = self._tasks.get(TaskType.EXECUTION)
        application = task.get_params().get("application")
        model = task.get_model()

        key = "Run_${it}"
        run_dir = f"{campaign.campaign_dir}/runs/{key}"

        exec_args = [
            run_dir,
            'easyvvuq_app',
            application
        ]

        execute_task = {
            "name": 'execute',
            "iteration": {"stop": run_max + 1, "start": run_min},
            "execution": {
                "model": model,
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "wd": self._eqi_dir,
                "stdout": f"{self._eqi_dir}/execute_{key}.stdout",
                "stderr": f"{self._eqi_dir}/execute_{key}.stderr"
            }
        }

        self.__fill_task_with_common_params(execute_task, task.get_requirements())
        return execute_task

    def __try_to_prepare_resume(self):
        eqi_dirs = glob(f'{self._campaign.campaign_dir}/.eqi-*')

        if eqi_dirs.__len__() > 0:
            resume_dir = eqi_dirs[0]    # we get the first eqi-* dir, TODO: get specific one
            self._eqi_dir = resume_dir
            print("Existing EQI directory found: ", resume_dir)
        else:
            print("No EQI directory found - can't resume")
            return False

        if 'submitted' in self.__get_from_state_file():  # jobs need to be submitted in order to resume
            print("Resume directory ready for use")
            return True
        else:
            print("The EQI not in the submitted state - can't resume")
            return False

    def __fill_task_with_common_params(self, task, requirements):

        if requirements:
            task.update(requirements.get_resources())
        if self._config_file:
            task["execution"].update({"env": {"EQI_CONFIG": self._config_file}})

    def __submit_jobs(self, submit_order):

        print("Starting submission of tasks to QCG-PilotJob Manager in a submit order: " + submit_order.name)
        if submit_order.is_iterative():
            self.__submit_iterative_jobs(submit_order)
        else:
            self.__submit_separate_jobs(submit_order)
        print("Jobs submitted")

        # Store information to the state file that the jobs has been already submitted
        self.__write_to_state_file({'submitted': True})

    def __submit_separate_jobs(self, submit_order):

        sampler = self._campaign._active_sampler_id

        if submit_order == SubmitOrder.RUN_ORIENTED_CONDENSED:
            for run in self._campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().add_std(
                    self._get_encoding_and_exec_task(self._campaign, run)))

        elif submit_order == SubmitOrder.RUN_ORIENTED:
            for run in self._campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().add_std(self._get_encoding_task(self._campaign, run)))
                self._qcgpjm.submit(Jobs().add_std(self._get_exec_task(self._campaign, run)))

        elif submit_order == SubmitOrder.PHASE_ORIENTED:
            for run in self._campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().add_std(self._get_encoding_task(self._campaign, run)))
            for run in self._campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().add_std(self._get_exec_task(self._campaign, run)))

        elif submit_order == SubmitOrder.EXEC_ONLY:
            for run in self._campaign.list_runs(sampler):
                self._qcgpjm.submit(Jobs().add_std(self._get_exec_only_task(self._campaign, run)))

    def __submit_iterative_jobs(self, submit_order):

        sampler = self._campaign._active_sampler_id

        list_runs = self._campaign.list_runs(sampler)
        min_run = int(list_runs[0][0][len("Run_"):])
        max_run = int(list_runs[len(list_runs) - 1][0][len("Run_"):])

        if len(list_runs) != max_run - min_run + 1:
            raise ValueError("Number of runs in a list is not homogeneous with their keys. "
                             "The iterative SubmitOrder can't be applied")

        if submit_order == SubmitOrder.PHASE_ORIENTED_ITERATIVE:
            self._qcgpjm.submit(Jobs().add_std(
                self._get_encoding_task_iterative(self._campaign, max_run, min_run)))
            self._qcgpjm.submit(Jobs().add_std(
                self._get_exec_task_iterative(self._campaign, max_run, min_run)))
        elif submit_order == SubmitOrder.RUN_ORIENTED_CONDENSED_ITERATIVE:
            self._qcgpjm.submit(Jobs().add_std(
                self._get_encoding_and_exec_task_iterative(self._campaign, max_run, min_run)))
        elif submit_order == SubmitOrder.EXEC_ONLY_ITERATIVE:
            self._qcgpjm.submit(Jobs().add_std(
                self._get_exec_only_task_iterative(self._campaign, max_run, min_run)))

    def __wait_and_sync(self):

        # TODO: mark that tasks have been submitted

        # wait for completion of all PJ tasks
        self._qcgpjm.wait4all()

        print("Syncing state of campaign after execution of PJ")

        def update_status(run_id, run_data):
            self._campaign.campaign_db.set_run_statuses([run_id], uq.constants.Status.ENCODED)

        self._campaign.call_for_each_run(update_status, status=uq.constants.Status.NEW)
        self.__write_to_state_file({'completed': True})
        print("Campaign synced")

    def __write_to_state_file(self, data):

        eqi_file_loc = f'{self._eqi_dir}/{EQI_STATE_FILE_NAME}'

        if os.path.exists(eqi_file_loc):
            with open(eqi_file_loc, 'r') as eqi_file:
                state_dict = json.load(eqi_file)
                state_dict.update(data)
        else:
            state_dict = data

        with open(eqi_file_loc, 'w') as eqi_file:
            json.dump(state_dict, eqi_file)

    def __get_from_state_file(self):

        eqi_file_loc = f'{self._eqi_dir}/{EQI_STATE_FILE_NAME}'
        if os.path.exists(eqi_file_loc):
            with open(eqi_file_loc, 'r') as eqi_file:
                state_dict = json.load(eqi_file)
        else:
            state_dict = {}

        return state_dict


class ServiceLogLevel(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class ClientLogLevel(Enum):
    INFO = "info"
    DEBUG = "debug"
