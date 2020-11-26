Quick Start
###########

The usage of EasyVVUQ with EasyVVUQ-QCGPJ is very similar to the typical usage
of EasyVVUQ. In the same way as it is in a regular EasyVVUQ script, the
user defines the Campaign object and configures it to use specific
encoders, decoders, samplers. The identical is also the part of
collating results and analysis. The difference is in the middle, in the
way how the campaign is executed.

Basically, the code has to be instrumented with a few instructions
required to configure EasyVVUQ-QCGPJ. This comes down to:

1. Creation of the EasyVVUQ-QCGPJ Executor object.
2. Creation of the QCG-PilotJob Manager for the use by the Executor.
3. Configuration of EasyVVUQ Tasks to be executed by the Executor (in
   practice to be executed by QCG-PilotJob Manager as separate processes).
4. Execution of EasyVVUQ workflow consisted of the Tasks using the
   Executor.
5. Finalization.


Example workflow
****************

In order to explain the basic usage of EasyVVUQ-QCGPJ API we will use an
example.

.. note:: For the full code of this example please look into the test case
 available at the EasyVVUQ-QCGPJ GitHub (https://github.com/vecma-project/EasyVVUQ-QCGPJ) in the path:
 ``/tests/test_pce_pj_executor.py``

Here we briefly outlines the
main parts of that workflow concentrating on the EasyVVUQ-QCGPJ and skipping
fragments that are common with the standard execution of EasyVVUQ.

.. code:: python

   # ...
   import easyvvuq as uq
   import eqi

   from eqi import TaskRequirements
   from eqi import Task, TaskType, ProcessingScheme

   jobdir = os.getcwd()
   tmpdir = jobdir
   appdir = jobdir

   TEMPLATE = "tests/cooling/cooling.template"
   APPLICATION = "tests/cooling/cooling_model.py"
   ENCODED_FILENAME = "cooling_in.json"


   def test_cooling_pj(tmpdir):
       my_campaign = uq.Campaign(name='cooling', work_dir=tmpdir)
       # ...
       # Skipped the typical code of EasyVVUQ that initialises the campaign with encoders, decoders etc.
       # ...
       my_campaign.draw_samples()

       ################################
       # START of EasyVVUQ-QCGPJ part #
       ################################

       # Create Executor
       qcgpjexec = Executor(my_campaign)

       # Create QCG-PilotJob-Manager with 4 cores
       # (if you want to use all available resources remove resources parameter)
       qcgpjexec.create_manager(resources='4')

       # Declare tasks, one for encoding and one for execution, providing their resource requirements
       qcgpjexec.add_task(Task(
           TaskType.ENCODING,
           TaskRequirements(cores=1)
       ))

       qcgpjexec.add_task(Task(
           TaskType.EXECUTION,
           TaskRequirements(cores=1),
           application='python3 ' + jobdir + "/" + APPLICATION + " " + ENCODED_FILENAME
       ))

       # Execute the encoding and execution steps of the campaing using Executor
       qcgpjexec.run(processing_scheme=ProcessingScheme.SAMPLE_ORIENTED)

       # Terminate the created QCG Pilot Job manager
       qcgpjexec.terminate_manager()

       ##############################
       # END of EasyVVUQ-QCGPJ part #
       ##############################

       # The rest of typical EasyVVUQ processing
       my_campaign.collate()
       # ...
       # Skipped code
       # ...

As you can see, the code required for parallel encoding and execution of
the samples stored in an EasyVVUQ campaign is quite concise. The user
just need to create an Executor object providing the already initialised Campaign
as an argument (the set of samples should be ready for processing)
and then, using the methods provided by the object, steer the execution
from the relatively high level.

Below we shortly describe particular elements of this process:

**1. Instantiation of the QCG Pilot Job Manager**

   The Executor internally uses QCG-PilotJob Manager to submit Tasks. The
   Pilot Job Manager instance needs to be set up for the Executor. To
   this end, it is possible to use one of two methods: the presented
   ``create_manager()`` or ``set_manager()``. More information on this
   topic is presented in the section :ref:`QCG-PilotJob Manager initialisation`.


**2. Declaration of tasks**

   The Executor with the ``add_task()`` method allows to define a set of
   Tasks that will be executed once the ``run()`` method is launched. A
   Task added with the ``add_task()`` method needs to be of some type.
   Currently EaasyVVUQ-QCGPJ supports three types of Tasks that maps to
   EasyVVUQ steps that should be executed within a Task:
   ``ENCODING``, ``EXECUTION`` and ``ENCODING_AND_EXECUTION``. These
   types are described in section :ref:`Task types`.


**3. Execution of tasks**

   The Executor configured with the QCG-PilotJob Manager instance and filled
   with a set of appropriate Tasks is ready to perform parallel
   processing of encoding and execution steps for all Campaign's samples
   using the ``run()`` method. This method takes ``processing_scheme`` parameter
   to define a type of the scheme for submission and execution of Tasks
   by QCG-PilotJob Manager. The available schemes differ in a several aspects:

   - *scope of covered EasyVVUQ steps*: encoding and execution, or just execution,

   - *order of submission: step oriented or sample oriented*,

   - *way of execution of tasks by QCG-PilotJob Manager*:
     separate tasks for all steps of a run vs a common task for all steps of a run (condensed),
     separate tasks for each run for a given step vs an iterative task for all runs within the step.

   There is no general rule for the selection of scheme as its applicability and performance
   depends on many factors. For more demanding use-cases it is worth to analyse which
   scheme works best. More information about the schemes can be found in
   the section :ref:`Processing schemes`.

Launching the workfow
*********************

The way of starting the defined workflow is typical, e.g.:

.. code:: bash

   python3 tests/test_pce_pj_executor.py

.. topic:: Common environment

   Please only be sure that the environment is correct for both, master
   script and tasks. More information on this topic is presented in the
   section :ref:`Passing the execution environment to QCG-PilotJob tasks`.

.. note::  It is worth noting that the workflow can be started in a common way on
 both local computer and cluster. In case of the batch execution on
 clusters, the above line can be put into the job script.

Resuming the workfow
********************

EQI is able to resume processing of tasks within QCG-PilotJob Manager if the workflow was not completed
(for example when it was stopped due to crossing the walltime limit).
The resume mechanism is enabled by default and it is used whenever Executor is inited with the campaign
for which EQI processing was already started but not completed.
