import logging
import os

from enum import Enum
from os.path import exists, dirname, abspath
from tempfile import mkdtemp
from glob import glob

import easyvvuq as uq
from qcg.pilotjob.api.job import Jobs
from qcg.pilotjob.api.manager import LocalManager

from eqi.core.task import TaskType
from eqi.core.tasks_manager import TasksManager
from eqi.core.processing_scheme import ProcessingScheme
from eqi.utils.state_keeper import StateKeeper


class Executor:
    """Integrates EasyVVUQ and QCG-PilotJob Manager

    Executor allows to process the most demanding operations of EasyVVUQ in parallel
    using QCG-PilotJob.

    """

    def __init__(self, campaign, config_file=None, resume=True, log_level='info'):
        self._qcgpjm = None
        self._campaign = campaign
        self._eqi_dir = "."
        self._config_file = None
        self._resume = False
        self._tasks_manager = None

        print("EQI initialisation for the campaign: " + self._campaign.campaign_dir)

        self._setup_eqi_dir(resume)

        self.logger = self._setup_eqi_logging(log_level)

        if config_file:
            self._config_file = config_file
            self.logger.debug("EQI config file for tasks (from param): " + self._config_file)
        elif 'EQI_CONFIG' in os.environ:
            self._config_file = os.environ['EQI_CONFIG']
            self.logger.debug("EQI config file for tasks (from environment variable): "
                              + self._config_file)

        self._tasks_manager = TasksManager(self._campaign, self._eqi_dir, self._config_file)

        """
        Parameters
        ----------
        campaign: easyvvuq.Campaign
            The campaign object that will be processed by QCG-PilotJob.
            It has to be previously initialised.
        config_file: str, optional
            The path to config file being sourced in a prelude of each of QCG-PilotJob tasks.
        resume: bool, optional
            By default EQI will try to resume not completed workflow of QCG-PJ tasks from
            the point where it was previously stopped. If this is not intended
            this parameter should be set to False.
        log_level : str, optional
            Logging level for EQI.
        """

    def create_manager(self,
                       resources=None,
                       reserve_core=False,
                       log_level='info'):
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

        # Establish logging levels
        service_log_level, client_log_level = self._setup_qcgpj_logging(log_level)

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

        if self._resume:
            args.append('--resume')
            args.append(self._eqi_dir)

        self.logger.info(f'Starting QCG-PJ Manager with arguments: {args}')

        # create QCGPJ Manager (service part)
        self._qcgpjm = LocalManager(args, client_conf)

        self.logger.info(f"QCG-PJ Manager created - available resources: "
                         f"{self._qcgpjm.resources()}")

        # if we resuming QCG-PJM, we need to wait for completion of previously submitted tasks
        if self._resume:
            self.logger.info("Waiting on completion of resumed workflow")
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

        self.logger.info(f"QCG-PJ Manager set - available resources: "
                         f"{self._qcgpjm.resources()}")

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

        self._tasks_manager.add_task(task)
        self.logger.debug(f"New task added: {task.get_name()}")

    def run(self, processing_scheme=ProcessingScheme.SAMPLE_ORIENTED):
        """ Executes demanding parts of EasyVVUQ campaign with QCG-PilotJob

        A user may choose the preferred execution scheme for the given scenario.

        Parameters
        ----------
        processing_scheme: ProcessingScheme
            Tasks processing scheme

        Returns
        -------
        None
        """
        # ---- EXECUTION ---
        self._submit_jobs(processing_scheme)
        self.__wait_and_sync()

    def print_resources_info(self):
        """ Displays resources assigned to QCG-PilotJob Manager
        """
        print("Available resources:\n%s\n" % str(self._qcgpjm.resources()))

    def terminate_manager(self):
        """ Terminates QCG-PilotJob Manager
        """

        self._qcgpjm.finish()

    def _setup_eqi_logging(self, log_level):
        log_level = log_level.upper()

        eqi_log_file = f'{self._eqi_dir}/eqi.log'
        print(f'EQI log file set to {eqi_log_file}')

        if not exists(dirname(abspath(eqi_log_file))):
            os.makedirs(dirname(abspath(eqi_log_file)))
