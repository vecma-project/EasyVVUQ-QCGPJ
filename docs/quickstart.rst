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
5. Finalization


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
   import easypj

   from easypj import TaskRequirements, Resources
   from easypj import Task, TaskType, SubmitOrder

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
       qcgpjexec = Executor()

       # Create QCG-PilotJob-Manager with 4 cores
       # (if you want to use all available resources remove resources parameter)
       qcgpjexec.create_manager(dir=my_campaign.campaign_dir, resources='4')

       # Declare tasks, one for encoding and one for execution, providing their resource requirements
       qcgpjexec.add_task(Task(
           TaskType.ENCODING,
           TaskRequirements(cores=Resources(exact=1))
       ))

       qcgpjexec.add_task(Task(
           TaskType.EXECUTION,
           TaskRequirements(cores=Resources(exact=1)),
           application='python3 ' + jobdir + "/" + APPLICATION + " " + ENCODED_FILENAME
       ))

       # Execute the encoding and execution steps of the campaing using Executor
       qcgpjexec.run(
           campaign=my_campaign,
           submit_order=SubmitOrder.RUN_ORIENTED)

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
just need to create an Executor object and using the methods of this
object steer the rest of the process. Below we shortly describe
particular elements of this process:

**1. Instantiation of the QCG Pilot Job Manager**

   The Executor internally uses QCG-PilotJob Manager to submit Tasks. The
   Pilot Job Manager instance needs to be set up for the Executor. To
   this end, it is possible to use one of two methods: the presented
   ``create_manager()`` or ``set_manager()``. More information on this
   topic is presented in the section :ref:`QCG Pilot Job Manager initialisation`.


**2. Declaration of tasks**

   The Executor with the ``add_task()`` method allows to define a set of
   Tasks that will be executed once the ``run()`` method is launched. A
   Task added with the ``add_task()`` method needs to be of some type.
   Currently EaasyVVUQ-QCGPJ supports three types of Tasks:
   ``ENCODING``, ``EXECUTION`` and ``ENCODING_AND_EXECUTION``. These
   types are described in section :ref:`Task types`.


**3. Execution of tasks**

   The Executor configured with the QCG-PilotJob Manager instance and filled
   with a set of appropriate Tasks is ready to perform parallel
   processing of encoding and execution steps for all Campaign's samples
   using the ``run()`` method. This method takes two parameters:
   ``campaign`` and ``submit_order``. The first parameter is a campaign
   object that should be already configured and for which the samples
   should be generated. The second parameter, ``submit_order`` is used
   to define a type of the scheme for the submission of Tasks in a
   specific order. There are four possibile submission schemes /
   ``submit_order``\ s: ``RUN_ORIENTED``, ``PHASE_ORIENTED``, ``EXEC_ONLY`` and
   ``RUN_ORIENTED_CONDENSED``. Description of the differences between
   these types is described in the section :ref:`Submission schemes`.

Launching the workfow
*********************

The way of starting the defined workflow is typical, e.g.:

.. code:: bash

   python3 tests/test_pce_pj_executor.py

.. topic:: Common environment

   Please only be sure that the environment is correct for both, the master
   script and the tasks. More information on this topic is presented in the
   section :ref:`Passing the execution environment to QCG Pilot Job tasks`.

.. note::  It is worth noting that the workflow can be started in a common way on
 both local computer and cluster. In case of the batch execution on
 clusters, the above line can be put into the job script.
