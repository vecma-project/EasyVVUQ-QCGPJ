
![](docs/images/easypj-logo.png)

[![Build Status](https://travis-ci.org/vecma-project/EasyVVUQ-QCGPJ.svg?branch=master)](https://travis-ci.org/vecma-project/EasyVVUQ-QCGPJ)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/vecma-project/EasyVVUQ-QCGPJ.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/vecma-project/EasyVVUQ-QCGPJ/alerts/)


EasyVVUQ-QCGPJ is a lightweight plugin for parallelization of EasyVVUQ (https://github.com/UCL-CCS/EasyVVUQ)
with the QCG Pilot Job system (https://github.com/vecma-project/QCG-PilotJob).

It is developed as part of VECMA (http://www.vecma.eu), and is part of the VECMA Toolkit (http://www.vecma-toolkit.eu).

The tool provides API that can be effortlessly integrated into typical EasyVVUQ workflows to enable parallel processing
of demanding operations, in particular the simulation model's executions and encodings.
It works regardless if you run your use-case on multi-core laptop or on large HPC machine.


## Requirements
The software requires pip 18.0.1+ for installation and Python 3.6+ for usage.

Moreover, since EasyVVUQ-QCGPJ is a wrapper over EasyVVUQ and QCG-PilotJob, you need to have
both these packages available in your environment. You can install them with pip in the following way:
```
$ pip3 install easyvvuq
$ pip3 install QCGPilotJobManager
```

### Installation
The software could be easily installed from the github with pip:

```
$ pip3 install git+https://github.com/vecma-project/EasyVVUQ-QCGPJ.git@master
```

## Getting started
Documentation is available at https://easyvvuq-qcgpj.readthedocs.io