#        elif exists(eqi_log_file):
#            os.remove(eqi_log_file)

        _logger = logging.getLogger(__name__)

        if _logger.hasHandlers():
            _logger.handlers.clear()

        _log_handler = logging.FileHandler(filename=eqi_log_file, mode='a', delay=False)
        _log_handler.setFormatter(logging.Formatter('%(asctime)-15s: %(message)s'))
        _logger.addHandler(_log_handler)
        _logger.setLevel(log_level)

        return _logger

    def _setup_qcgpj_logging(self, log_level):
        log_level = log_level.upper()

        try:
            service_log_level = ServiceLogLevel[log_level].value
        except KeyError:
            service_log_level = ServiceLogLevel.DEBUG.value

        try:
            client_log_level = ClientLogLevel[log_level].value
        except KeyError:
            client_log_level = ClientLogLevel.DEBUG.value

        return service_log_level, client_log_level

    def _setup_eqi_dir(self, resume):

        self._resume = False

        if resume:
            eqi_dirs = glob(f'{self._campaign.campaign_dir}/.eqi-*')

            if eqi_dirs.__len__() > 0:
                resume_dir = eqi_dirs[0]    # we get the first eqi-* dir, TODO: get specific one
                print("Existing EQI directory found: ", resume_dir)
                self._eqi_dir = resume_dir
                self._state_keeper = StateKeeper(self._eqi_dir)
                self._state_keeper.setup(self._campaign)
                _dict = self._state_keeper.get_from_state_file()
                if 'submitted' in _dict and 'completed' not in _dict:
                    print("EQI resuming in dir: " + self._eqi_dir)
                    self._resume = True
                else:
                    print("The EQI not in the submitted state - can't resume")
            else:
                print("No EQI directory found - can't resume")

        # jobs need to be submitted in order to resume
        if self._resume is False:
            self._eqi_dir = mkdtemp(None, ".eqi-", self._campaign.campaign_dir)
            print("EQI starting in dir: " + self._eqi_dir)
            self._state_keeper = StateKeeper(self._eqi_dir)
            self._state_keeper.setup(self._campaign)

    def _submit_jobs(self, processing_scheme):

        self.logger.info("Starting submission of tasks to QCG-PilotJob Manager "
                         "in a processing scheme: " + processing_scheme.name)

        if processing_scheme.is_iterative():
            jobs = self._prepare_iterative_jobs(processing_scheme)
        else:
            jobs = self._prepare_separate_jobs(processing_scheme)

        if jobs and jobs.job_names():
            self._qcgpjm.submit(jobs)
            self.logger.info("Tasks submitted")
            # Store information to the state file that the jobs has been already submitted
            self._state_keeper.write_to_state_file({'submitted': True})
        else:
            self.logger.error("Tasks not submitted")
            # Store information to the state file that the jobs has been already submitted
            self._state_keeper.write_to_state_file({'submitted': False})

    def _prepare_separate_jobs(self, processing_scheme):

        sampler = self._campaign._active_sampler_id

        jobs = Jobs()

        if processing_scheme == ProcessingScheme.SAMPLE_ORIENTED_CONDENSED:
            for run in self._campaign.list_runs(sampler):
                jobs.add_std(self._tasks_manager.get_task(TaskType.ENCODING_AND_EXECUTION, key=run[0]))

        elif processing_scheme == ProcessingScheme.SAMPLE_ORIENTED:
            for run in self._campaign.list_runs(sampler):
                t1 = self._tasks_manager.get_task(TaskType.ENCODING, key=run[0])
                t2 = self._tasks_manager.get_task(
                    TaskType.EXECUTION, key=run[0], after=(t1['name'],))
                jobs.add_std(t1)
                jobs.add_std(t2)

        elif processing_scheme == ProcessingScheme.STEP_ORIENTED:
            wait_list = []
            for run in self._campaign.list_runs(sampler):
                t = self._tasks_manager.get_task(TaskType.ENCODING, key=run[0])
                jobs.add_std(t)
                wait_list.append(t['name'])

            i = 0
            for run in self._campaign.list_runs(sampler):
                jobs.add_std(self._tasks_manager.get_task(
                    TaskType.EXECUTION, key=run[0], after=(wait_list[i],)))
                i += 1

        elif processing_scheme == ProcessingScheme.EXEC_ONLY:
            for run in self._campaign.list_runs(sampler):
                jobs.add_std(self._tasks_manager.get_task(TaskType.EXECUTION, key=run[0]))

        return jobs

    def _prepare_iterative_jobs(self, processing_scheme):

        sampler = self._campaign._active_sampler_id

        list_runs = self._campaign.list_runs(sampler)
        min_run = int(list_runs[0][0][len("Run_"):])
        max_run = int(list_runs[len(list_runs) - 1][0][len("Run_"):])

        if len(list_runs) != max_run - min_run + 1:
            raise ValueError("Number of runs in a list is not homogeneous with their keys. "
                             "The iterative ProcessingScheme can't be applied")

        jobs = Jobs()

        if processing_scheme == ProcessingScheme.STEP_ORIENTED_ITERATIVE:
            t1 = self._tasks_manager.get_task(
                TaskType.ENCODING, key_min=min_run, key_max=max_run)
            t2 = self._tasks_manager.get_task(
                TaskType.EXECUTION, key_min=min_run, key_max=max_run, after=(t1['name'],))
            jobs.add_std(t1)
            jobs.add_std(t2)

        elif processing_scheme == ProcessingScheme.SAMPLE_ORIENTED_CONDENSED_ITERATIVE:
            jobs.add_std(self._tasks_manager.get_task(
                TaskType.ENCODING_AND_EXECUTION, key_min=min_run, key_max=max_run))

        elif processing_scheme == ProcessingScheme.EXEC_ONLY_ITERATIVE:
            jobs.add_std(self._tasks_manager.get_task(
                TaskType.EXECUTION, key_min=min_run, key_max=max_run))

        return jobs

    def __wait_and_sync(self):

        # wait for completion of all PJ tasks
        self._qcgpjm.wait4all()

        self.logger.info("Tasks execution completed")
        self.logger.debug("Syncing state of campaign")

        def update_status(run_id, run_data):
            self._campaign.campaign_db.set_run_statuses([run_id], uq.constants.Status.ENCODED)

        self._campaign.call_for_each_run(update_status, status=uq.constants.Status.NEW)
        self._state_keeper.write_to_state_file({'completed': True})
        self.logger.info("Campaign synced")


class ServiceLogLevel(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class ClientLogLevel(Enum):
    INFO = "info"
    DEBUG = "debug"
