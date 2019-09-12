# EasyVVUQ-QCGPJ
This is a lightweight wrapper over [EasyVVUQ](https://github.com/UCL-CCS/EasyVVUQ) and [QCG Pilot Job Manager](https://github.com/vecma-project/QCG-PilotJob) that enables efficient execution of critical parts of EasyVVUQ workflows on HPC machines. 

## Requirements
The software requires pip 18.0.1+ for installation and Python 3.6+ for usage.

## Installation
The software could be easily installed from the github with pip:

```
$ pip3 install git+https://github.com/vecma-project/EasyVVUQ-QCGPJ.git@master
```

## Basic usage
Usage of the EasyVVUQ together with QCG Pilot Job tasks requires a few changes to the typical EasyVVUQ script. 
The required extensions are as follows:
1. QCG Pilot Job Manager should be instantiated.
2. For the generated EasyVVUQ samples an appropriate QCG Pilot Job workflow should be constructed with the tasks for encoding and application execution. 
3. Since the encoding and application execution tasks runs as new processes, they need to be a separate pieces of code. There are prepared helper scripts that can be used to invoke encoding and execution as separate processes.

## Example workflow
For the full example please look into the `/tests/test_cooling_pj.py` test, where a workflow for cooling coffee mug model is presented. Here we briefly outlines the main parts of that worklow concentrating on the Pilot Job integration and skipping fragments that are common with the standard execution of EasyVVUQ.

```python
import os
import chaospy as cp
import easyvvuq as uq

from qcg.appscheduler.api.job import Jobs
from qcg.appscheduler.api.manager import LocalManager

cwd = os.getcwd()

def test_cooling_pj(tmpdir):

    # Initializing the Pilot Job Manager
    client_conf = {'log_level': 'DEBUG'}
    m = LocalManager([], client_conf)
  
    # Set up a fresh campaign called "cooling"
    my_campaign = uq.Campaign(name='cooling', work_dir=tmpdir)
    # ... 
    # Skipped the typical code of EasyVVUQ that initialises the campaign with encoders, decoders etc. 
    # ...
    my_campaign.draw_samples()

    # Execute encode -> execute for each run using QCG-PJ
    print("Starting submission of tasks to QCG Pilot Job Manager")
    for run in my_campaign.list_runs():

        key = run[0]
        run_dir = run[1]['run_dir']

        enc_args = [
            my_campaign.db_type,
            my_campaign.db_location,
            'FALSE',
            "cooling",
            "cooling",
            key
        ]

        exec_args = [
            run_dir,
            'easyvvuq_app',
            'python3 ' + cwd + "/tests/cooling/cooling_model.py", "cooling_in.json"
        ]

        encode_job = {
            "name": 'encode_' + key,
            "execution": {
                "exec": 'easyvvuq_encode',
                "args": enc_args,
                "wd": cwd
            },
            "resources": {
                "numCores": {
                    "exact": 1
                }
            }
        }

        execute_job = {
            "name": 'execute_' + key,
            "execution": {
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "wd": cwd
            },
            "resources": {
                "numCores": {
                    "exact": 1
                }
            },
            "dependencies": {
                "after": ["encode_" + key]
            }
        }

        m.submit(Jobs().addStd(encode_job))
        m.submit(Jobs().addStd(execute_job))

    # wait for completion of all PJ tasks and terminate the PJ manager
    m.wait4all()
    m.finish()
    m.stopManager()
    m.cleanup()

    # sync states of runs in the campaign after execution of PJ
    def update_status(run_id, run_data):
        my_campaign.campaign_db.set_run_statuses([run_id], uq.constants.Status.ENCODED)

    my_campaign.call_for_each_run(update_status, status=uq.constants.Status.NEW)

    # The rest of typical EasyVVUQ processing
    my_campaign.collate()
    # ...
    # Skipped code
    # ...
```
As you can see, the biggest part of the code is occupied by the loop over the `runs` stored in the `my_campaign` object. This is a typical way of description of the workflow for QCG Pilot Job - for the reference go to [QCG Pilot Job Manager instructions](https://github.com/vecma-project/QCG-PilotJob). The critical is here the specification of parameters for execution of particular tasks. The `exec` parameter for the encode_job task takes here `easyvvuq_encode`, simillarly `exec` for the execute_job task takes `easyvvuq_execute`. There is also an additional script wrapping the actual invocation of the application code `easyvvuq_app`. The idea of all these scripts is to simplify execution of encoding and application as separate processes. `easyvvuq_encode` and `easyvvuq_execute` internally start the respective python code for the encoding and execution. All the scripts can source the environment configuration script file specified in the `EASYPJ_CONF` environment variable. This allows to easily adjust the execution environment to specific system. An example such script may look as follows:
```bash
#!/bin/bash

# init virtualenv
. ~/.virtualenvs/easyvvuq-qcgpj/bin/activate
```

In the presented scenario, the loop iterates one by one over runs and for each individual run the two tasks, for encoding and execution are submitted to be started by QCG Pilot Job Manager. Thus the dependency scope is limited to a single run. This is quite typical scenario, but it is not the only possible way to start EasyVVUQ with QCG Pilot Job. QCG Pilot Job provides good flexibility and the scenario may be modified depending on particular needs. For example, it may be more optimal for some use cases to define two loops over runs and firstly execute all encoding steps and then all execution steps. 

## Start
The start of the defined workflow is typical:
```bash
python3 tests/test_cooling_pj.py
```
