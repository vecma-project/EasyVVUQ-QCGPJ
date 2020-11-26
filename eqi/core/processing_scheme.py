from enum import Enum


class ProcessingScheme(Enum):
    """ Specifies scheme of processing of tasks with QCG-PJ

    Parameters
    ----------
    description : str
        Description of the ProcessingScheme
    iterative : bool
        Defines if the ProcessingScheme uses iterative tasks of QCG-PJ
    """

    STEP_ORIENTED = \
        ("Submits specific EasyVVUQ operation (e.g. encoding) "
         "for all samples as a separate QCG PJ tasks"
         "and then goes to the next EasyVVUQ operation (e.g. execution)")
    STEP_ORIENTED_ITERATIVE = \
        ("Submits an iterative task for execution of specific EasyVVUQ operation "
         "(e.g. encoding) for all samples (a single iteration is here an execution of "
         "the encoding operation for a single sample)"
         "and then do the same for the next EasyVVUQ operation (e.g. for execution)", True)

    SAMPLE_ORIENTED = \
        ("Submits a workflow of EasyVVUQ operations as "
         "separate QCG PJ tasks for a sample "
         "(e.g. encoding -> execution) and then goes to the next sample")
    SAMPLE_ORIENTED_CONDENSED = \
        ("Submits all EasyVVUQ operations for a sample "
         "as a single QCG PJ task (e.g. encoding -> execution) "
         "and then goes to the next sample")
    SAMPLE_ORIENTED_CONDENSED_ITERATIVE = \
        ("Submits an iterative QCG PJ task for all samples, "
         "where a single iteration is composed of"
         "all EasyVVUQ operations for a sample (e.g. encoding -> execution)", True)

    EXEC_ONLY = \
        ("Submits a workflow of EasyVVUQ operations as "
         "separate QCG PJ tasks for execution only")
    EXEC_ONLY_ITERATIVE = \
        ("Submits an iterative QCG PJ task for all samples, "
         "where a single iteration is an execution of sample ", True)

    def __init__(self, description, iterative=False):
        self._description = description
        self._iterative = iterative

    def is_iterative(self):
        """
        Checks if ProcessingScheme makes use of iterative QCG-PJ tasks

        Returns
        -------
            bool : True if ProcessingScheme uses iterative QCG-PJ tasks
        """
        return self._iterative
