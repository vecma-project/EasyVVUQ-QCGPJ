API description
###############

QCG-PilotJob Manager initialisation
***********************************

The EasyVVUQ-QCGPJ Executor needs to be configured to use an instance of QCG-PilotJob
Manager service. It is possible to do this in two ways:

-  The first and simpler option is to use ``create_manager()`` method
   that creates QCG-PilotJob Manager in a basic configuration. The method
   takes three optional parameters:

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
   -  ``reserve_core`` to specify if the manager service should run on a
      separate, reserved core (by default ``False``, which means that
      the manager's core will be shared with executed tasks).

-  The second and more advanced option is to use ``set_manager()``
   method. This methods takes a single parameter, which is an instance
   of externally created QCG-PilotJob Manager instance.

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
this if the Task is actually used depends on a specific submission
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

Both ``nodes`` and ``cores`` parameters are of the ``Resources`` type
and may be specified in the common way, with the following keyword
combinations:

-  ``exact`` - the exact number of resources should be used,
-  ``min`` - ``max`` - the resources number should be larger than
   ``min`` and lower than \`max,
-  ``min`` - ``split-into`` - all available resources should be divided
   into chunks of size ``split-into``, but the size of chunks can't be
   smaller than ``min``

Example ``TaskRequirements`` specifications:

-  Use exactly 4 cores, regardeless of their location

.. code:: python

        TaskRequirements(cores=Resources(exact=4))

-  Use 4 cores on a single node

.. code:: python

        TaskRequirements(nodes=Resources(exact=1),cores=Resources(exact=4))

-  Use from 4 to 6 cores on each of 2 nodes

.. code:: python

        TaskRequirements(nodes=Resources(exact=2),cores=Resources(min=4,max=6))

The algorithm used to define Task requirements in EasyVVUQ-QCGPJ is inherited
from the QCG-PilotJob system. Further instruction can be found in the `QCG
Pilot Job
documentation <https://github.com/vecma-project/QCG-PilotJob>`__

Submission schemes
******************

EasyVVUQ-QCGPJ allows to submit tasks in a few predefined order schemes. The
submission may be ``RUN_ORIENTED``, ``PHASE_ORIENTED``, ``EXECUTION_ONLY`` or
``RUN_ORIENTED_CONDENSED``. Depending on a specific usecase the
efficiency of these schemes may significantly differ.

Below we shortly describe the four currently supported schemes of
submission, making the use of some kind of visual representation.
Firstly, let's assume that we have a set of EasyVVUQ samples marked as
s1, s2, ..., sN. Then:

``RUN_ORIENTED``
   means that the tasks are submitted in a priority
   of RUN (aka sample); in other words we want to complete whole
   processing (encoding and execution) for a given sample as soon as
   possible and then go to the next sample. This order can be written as
   follows:

   ``encoding(s1)->execution(s1)->encoding(s2)->execution(s2)->...->encoding(sN)->execution(sN)``

``PHASE_ORIENTED``
   means that the tasks are submitted in a priority
   of PHASE; we want to complete encoding phase for all samples and then
   go to the execution phase for all samples. This order is as follows:

   ``encoding(s1)->encoding(s2)->...->encoding(sN)->execution(s1)->execution(s2)->...->execution(sN)``


``EXECUTION_ONLY``
   instructs to submit only the ``EXECUTION`` tasks assuming that the encoding phase is executed outside
   QCG-PilotJob. It could be written as follows:

   ``execution(s1)->execution(s2)->...->execution(sN)``


``RUN_ORIENTED_CONDENSED``
   it is similar order to ``RUN_ORIENTED``,
   but the encoding and execution are *condensed* into a single PJ task.
   It could be expressed as:

   ``encoding&execution(s1)->encoding&execution(s2)->...->encoding&execution(sN)``

The schemes use different task types that need to be added to Executor to execute:

-  The ``RUN_ORIENTED`` and ``PHASE_ORIENTED`` schemes require
   ``ENCODING`` and ``EXECUTION`` tasks.
-  The ``EXECUTION_ONLY`` scheme requires ``EXECUTION`` task.
-  The ``RUN_ORIENTED_CONDENSED`` requires ``ENCODING_AND_EXECUTION``
   task.

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
execution. The path to this file can be provided in ``EASYPJ_CONFIG``
environment variable. If this environment variable is available in the
master script, it is also automatically passed to QCG-PilotJob tasks.

To the large extent the structure of the script provided in
``EASYPJ_CONFIG`` is fully custom. In this script a user can load
modules, set further environment variables or even do simple
calculations. The content can be all things that are needed by a Task in
prior of its actual execution. Very basic example of the
``EASYPJ_CONFIG`` file may look as follows:

.. code:: bash

   #!/bin/bash

   module load openmpi/4.0

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
define it in the ``EASYPJ_CONFIG``

An example configuration of ``EASYPJ_CONFIG`` that includes
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

   export EASYPJ_CONFIG=$this_dir/$this_file
