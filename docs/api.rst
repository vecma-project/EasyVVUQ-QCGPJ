API description
###############

EasyVVUQ-QCGPJ Executor
***********************
``Executor`` is the main object responsible for steering the configuration
and parallel execution of selected EasyVVUQ tasks with QCG-PilotJob.
The object needs to be tied to the already prepared instance of
the EasyVVUQ campaign and therefore it takes it as the mandatory ``campaign``
parameter for the constructor.

The second (optional) parameter of the ``Executor``'s constructor is
``config_file``, which can be used to initialise the environment
of tasks started by QCG-PilotJob. More information on this topic is presented
in the section :ref:`Passing the execution environment to QCG-PilotJob tasks`

The next parameter is ``resume``. By default it is set to True, which
means that EQI will try to resume not completed workflow of tasks submitted to QCG-PilotJob Manager.
 More on this topic is discussed in the section :ref:`Resume mechanism`

The last (optional) parameter is ``log_level`` that allows to set
specific level of logging just for the EasyVVUQ-QCGPJ part of processing.

QCG-PilotJob Manager initialisation
***********************************

The EasyVVUQ-QCGPJ Executor needs to be configured to use an instance of QCG-PilotJob
Manager service. It is possible to do this in two ways:

-  The first and simpler option is to use ``create_manager()`` method
   that creates QCG-PilotJob Manager in a basic configuration. The method
   takes the following optional parameters:

   -  ``dir`` to customise a working directory of the manager (by
      default current directory)
   -  ``resources`` to specify resources that should be assigned for the
      Pilot Job. If the parameter is not specified, the whole available
      resources will be assigned for the Pilot Job: it means that in
      case of running the Pilot Job inside a queuing system the whole
      allocation will be used. If the parameter is provided, its
      specification should be consisted with the format supported by
      Local mode of `QCG-PilotJob
      manager <https://github.com/vecma-project/QCG-PilotJob>`__, i.e.
      ``[NODE_NAME]:CORES[,[NODE_NAME]:CORES]...``
   -  ``enable_rt_stats`` to enable collection of QCG-PilotJob Manager runtime statistics
   -  ``wrapper_rt_stats`` when ``enable_rt_stats`` is set to ``True``, this parameter
      should point to the location of a QCG-PilotJob tasks wrapper program, used for collection
      of statistic for executed tasks.
   -  ``reserve_core`` to specify if the manager service should run on a
      separate, reserved core (by default ``False``, which means that
      the manager's core will be shared with executed tasks)
    - ``log_level`` to set logging level for QCG-PilotJob Manager service and
      client parts.

-  The second and more advanced option is to use ``set_manager()``
   method. This methods takes a single parameter, which is an instance
   of externally created QCG-PilotJob Manager instance. Don't try to use
   this method unless you have very specific needs.

   For the reference go to: `QCG-PilotJob
   documentation <https://github.com/vecma-project/QCG-PilotJob>`__.

Task types
**********

EasyVVUQ-QCGPJ supports the following types of Tasks that may be executed by QCG
PJ Manager:

-  ``ENCODING``: this Task is used for the encoding of a single sample.

-  ``EXECUTION``: this Task is used for the execution of an application
   for a single sample. The constructor of this Task requires the
   ``application`` parameter to be specified with the value defining a
   command to run the application. The ``EXECUTION`` Task for a given
   sample depends on the ``ENCODING`` Task for the same sample.

-  ``ENCODING&EXECUTION``: this Task is used for running both encoding
   and execution for a single sample. Similarly to the ``EXECUTION``
   Task the constructor of this Task requires the ``application``
   parameter to be specified with the value defining a command to run
   the application.

The addition of a Task to Executor does not condition its later use -
this if the Task is actually used depends on a specific processing
scheme that is selected for the execution in the ``run()`` method of
Executor. In order to keep consistency of the environment only a single
Task of a given type should be kept in the Executor.

Tasks requirements
******************

Tasks defined for execution by the QCG-PilotJob system need to define their
resource requirements. In EasyVVUQ-QCGPJ the specification of resource
requirements for a Task is made directly via the Task's constructor,
particularly by its second parameter - ``TaskRequirements``. This object
may be inited with a combination of two parameters: ``nodes`` and
``cores``. If the only specified parameter is ``cores``, the Task will
run on a specified number of cores regardless of their physical location
(the cores can be distributed on many nodes). If there are two
parameters specified: ``nodes`` and ``cores`` the Task will use the
number of cores requested by ``cores`` parameter on each of the nodes
requested by ``nodes`` parameter. Therefore, in order to have good
efficiency, for the multicore Tasks it is advised to specify two
parameters: ``nodes`` and ``cores`` (even if there is only a need to
take one node).

Both ``nodes`` and ``cores`` parameters may be of ``int`` type or of ``Resources`` type.
In the case when a parameter is of an ``int`` type, the provided value is simply
mapped to the exact number of required resources. In the case of parameters of ``Resources``
type, there is much more flexibility in the requirements specification,
which may be obtained with the following keyword combinations:

-  ``exact`` - the exact number of resources should be used,
-  ``min`` - ``max`` - the resources number should be larger than
   ``min`` and lower than \`max,
-  ``min`` - ``split-into`` - all available resources should be divided
   into chunks of size ``split-into``, but the size of chunks can't be
   smaller than ``min``

Example ``TaskRequirements`` specifications:

-  Use exactly 4 cores, regardeless of their location

.. code:: python

        TaskRequirements(cores=4)

-  Use 4 cores on a single node

.. code:: python

        TaskRequirements(nodes=1,cores=4)

-  Use from 4 to 6 cores on each of 2 nodes

.. code:: python

        TaskRequirements(nodes=2,cores=Resources(min=4,max=6))

The algorithm used to define Task requirements in EasyVVUQ-QCGPJ is inherited
from the QCG-PilotJob system. Further instruction can be found in the `QCG
Pilot Job documentation <https://github.com/vecma-project/QCG-PilotJob>`__

Task execution models
*********************

The optional parameter of ``Task`` constructor is ``model``. It allows to adjust the way how a task will be
started by QCG-PilotJob Manager in a parallel environment. At the moment of writing this documentation, the
following models are available: ``threads``, ``openmpi``, ``intelmpi``, ``srunmpi``, ``default``.
Since this option comes directly from QCG-PilotJob, the detailed description of the particular models is available
in the `QCG Pilot Job documentation <https://github.com/vecma-project/QCG-PilotJob>`__


Processing schemes
*******************

EasyVVUQ-QCGPJ allows to process tasks in a few predefined schemes which differ
in both the scope of covered EasyVVUQ steps as well as the order of submission
and the way of processing of tasks by QCG-PilotJob.

Below we shortly describe the seven currently supported schemes,
making the use of some kind of visual representation.
Firstly, let's assume that we have a set of EasyVVUQ samples marked as
s1, s2, ..., sN. Then:

``STEP_ORIENTED``
   in this scheme tasks are submitted in a priority
   of STEP; we want to complete encoding step for all samples and then
   go to the execution step for all samples. This scheme is as follows:

   ``encoding(s1)->encoding(s2)->...->encoding(sN)->execution(s1)->execution(s2)->...->execution(sN)``

``STEP_ORIENTED_ITERATIVE``
   this scheme is similar to ``STEP_ORIENTED`` in a sense that the tasks
   are submitted in a priority of STEP, but here we make use of iterative
   tasks of QCG-PilotJob to execute all operation within a STEP in a single
   iterative task (internally consisted of many iterations).
   This scheme can be expressed as follows:

   ``encoding_iterative(s1, s2, ..., sN)->execution_iterative(s1, s2, ..., sN)``


``SAMPLE_ORIENTED``
   in this scheme the tasks are submitted in a priority
   of SAMPLE; in other words we want to complete whole
   processing (encoding and execution) for a given sample as soon as
   possible and then go to the next sample. This scheme can be written as
   follows:

   ``encoding(s1)->execution(s1)->encoding(s2)->execution(s2)->...->encoding(sN)->execution(sN)``


``SAMPLE_ORIENTED_CONDENSED``
   it is similar scheme to ``SAMPLE_ORIENTED``,
   but the encoding and execution are *condensed* into a single PJ task.
   It could be expressed as:

   ``encoding&execution(s1)->encoding&execution(s2)->...->encoding&execution(sN)``


``SAMPLE_ORIENTED_CONDENSED_ITERATIVE``
   this type employs iterative tasks to run *condensed* encoding and execution.
   This is similar to ``SAMPLE_ORIENTED_CONDENSED``, but here encoding&execution tasks are
   a part of iterative task. It could be expressed as:

   ``encoding&execution_iterative(s1, s2, ..., sN)``


``EXECUTION_ONLY``
   instructs to submit only the ``EXECUTION`` tasks assuming that the encoding step
   is executed outside QCG-PilotJob. It could be written as follows:

   ``execution(s1)->execution(s2)->...->execution(sN)``


``EXECUTION_ONLY_ITERATIVE``
   the variation of scheme to submit only the ``EXECUTION`` tasks, but in contrast to
   the ``EXECUTION_ONLY`` scheme, here an iterative QCG-PilotJob task is used to run all tasks.
   It could be written as follows:

   ``execution_iterative(s1, s2,... sN)``


The schemes use different task types that need to be added to Executor in order to allow processing:

-  The ``SAMPLE_ORIENTED``, ``STEP_ORIENTED``and ``STEP_ORIENTED_ITERATIVE`` schemes require
   ``ENCODING`` and ``EXECUTION`` tasks.
-  The ``EXECUTION_ONLY`` and ``EXECUTION_ONLY_ITERATIVE`` schemes require ``EXECUTION`` task.
-  The ``SAMPLE_ORIENTED_CONDENSED`` and ``SAMPLE_ORIENTED_CONDENSED_ITERATIVE`` require ``ENCODING_AND_EXECUTION``
   task.

The efficiency of the schemes may significantly differ depending on use case
and resource requirements defined for execution of both the whole PilotJob
and the individual task types.
For many scenarios the iterative schemes could run a bit better,
but there is no general rule of thumb that says so, and therefore we encourage you
to test different schemes when the efficiency is priority.

Passing the execution environment to QCG-PilotJob tasks
*******************************************************

Since every QCG-PilotJob task is started in a separate process, it needs to be
properly configured to run in an environment consistent with the
requirements of the parent script. On the one hand, EasyVVUQ allows to
easily recover information about the campaign from the database, but
some environment settings, such as information about required
environment modules or virtual environment, have to be passed in a
different way. To this end, EasyVVUQ-QCGPJ delivers a simple mechanism based on
an idea of bash script, that is sourced by each task prior to its actual
execution. The path to this file can be provided in the ``EQI_CONFIG``
environment variable. If this environment variable is available in the
master script, it is also automatically passed to QCG-PilotJob tasks.

To the large extent the structure of the script provided in
``EQI_CONFIG`` is fully custom. In this script a user can load
modules, set further environment variables or even do simple
calculations. The content can be all things that are needed by a Task in
prior of its actual execution. Very basic example of the
``EQI_CONFIG`` file may look as follows:

.. code:: bash

   #!/bin/bash

   module load openmpi/4.0

.. note::
    The alternate option to provide the configuration file is to specify
    its location by the ``config_file`` parameter
    provided into the constructor of the ``Executor`` object.

Resume mechanism
****************
EQI is able to resume not completed workflow of tasks submitted to QCG-PilotJob Manager
(for example terminated because of the walltime crossing).
By default the resume mechanism is activated automatically when Executor is inited with the campaign
for which EQI processing was already started (working directory exists) but it is not yet completed.
If this behaviour is not intended, the resume mechanism can be disabled with providing
``resume=False`` parameter to the ``Executor's`` constructor.

The resumed workflow will start in a working directory of the previous, not-completed execution.
This is fully expected behaviour, but since the partially generated output or intermediate files can exists,
they need to be carefully handled. EQI tries to help in this matter by providing
mechanisms for automatic recovery of individual tasks.

How much the automatism can interfere with the resume logic depends on a use case and therefore
EQI provides a few ``ResumeLevels`` of automatic recovery. The levels can be set in the ``Task``'s
constructor with the ``resume_level`` parameter. There are the following options available:

``DISABLED``
    Automatic resume is fully disabled for a task.
``BASIC``
    For the task types creating run directories (``ENCODING``, ``ENCODING_AND_EXECUTION``), the resume checks
    if an unfinished task created run directory. If such directory is available, this directory is recursively
    removed before the start of the resumed task.
``MODERATE``
    This level processes all operations offered by the ``BASIC`` level, and adds the following features.
    At the beginning of a task's execution, the list of directories and files in a run directory
    is generated and stored. The resumed task checks for the differences and remove new files and directories
    in order to resurrect the initial state.

Please note that this functionality may be not sufficient for more advanced scenarios
(for example if input files are updated during an execution) and those for which the overhead
of the built-in mechanism is not acceptable.
In such cases, the more optimal logic of resume may need to be provided on a level of the actual code of a task.

External Encoders
*****************

EasyVVUQ allows to define custom encoders for specific use cases. This
works without any issues as long as we are in a single process. However,
in case we want to execute the encoding in a separate processes, there
is a need to instruct these processes about the encoder. This
information is partially available in the Campaign itself and can be
recovered, but we need to somehow instruct EasyVVUQ-QCGPJ code to import
required python modules for the encoder. To this end once again we make
use of environment variable - this time ``ENCODER_MODULES``. The value
of this variable should be the semicolon-separated list of the modules
names, which are required by the custom encoder. The modules will be
dynamically loaded before the encoder is recovered, what resolves the
problem. In order to use ``ENCODER_MODULES`` variable we propose to
define it in the ``EQI_CONFIG``

An example configuration of ``EQI_CONFIG`` that includes
specification of custom ``ENCODER_MODULES`` may look as follows (for the
full test case please look in ``tests/custom_encoder``):

.. code:: bash

   #!/bin/bash

   # WORKS ONLY IN BASH - SHOULD BE CHANGED (EG. TO GLOBAL PATHS) IN CASE OF OTHER INTERPRETERS
   this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
   this_file=$(basename "${BASH_SOURCE[0]}")

   PYTHONPATH="${PYTHONPATH}:${this_dir}"
   ENCODER_MODULES="custom_encoder"
   export PYTHONPATH
   export ENCODER_MODULES

   export EQI_CONFIG=$this_dir/$this_file
