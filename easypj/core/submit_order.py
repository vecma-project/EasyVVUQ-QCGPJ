from enum import Enum


class SubmitOrder(Enum):
    PHASE_ORIENTED = "Submits specific EasyVVUQ operation (e.g. encoding) " \
                     "for all runs as a separate QCG PJ tasks" \
                     "and then goes to the next EasyVVUQ operation (e.g. execution)"
    RUN_ORIENTED = "Submits a workflow of EasyVVUQ operations as " \
                   "separate QCG PJ tasks for a run " \
                   "(e.g. encoding -> execution) and then goes to the next run"
    RUN_ORIENTED_CONDENSED = "Submits all EasyVVUQ operations for a run " \
                             "as a single QCG PJ task (e.g. encoding -> execution) " \
                             "and then goes to the next run"
    EXEC_ONLY = "Submits a workflow of EasyVVUQ operations as " \
                "separate QCG PJ tasks for execution only"
