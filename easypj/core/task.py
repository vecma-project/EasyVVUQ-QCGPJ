from enum import Enum


class TaskType(Enum):
    ENCODING = "ENCODING"
    EXECUTION = "EXECUTION"
    ENCODING_AND_EXECUTION = "ENCODING_AND_EXECUTION"
    OTHER = "OTHER"


class Task:
    """ Represents a piece of work to be executed by QCG-PilotJob Manager

    Parameters
    ----------
    type : TaskType
        The type of the task. Allowed tasks are: ENCODING, EXECUTION, ENCODING_AND_EXECUTION,
         and OTHER (currently not supported)
    requirements : TaskRequirements
        The requirements for the Task
    name : str
        name of the Task, if not provided the name will take a value of type
    params: kwargs
        additional parameters that may be used by specific Task types
    """

    def __init__(self, type, requirements, name=None, **params):
        self._type = type
        self._requirements = requirements
        self._params = params
        self._name = name if name else type

    def get_type(self):
        return self._type

    def get_requirements(self):
        return self._requirements

    def get_params(self):
        return self._params

    def get_name(self):
        return self._name
