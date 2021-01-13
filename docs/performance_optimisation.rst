Performance optimisation hints
##############################

There are many factors that influence on the performance of EQI.
This section presents some guidance on optimisation of EQI. However, since the scenarios are very different
the presented information should be considered only as hints that can help in optimisation, but they are not
a ready-to-use recipes.

Performance-aware usage of QCG-PilotJob
***************************************
Firstly, the performance of EQI is naturally limited by the performance of QCG-PilotJob.
At this level, the usage of ``ITERATIVE`` versions of tasks is preferred
as it minimises communication overhead related to interaction with QCG-PilotJob Manager.
The other element that is related to QCG-PilotJob and should be taken into account and may be beneficial
for larger executions is the reservation of a dedicated core for QCG-PilotJob Manager.
However, in general, it should be noted that the QCG-PilotJob performance may cause a problem only for extremely
demanding scenarios. For the typical use cases, there are other aspects that possibly play more important role.

Tasks fitting in allocation
***************************
The critical element for good performance of EQI is to ensure good fitting of the tasks
to the size of allocation so there are no empty slots during the execution. For example,
it would be very inefficient to have 10 cores in allocation and execute only tasks requiring 6 cores. Then 4 cores
would be empty all the time. Much more optimal would be to execute tasks that require 5 cores so
two task could be executed in parallel. Please note that there are different types of tasks and different processing
schemes that may use these tasks available in EQI, so the allocation of tasks may be not so obvious
as in the given example. Thus both the allocation size, tasks sizes and processing scheme selection are all variables
that need to be determined through scenario analysis and pre-production tests. Please by also aware
that reservation of a core for QCG-PilotJob Manager naturally reduces a number of available cores for tasks,
thus it should be taken into account during the analysis.

Workflow splitting
******************
The basic way of usage of EQI goes down to modification of few lines in a typical EasyVVUQ workflow
and execution of the modified workflow on a computing cluster. This is easy, but it should be noted that the
whole workflow will be executed in an allocation that can consist of many computing nodes. Likely not all
steps of EasyVVUQ require HPC power or may be done in parallel (e.g. sampling and analysis are typically
done serially) and therefore in some use cases it may be more optimal to split the workflow
into parts executed on HPC machines and those executed locally (or in different, smaller allocation).
EasyVVUQ provides the save / load mechanism for the Campaign based on a state file,
that can be used to resurrect the workflow when some calculations have been already made in a different
location. In particular, this optimisation should be considered when there is a large allocation
and relatively long processing time of sampling / analysis

Going forward with this issue, also encoding tasks can be extracted from the processing in a large allocation.
Please note however that possible inefficiency is here relatively small since encoding tasks can be executed
in parallel over the whole allocation (unless the ``EXECUTION_ONLY`` processing scheme is not selected).

Resume mechanism settings
*************************
The resume mechanism, and particularly its level, can influence on task's performance. If the risk of
interruption of a workflow can be accepted or if resume mechanism is provided by application itself, the
automatic resume mechanism of EQI may be set on ``BASIC`` level or even switched-off completely.

Logging and output generation
*****************************
When there is a huge number of tasks even relatively rare writes to disk may cause a problem. Therefore it may be
beneficial to turn logging into less descriptive type or limit a number of output messages.
This applies to the logging in EQI, but also to any code that is executed inside a task.
