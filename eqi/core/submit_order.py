from enum import Enum


class SubmitOrder(Enum):
    """ Specifies order of submission of tasks to QCG-PJ

    Parameters
    ----------
    description : str
        Description of the SubmitOrder
    iterative : bool
        Defines if the SubmitOrder uses iterative tasks of QCG-PJ
    """

    PHASE_ORIENTED = \
        ("Submits specific EasyVVUQ operation (e.g. encoding) "
         "for all runs as a separate QCG PJ tasks"
         "and then goes to the next EasyVVUQ operation (e.g. execution)")
    RUN_ORIENTED = \
        ("Submits a workflow of EasyVVUQ operations as "
         "separate QCG PJ tasks for a run "
         "(e.g. encoding -> execution) and then goes to the next run")
    RUN_ORIENTED_CONDENSED = \
        ("Submits all EasyVVUQ operations for a run "
         "as a single QCG PJ task (e.g. encoding -> execution) "
         "and then goes to the next run")
    EXEC_ONLY = \
        ("Submits a workflow of EasyVVUQ operations as "
         "separate QCG PJ tasks for execution only")

    PHASE_ORIENTED_ITERATIVE = \
        ("Submits specific EasyVVUQ operation (e.g. encoding) "
         "for all runs as an iterative QCG PJ task"
         "and then goes to the next EasyVVUQ operation (e.g. execution)", True)
    RUN_ORIENTED_CONDENSED_ITERATIVE = \
        ("Submits iterative QCG PJ task consisted of iterations composed of"
         "all EasyVVUQ operations for a run (e.g. encoding -> execution)", True)
    EXEC_ONLY_ITERATIVE = \
        ("Submits iterative QCG PJ task just for the execution of all runs ", True)

    def __init__(self, description, iterative=False):
        self._description = description
        self._iterative = iterative

    def is_iterative(self):
        """
        Checks if SubmitOrder makes use of iterative QCG-PJ tasks

        Returns
        -------
            bool : True if SubmitOrder uses iterative QCG-PJ tasks
        """
        return self._iterative
