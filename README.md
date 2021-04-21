![](docs/images/eqi-logo-h.png)

# EasyVVUQ-QCGPJ - Python API for HPC execution of EasyVVUQ (EQI)

[![Build status](https://github.com/vecma-project/EasyVVUQ-QCGPJ/actions/workflows/python-package.yml/badge.svg)](https://github.com/vecma-project/EasyVVUQ-QCGPJ/actions/workflows/python-package.yml)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/vecma-project/EasyVVUQ-QCGPJ.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/vecma-project/EasyVVUQ-QCGPJ/alerts/)

EasyVVUQ-QCGPJ (EQI) is a lightweight plugin for parallelization of [EasyVVUQ](https://github.com/UCL-CCS/EasyVVUQ)
with [QCG-PilotJob](https://github.com/vecma-project/QCG-PilotJob).

It is a part of the [VECMA Toolkit](http://www.vecma-toolkit.eu).

The tool provides API that can be effortlessly integrated into typical EasyVVUQ workflows to enable parallel processing
of demanding operations, in particular the simulation model's executions and encodings.
It works regardless if you run your use-case on multi-core laptop or on large HPC machine.


## Requirements

The software requires Python 3.6+ for usage.

Moreover, since EasyVVUQ-QCGPJ is a wrapper over EasyVVUQ and QCG-PilotJob, you need to have
both these packages available in your environment. This version of the library is compatible with 
EasyVVUQ v0.8 and QCG-PilotJob v0.11.1. Compatibility with other versions is not confirmed and may be limited.
Thus, if you want to be sure that correct versions of required packages are available, 
install them in the following way:
```
$ pip3 install --force-reinstall easyvvuq==0.8
$ pip3 install --force-reinstall qcg-pilotjob==0.11.1
```

## Installation

The software could be easily installed from the PyPi repository:
```
$ pip3 install easyvvq-qcgpj
```

Alternatively, if you want to use specific branch of the software, 
you can get it from the the github repository. The procedure is quite typical, e.g.:

```
$ git clone https://github.com/vecma-project/EasyVVUQ-QCGPJ.git
$ cd EasyVVUQ-QCGPJ
$ git checkout some_branch
$ pip3 install .
```

## Getting started
Documentation is available at https://easyvvuq-qcgpj.readthedocs.io

## Authors
* Bartosz Bosak <bbosak@man.poznan.pl>
* Piotr Kopta <pkopta@man.poznan.pl>
* Tomasz Piontek <piontek@man.poznan.pl>
* Jalal Lakhlili <jalal.lakhlili@ipp.mpg.de>
