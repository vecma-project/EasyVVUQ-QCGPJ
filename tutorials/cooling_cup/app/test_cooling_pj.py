import os
import time

import chaospy as cp
import easyvvuq as uq
import easypj

from easypj import TaskRequirements, Resources
from easypj import Task, TaskType, SubmitOrder

# author: Jalal Lakhlili / Bartosz Bosak

__license__ = "LGPL"

COOLING_APP_DIR = os.environ["COOLING_APP"]

TEMPLATE = COOLING_APP_DIR + "/cooling.template"
APPLICATION = COOLING_APP_DIR + "/cooling_model.py"
ENCODED_FILENAME = "cooling_in.json"

if "SCRATCH" in os.environ:
    tmpdir = os.environ["SCRATCH"]
else:
    tmpdir = "/tmp/"
jobdir = os.getcwd()
uqmethod = "pce"


def test_cooling_pj():
    print("Job directory: " + jobdir)
    print("Temporary directory: " + tmpdir)

    # ---- CAMPAIGN INITIALISATION ---
    print("Initializing Campaign")
    # Set up a fresh campaign called "cooling"
    my_campaign = uq.Campaign(name='cooling', work_dir=tmpdir)

    # Define parameter space
    params = {
        "temp_init": {
            "type": "float",
            "min": 0.0,
            "max": 100.0,
            "default": 95.0},
        "kappa": {
            "type": "float",
            "min": 0.0,
            "max": 0.1,
            "default": 0.025},
        "t_env": {
            "type": "float",
            "min": 0.0,
            "max": 40.0,
            "default": 15.0},
        "out_file": {
            "type": "string",
            "default": "output.csv"}}

    output_filename = params["out_file"]["default"]
    output_columns = ["te", "ti"]

    # Create an encoder, decoder and collation element
    encoder = uq.encoders.GenericEncoder(
        template_fname=COOLING_APP_DIR + '/cooling.template',
        delimiter='$',
        target_filename=ENCODED_FILENAME)

    decoder = uq.decoders.SimpleCSV(target_filename=output_filename,
                                    output_columns=output_columns,
                                    header=0)

    collater = uq.collate.AggregateSamples(average=False)

    # Add the PCE app (automatically set as current app)
    my_campaign.add_app(name="cooling",
                        params=params,
                        encoder=encoder,
                        decoder=decoder,
                        collater=collater
                        )

    vary = {
        "kappa": cp.Uniform(0.025, 0.075),
        "t_env": cp.Uniform(15, 25)
    }

    # Create the sampler
    if uqmethod == 'pce':
        my_sampler = uq.sampling.PCESampler(vary=vary, polynomial_order=2)
    if uqmethod == 'qmc':
        my_sampler = uq.sampling.QMCSampler(vary=vary, n_samples=10)

    # Associate the sampler with the campaign
    my_campaign.set_sampler(my_sampler)

    print("Generating samples")
    # Will draw all (of the finite set of) samples
    my_campaign.draw_samples()

    print("Initialising EasyPJ Executor")
    # Create EasyVVUQ-QCGPJ Executor that will process the execution
    qcgpjexec = easypj.Executor()

    # Create QCG PJ-Manager that will utilise all available resources.
    # Refer to the documentation for customisation options.
    qcgpjexec.create_manager(dir=my_campaign.campaign_dir)

    # Define ENCODING task that will be used for execution of encodings using encoders specified by EasyVVUQ.
    # The presented specification of 'TaskRequirements' assumes the execution of each of the tasks on 1 core.
    qcgpjexec.add_task(Task(
        TaskType.ENCODING,
        TaskRequirements(cores=Resources(exact=1))
    ))

    # Define EXECUTION task that will be used for the actual execution of application.
    # The presented specification of 'TaskRequirements' assumes the execution of each of the tasks on 1 core,
    # but for more advanced parallel applications the resource requirements may be extended to use
    # many cores or even many resources.
    # Each task will execute the command provided in the 'application' parameter.
    qcgpjexec.add_task(Task(
        TaskType.EXECUTION,
        TaskRequirements(cores=Resources(exact=1)),
        application='python3 ' + APPLICATION + " " + ENCODED_FILENAME
    ))

    print("Starting the execution of QCG Pilot Job tasks")
    # Execute encodings and executions for all generated samples
    qcgpjexec.run(
        campaign=my_campaign,
        submit_order=SubmitOrder.RUN_ORIENTED)

    # Terminate QCG PJ-Manager
    print("Completing the execution")
    qcgpjexec.terminate_manager()

    print("Collating results")
    my_campaign.collate()

    print("Making analysis")

    if uqmethod == 'pce':
        analysis = uq.analysis.PCEAnalysis(sampler=my_sampler, qoi_cols=output_columns)
    if uqmethod == 'qmc':
        analysis = uq.analysis.QMCAnalysis(sampler=my_sampler, qoi_cols=output_columns)

    my_campaign.apply_analysis(analysis)

    results = my_campaign.get_last_analysis()
    stats = results['statistical_moments']['te']
    per = results['percentiles']['te']
    dist_out = results['output_distributions']['te']

    print("Stats: ")
    print(stats)
    print("Percentiles: ")
    print(per)
    print("Output distribution: ")
    print(dist_out)

    print("Processing completed")
    return stats, per, dist_out


if __name__ == "__main__":
    start_time = time.time()

    stats, per, dist_out = test_cooling_pj()

    end_time = time.time()
    print('>>>>> elapsed time = ', end_time - start_time)
