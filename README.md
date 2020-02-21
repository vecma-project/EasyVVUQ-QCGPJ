
![](docs/easypj-logo.png)

[![Build Status](https://travis-ci.org/vecma-project/EasyVVUQ-QCGPJ.svg?branch=master)](https://travis-ci.org/vecma-project/EasyVVUQ-QCGPJ)

This is a lightweight wrapper over [EasyVVUQ](https://github.com/UCL-CCS/EasyVVUQ) 
and [QCG Pilot Job Manager](https://github.com/vecma-project/QCG-PilotJob) that enables efficient execution 
of critical parts of EasyVVUQ workflows on HPC machines. 

EasyVVUQ-QCGPJ provides an API to configure EasyVVUQ to use QCG Pilot Job for execution of demanding 
parts of EasyVVUQ workflow in parallel. 

In the rest of this documentation EasyVVUQ-QCGPJ is shortened as EasyPJ and QCG Pilot Job as QCG PJ

## Requirements
The software requires pip 18.0.1+ for installation and Python 3.6+ for usage.

## Installation
The software could be easily installed from the github with pip:

```
$ pip3 install git+https://github.com/vecma-project/EasyVVUQ-QCGPJ.git@master
```

## Basic usage
The usage of EasyVVUQ with EasyPJ is very similar to the typical usage of EasyVVUQ. In the same way 
as it is in a regular EasyVVUQ script, the user defines the Campaign object and configures it to use 
specific encoders, decoders, samplers. The identical is also the part of collating results and analysis. 
The difference is in the middle, in the way how the campaign is executed. 

Basically, the code has to be instrumented with a few instructions required to configure EasyPJ. 
This comes down to:
1. Creation of the EasyPJ Executor object.
2. Creation of the QCG PJ Manager for the use by the Executor.
3. Configuration of EasyVVUQ Tasks to be executed by the Executor (in practice to be executed by QCG PJ Manager
as separate processes).
4. Execution of EasyVVUQ workflow consisted of the Tasks using the Executor.
5. Finalization 

## Example workflow
In order to explain the basic usage of EasyPJ API we will use an example. 
For the full code of this example please look into the `/tests/test_pce_pj_executor.py` test. 
Here we briefly outlines the main parts of that worklow concentrating on the EasyPJ 
and skipping fragments that are common with the standard execution of EasyVVUQ.

```python
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
    # START of EasyPJ part #
    ################################
    
    # Create Executor
    qcgpjexec = easypj.Executor()
    
    # Create QCG PJ-Manager with 4 cores 
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
    # END of EasyPJ part #
    ##############################

    # The rest of typical EasyVVUQ processing
    my_campaign.collate()
    # ...
    # Skipped code
    # ...
```
As you can see, the code required for parallel encoding and execution of the samples stored in an EasyVVUQ campaign 
is quite concise. The user just need to create an Executor object and using the methods of this object 
steer the rest of the process. Below we shortly describe particular elements of this process:

1. **Instantiation of the QCG Pilot Job Manager**
   
   The Executor internally uses QCG PJ Manager to submit Tasks. The Pilot Job Manager instance 
   needs to be set up for the Executor. To this end, it is possible to use one of two methods: 
   the presented `create_manager()` or `set_manager()`. More information on this topic 
   is presented in the section [QCG Pilot Job Manager initialisation](#qcg-pilot-job-manager-initialisation).
   
2. **Declaration of tasks**
   
   The Executor with the `add_task()` method allows to define a set of Tasks that will be executed 
   once the `run()` method is launched. A Task added with the `add_task()` method needs to be of some type. 
   Currently EaasyVVUQ-QCGPJ supports three types of Tasks: `ENCODING`, `EXECUTION` and `ENCODING_AND_EXECUTION`.
   These types are described in section [Task types](#task-types)

3. **Execution of tasks**
   
   The Executor configured with the QCG PJ Manager instance and filled with a set of appropriate Tasks is ready 
   to perform parallel processing of encoding and execution steps for all Campaign's samples using the `run()` method.
   This method takes two parameters: `campaign` and `submit_order`. The first parameter is a campaign object that 
   should be already configured and for which the samples should be generated. The second parameter, `submit_order` 
   is used to define a type of the scheme for the submission of Tasks in a specific order. 
   There are three possibile submission schemes / `submit_order`s: 
   `RUN_ORIENTED`, `PHASE_ORIENTED` and `RUN_ORIENTED_CONDENSED`.
   Description of the differences between these types is described in 
   the section [Submission schemes](#submission-schemes).
   
## Launching the workfow
The way of starting the defined workflow is typical, e.g.:
```bash
python3 tests/test_pce_pj_executor.py
```
Please only be sure that the environment is correct for both, the master script and the tasks. More information
on this topic is presented in the section 
[Passing the execution environment to QCG Pilot Job tasks](#passing-the-execution-environment-to-qcg-pilot-job-tasks).

It is worth noting that the workflow can be started in a common way on both local computer and cluster. 
In case of the batch execution on clusters, the above line can be put into the job script.
 

## QCG Pilot Job Manager initialisation
   The EasyPJ Executor needs to be configured to use an instance of QCG PJ Manager service. 
   It is possible to do this in two ways:
   * The first and simpler option is to use `create_manager()` method that creates QCG PJ Manager
     in a basic configuration. The method takes three optional parameters: 
     * `dir` to customise a working directory of the manager (by default current directory) 
     * `resources` to specify resources that should be assigned for the Pilot Job.
        If the parameter is not specified, the whole available resources will be assigned for the Pilot Job:
        it means that in case of running the Pilot Job inside a queuing system the whole allocation will be used. 
        If the parameter is provided, its specification should be consisted with the format supported by Local 
        mode of [QCG Pilot Job manager](https://github.com/vecma-project/QCG-PilotJob), i.e.
        `[NODE_NAME]:CORES[,[NODE_NAME]:CORES]...` 
     * `reserve_core` to specify if the manager service should run on a separate, reserved core 
       (by default `False`, which means that the manager's core will be shared with executed tasks).
     
   * The second and more advanced option is to use `set_manager()` method. This methods takes 
     a single parameter, which is an instance of externally created Pilot Job Manager instance.
     
     For the reference go to:
     [QCG Pilot Job documentation](https://github.com/vecma-project/QCG-PilotJob).

## Task types
   EasyPJ supports the following types of Tasks that may be executed by QCG PJ Manager:
   
   * `ENCODING`: this Task is used for the encoding of a single sample. 
   
   * `EXECUTION`: this Task is used for the execution of an application for a single sample. 
     The constructor of this Task requires the `application` parameter to be specified with the value defining 
     a command to run the application. 
     The `EXECUTION` Task for a given sample depends on the `ENCODING` Task for the same sample. 
   
   * `ENCODING&EXECUTION`: this Task is used for running both encoding and execution for a single sample.
     Similarly to the `EXECUTION` Task the constructor of this Task requires the `application`
     parameter to be specified with the value defining a command to run the application.
     
   The addition of a Task to Executor does not condition its later use - 
   this if the Task is actually used depends on a specific submission scheme that is selected 
   for the execution in the `run()` method of Executor. 
   In order to keep consistency of the environment only a single Task of a given type should be kept in the Executor. 

## Tasks requirements
   Tasks defined for execution by the QCG PJ system need to define their resource requirements. 
   In EasyPJ the specification of resource requirements for a Task is made directly via the Task's constructor,
   particularly by its second parameter - `TaskRequirements`. This object may be inited with 
   a combination of two parameters: `nodes` and `cores`. If the only specified parameter is `cores`, the Task
   will run on a specified number of cores regardless of their physical location 
   (the cores can be distributed on many nodes). If there are two parameters specified: `nodes` and `cores` the
   Task will use the number of cores requested by `cores` parameter on each of the nodes requested by `nodes` parameter.
   Therefore, in order to have good efficiency, for the multicore Tasks it is advised to specify 
   two parameters: `nodes` and `cores` (even if there is only a need to take one node). 
   
   Both `nodes` and `cores` parameters are of the `Resources` type and may be specified in the common way, 
   with the following keyword combinations:
   * `exact` - the exact number of resources should be used,
   * `min` - `max` - the resources number should be larger than `min` and lower than `max,
   * `min` - `split-into` - all available resources should be divided into chunks of size `split-into`, 
      but the size of chunks can't be smaller than `min`
      
   Example `TaskRequirements` specifications:
   * Use exactly 4 cores, regardeless of their location
   ```python
        TaskRequirements(cores=Resources(exact=4))
   ```
   * Use 4 cores on a single node
   ```python
        TaskRequirements(nodes=Resources(exact=1),cores=Resources(exact=4))
   ```
   * Use from 4 to 6 cores on each of 2 nodes
   ```python
        TaskRequirements(nodes=Resources(exact=2),cores=Resources(min=4,max=6))
   ```
   
   The algorithm used to define Task requirements in EasyPJ is inherited from the QCG PJ system. Further
   instruction can be found in the [QCG Pilot Job documentation](https://github.com/vecma-project/QCG-PilotJob)

## Submission schemes
   
   EasyPJ allows to submit tasks in a few predefined order schemes. The submission may be `RUN_ORIENTED`, 
   `PHASE_ORIENTED` or `RUN_ORIENTED_CONDENSED`. Depending on a specific usecase the efficiency of 
   these schemes may significantly differ.
   
   Below we shortly describe the three currently supported schemes of submission, 
   making the use of some kind of visual representation. Firstly, let's assume that we have a set of EasyVVUQ samples 
   marked as s1, s2, ..., sN. Then: 
   * `RUN_ORIENTED` - means that the tasks are submitted in a priority of RUN (aka sample); in other words we want to 
     complete whole processing (encoding and execution) for a given sample as soon as possible 
     and then go to the next sample. This order can be written as follows:
     
     `encoding(s1)->execution(s1)->encoding(s2)->execution(s2)->...->encoding(sN)->execution(sN)`
     
   * `PHASE_ORIENTED` - means that the tasks are submitted in a priority of PHASE; we want to complete encoding phase
     for all samples and then go to the execution phase for all samples. This order is as follows:
     
     `encoding(s1)->encoding(s2)->...->encoding(sN)->execution(s1)->execution(s2)->...->execution(sN)`
     
   * `RUN_ORIENTED_CONDENSED` - it is similar order to `RUN_ORIENTED`, but the encoding and execution are *condensed* 
     into a single PJ task. It could be expressed as: 
     
     `encoding&execution(s1)->encoding&execution(s2)->...->encoding&execution(sN)`
   
   The schemes use different task types to execute:
   * The `RUN_ORIENTED` and `PHASE_ORIENTED` schemes require `ENCODING` and `EXECUTION` tasks to be added to Executor. 
   * The `RUN_ORIENTED_CONDENSED` requires `ENCODING_AND_EXECUTION` task to be added to Executor
     

## Passing the execution environment to QCG Pilot Job tasks
Since every QCG PJ task is started in a separate process, it needs to be properly configured 
to run in an environment consistent with the requirements of the parent script. On the one hand, 
EasyVVUQ allows to easily recover information about the campaign from the database, but some environment settings, 
such as information about required environment modules or virtual environment, have to be passed in a different way. 
To this end, EasyPJ delivers a simple mechanism based on an idea of bash script, that is sourced by 
each task prior to its actual execution. The path to this file can be provided in `EASYPJ_CONFIG` environment variable. 
If this environment variable is available in the master script, it is also automatically passed to QCG PJ tasks. 

To the large extent the structure of the script provided in `EASYPJ_CONFIG` is fully custom. 
In this script a user can load modules, set further environment variables or even do simple calculations.
The content can be all things that are needed by a Task in prior of its actual execution. 
Very basic example of  the `EASYPJ_CONFIG` file may look as follows:
```bash
#!/bin/bash

module load openmpi/4.0
```

## External Encoders
EasyVVUQ allows to define custom encoders for specific use cases. This works without any issues as long as we are 
in a single process. However, in case we want to execute the encoding in a separate processes, there is a need to 
instruct these processes about the encoder. This information is partially available in the Campaign itself and 
can be recovered, but we need to somehow instruct EasyPJ code to import required python modules for the encoder. 
To this end once again we make use of environment variable - this time `ENCODER_MODULES`. 
The value of this variable should be the semicolon-separated list of the modules names, which are required by
the custom encoder. The modules will be dynamically loaded before the encoder is recovered, what resolves the problem.
In order to use `ENCODER_MODULES` variable we propose to define it in the `EASYPJ_CONFIG`

An example configuration of `EASYPJ_CONFIG` that includes specification of custom `ENCODER_MODULES` 
may look as follows (for the full test case please look in `tests/custom_encoder`):   

```bash
#!/bin/bash

# WORKS ONLY IN BASH - SHOULD BE CHANGED (EG. TO GLOBAL PATHS) IN CASE OF OTHER INTERPRETERS
this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
this_file=$(basename "${BASH_SOURCE[0]}")

PYTHONPATH="${PYTHONPATH}:${this_dir}"
ENCODER_MODULES="custom_encoder"
export PYTHONPATH
export ENCODER_MODULES

export EASYPJ_CONFIG=$this_dir/$this_file
```

