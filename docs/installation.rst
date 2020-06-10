Installation
############

Requirements
------------

The software requires Python 3.6+ for usage.

Moreover, since EasyVVUQ-QCGPJ is a wrapper over EasyVVUQ and QCG-PilotJob, you need to have
both these packages available in your environment. You can install them with pip in the following way:

::

    $ pip3 install easyvvuq
    $ pip3 install qcg-pilotjob


Automatic installation
----------------------

The software could be easily installed from the PyPi repository:

::

   $ pip3 install easyvvq-qcgpj


Manual installation
-------------------

If you prefer manual installation or you wont to install specific branch of the software
you can get it from the the github repository. The procedure is quite typical, e.g.:

::

   $ git clone https://github.com/vecma-project/EasyVVUQ-QCGPJ.git
   $ cd EasyVVUQ-QCGPJ
   $ git checkout some_branch
   $ pip3 install .
