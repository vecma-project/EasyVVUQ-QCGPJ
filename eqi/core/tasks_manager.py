from eqi.core.task import TaskType


class TasksManager:
    """Manages tasks for execution with QCG-PJ

    This is the main class for definition and management of tasks for execution
    by QCG-PilotJob. The tasks usually maps to certain steps of EasyVVUQ

    """

    def __init__(self, campaign, eqi_dir, config_file=None):
        self._tasks = {}
        self._campaign = campaign
        self._config_file = config_file
        self._eqi_dir = eqi_dir

    def add_task(self, task):
        self._tasks[task.get_name()] = task

    def get_task(self, name, key=None, key_min=None, key_max=None, after=None):
        task = self._tasks.get(name)
        task_type = task.get_type()

        ready_task = None

        if key:
            switcher = {
                TaskType.ENCODING: self._prepare_encoding_task,
                TaskType.EXECUTION: self._prepare_exec_task,
                TaskType.ENCODING_AND_EXECUTION: self._prepare_encoding_and_exec_task,
            }
            task_method = switcher.get(task_type)
            ready_task = task_method(task, key)
        elif key_max:
            switcher = {
                TaskType.ENCODING: self._prepare_encoding_task_iterative,
                TaskType.EXECUTION: self._prepare_exec_task_iterative,
                TaskType.ENCODING_AND_EXECUTION: self._prepare_encoding_and_exec_task_iterative,
            }
            task_method = switcher.get(task_type)
            ready_task = task_method(task, key_max, key_min)

        self._fill_task_with_common_params(ready_task, task.get_resume_level(), task.get_requirements(), after)

        return ready_task

    def _prepare_encoding_task(self, task, key):

        model = task.get_model()

        enc_args = [
            key
        ]

        encode_task = {
            "name": 'encode_' + key,
            "execution": {
                "model": model,
                "exec": 'easyvvuq_encode',
                "args": enc_args,
                "stdout": f"encode_{key}.stdout",
                "stderr": f"encode_{key}.stderr"
            }
        }

        return encode_task

    def _prepare_encoding_task_iterative(self, task, key_max, key_min=0):

        model = task.get_model()

        key = "Run_${it}"

        enc_args = [
            key,
        ]

        encode_task = {
            "name": "encode",
            "iteration": {"stop": key_max + 1, "start": key_min},
            "execution": {
                "model": model,
                "exec": 'easyvvuq_encode',
                "args": enc_args,
                "stdout": f"encode_{key}.stdout",
                "stderr": f"encode_{key}.stderr"
            }
        }

        return encode_task

    def _prepare_exec_task(self, task, key):

        application = task.get_params().get("application")
        model = task.get_model()

        exec_args = [
            key,
            application
        ]

        execute_task = {
            "name": 'execute_' + key,
            "execution": {
                "model": model,
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "stdout": f"execute_{key}.stdout",
                "stderr": f"execute_{key}.stderr"
            }
        }

        return execute_task

    def _prepare_exec_task_iterative(self, task, key_max, key_min=0):

        application = task.get_params().get("application")
        model = task.get_model()

        key = "Run_${it}"

        exec_args = [
            key,
            application
        ]

        execute_task = {
            "name": "execute",
            "iteration": {"stop": key_max + 1, "start": key_min},
            "execution": {
                "model": model,
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "stdout": f"execute_{key}.stdout",
                "stderr": f"execute_{key}.stderr"
            }
        }

        return execute_task

    def _prepare_encoding_and_exec_task(self, task, key):

        application = task.get_params().get("application")
        model = task.get_model()

        args = [
            key,
            application
        ]

        encode_execute_task = {
            "name": 'encode_execute_' + key,
            "execution": {
                "model": model,
                "exec": 'easyvvuq_encode_execute',
                "args": args,
                "stdout": f"encode_execute_{key}.stdout",
                "stderr": f"encode_execute_{key}.stderr"
            }
        }

        return encode_execute_task

    def _prepare_encoding_and_exec_task_iterative(self, task, key_max, key_min=0):

        application = task.get_params().get("application")
        model = task.get_model()

        key = "Run_${it}"

        args = [
            key,
            application
        ]

        encode_execute_task = {
            "name": 'encode_execute',
            "iteration": {"stop": key_max + 1, "start": key_min},
            "execution": {
                "model": model,
                "exec": 'easyvvuq_encode_execute',
                "args": args,
                "stdout": f"encode_execute_{key}.stdout",
                "stderr": f"encode_execute_{key}.stderr"
            }
        }

        return encode_execute_task

    def _get_exec_only_task(self, task, key):

        application = task.get_params().get("application")
        model = task.get_model()

        exec_args = [
            key,
            application
        ]

        execute_task = {
            "name": 'execute_' + key,
            "execution": {
                "model": model,
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "stdout": f"execute_{key}.stdout",
                "stderr": f"execute_{key}.stderr"
            }
        }

        return execute_task

    def _get_exec_only_task_iterative(self, task, key_max, key_min=0):

        application = task.get_params().get("application")
        model = task.get_model()

        key = "Run_${it}"

        exec_args = [
            key,
            application
        ]

        execute_task = {
            "name": 'execute',
            "iteration": {"stop": key_max + 1, "start": key_min},
            "execution": {
                "model": model,
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "stdout": f"execute_{key}.stdout",
                "stderr": f"execute_{key}.stderr"
            }
        }

        return execute_task

    def _fill_task_with_common_params(self, task, resume_level, requirements=None, after=None,):

        if requirements:
            task.update(requirements.get_resources())
        if after:
            task.update({
                'dependencies': {
                    'after': after
                }})

        task["execution"].update({"env": {"EQI_RESUME_LEVEL": resume_level.name}})

        if self._config_file:
            task["execution"].update({"env": {"EQI_CONFIG": self._config_file}})
