import os
import time

import chaospy as cp
import easyvvuq as uq

from eqi import TaskRequirements, Executor
from eqi import Task, TaskType, ProcessingScheme

# author: Jalal Lakhlili / Bartosz Bosak
__license__ = "LGPL"


TEMPLATE = "tests/app_cooling/cooling.template"
APPLICATION = "tests/app_cooling/cooling_model.py"
ENCODED_FILENAME = "cooling_in.json"

if "SCRATCH" in os.environ:
    tmpdir = os.environ["SCRATCH"]
else:
    tmpdir = "/tmp/"
jobdir = os.getcwd()


def setup_cooling_app():
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
    output_columns = ["te"]

    encoder = uq.encoders.GenericEncoder(
        template_fname=f"{jobdir}/{TEMPLATE}",
        delimiter='$',
        target_filename=ENCODED_FILENAME)
    decoder = uq.decoders.SimpleCSV(target_filename=output_filename,
                                    output_columns=output_columns)

    vary = {
        "kappa": cp.Uniform(0.025, 0.075),
        "t_env": cp.Uniform(15, 25)
    }

    cooling_sampler = uq.sampling.PCESampler(vary=vary, polynomial_order=2)
    cooling_stats = uq.analysis.PCEAnalysis(sampler=cooling_sampler, qoi_cols=output_columns)

    return params, encoder, decoder, cooling_sampler, cooling_stats


def test_encoding_execution_step_oriented():
    start_time = time.time()
    print("Running ENCODING AND EXECUTION STEP ORIENTED")
    print("Job directory: " + jobdir)
    print("Temporary directory: " + tmpdir)

    # ---- CAMPAIGN INITIALISATION ---
    print("Initializing Campaign")
    # Set up a fresh campaign called "cooling"
    my_campaign = uq.Campaign(name='cooling', work_dir=tmpdir)

    (params, encoder, decoder, cooling_sampler, cooling_stats) = setup_cooling_app()

    my_campaign.add_app(name="cooling",
                        params=params,
                        encoder=encoder,
                        decoder=decoder)

    # Associate the sampler with the campaign
    my_campaign.set_sampler(cooling_sampler)

    # Will draw all (of the finite set of samples)
    my_campaign.draw_samples()

    print("Preparing execution with QCG-PJ")
    qcgpjexec = Executor(my_campaign)

    # Create QCG PJ-Manager with 4 cores
    # (if you want to use all available resources remove resources parameter)
    qcgpjexec.create_manager(resources="4", log_level='debug')

    qcgpjexec.add_task(Task(
        TaskType.ENCODING,
        TaskRequirements(cores=1)
    ))

    qcgpjexec.add_task(Task(
        TaskType.EXECUTION,
        TaskRequirements(cores=1),
        application='python3 ' + jobdir + "/" + APPLICATION + " " + ENCODED_FILENAME
    ))

    print("Starting execution with QCG-PJ")
    qcgpjexec.run(processing_scheme=ProcessingScheme.STEP_ORIENTED)

    qcgpjexec.terminate_manager()

    print("Collating results")
    my_campaign.collate()

    print("Making analysis")

    my_campaign.apply_analysis(cooling_stats)

    results = my_campaign.get_last_analysis()

    stats = results.describe()['te'].loc['mean'], results.describe()['te'].loc['std']

    print("Processing completed")
    end_time = time.time()
    print('>>>>> elapsed time = ', end_time - start_time)
    return stats


def test_encoding_execution_sample_oriented():
    start_time = time.time()
    print("Running ENCODING AND EXECUTION SAMPLE ORIENTED")
    print("Job directory: " + jobdir)
    print("Temporary directory: " + tmpdir)

    # ---- CAMPAIGN INITIALISATION ---
    print("Initializing Campaign")
    # Set up a fresh campaign called "cooling"
    my_campaign = uq.Campaign(name='cooling', work_dir=tmpdir)

    (params, encoder, decoder, cooling_sampler, cooling_stats) = setup_cooling_app()

    my_campaign.add_app(name="cooling",
                        params=params,
                        encoder=encoder,
                        decoder=decoder)

    # Associate the sampler with the campaign
    my_campaign.set_sampler(cooling_sampler)

    # Will draw all (of the finite set of samples)
    my_campaign.draw_samples()

    print("Preparing execution with QCG-PJ")
    qcgpjexec = Executor(my_campaign)

    # Create QCG PJ-Manager with 4 cores
    # (if you want to use all available resources remove resources parameter)
    qcgpjexec.create_manager(resources="4", log_level='debug')

    qcgpjexec.add_task(Task(
        TaskType.ENCODING,
        TaskRequirements(cores=1)
    ))

    qcgpjexec.add_task(Task(
        TaskType.EXECUTION,
        TaskRequirements(cores=1),
        application='python3 ' + jobdir + "/" + APPLICATION + " " + ENCODED_FILENAME
    ))

    print("Starting execution with QCG-PJ")
    qcgpjexec.run(processing_scheme=ProcessingScheme.SAMPLE_ORIENTED)

    qcgpjexec.terminate_manager()

    print("Collating results")
    my_campaign.collate()

    print("Making analysis")

    my_campaign.apply_analysis(cooling_stats)

    results = my_campaign.get_last_analysis()

    stats = results.describe()['te'].loc['mean'], results.describe()['te'].loc['std']

    print("Processing completed")
    end_time = time.time()
    print('>>>>> elapsed time = ', end_time - start_time)
    return stats


def test_encoding_execution_sample_oriented_condensed():
    start_time = time.time()

    print("Running ENCODING EXECUTION SAMPLE ORIENTED CONDENSED")
    print("Job directory: " + jobdir)
    print("Temporary directory: " + tmpdir)

    # ---- CAMPAIGN INITIALISATION ---
    print("Initializing Campaign")
    # Set up a fresh campaign called "cooling"
    my_campaign = uq.Campaign(name='cooling', work_dir=tmpdir)

    (params, encoder, decoder, cooling_sampler, cooling_stats) = setup_cooling_app()

    my_campaign.add_app(name="cooling",
                        params=params,
                        encoder=encoder,
                        decoder=decoder)

    # Associate the sampler with the campaign
    my_campaign.set_sampler(cooling_sampler)

    # Will draw all (of the finite set of samples)
    my_campaign.draw_samples()

    my_campaign.populate_runs_dir()

    print("Preparing execution with QCG-PJ")
    qcgpjexec = Executor(my_campaign)

    # Create QCG PJ-Manager with 4 cores
    # (if you want to use all available resources remove resources parameter)
    qcgpjexec.create_manager(resources="4", log_level='debug')

    qcgpjexec.add_task(Task(
        TaskType.ENCODING_AND_EXECUTION,
        TaskRequirements(cores=1),
        application='python3 ' + jobdir + "/" + APPLICATION + " " + ENCODED_FILENAME
    ))

    print("Starting execution with QCG-PJ")
    qcgpjexec.run(processing_scheme=ProcessingScheme.SAMPLE_ORIENTED_CONDENSED)

    qcgpjexec.terminate_manager()

    print("Collating results")
    my_campaign.collate()

    print("Making analysis")

    my_campaign.apply_analysis(cooling_stats)

    results = my_campaign.get_last_analysis()

    stats = results.describe()['te'].loc['mean'], results.describe()['te'].loc['std']

    print("Processing completed")

    end_time = time.time()
    print('>>>>> elapsed time = ', end_time - start_time)

    return stats


def test_execution():
    start_time = time.time()

    print("Running EXECUTION")
    print("Job directory: " + jobdir)
    print("Temporary directory: " + tmpdir)

    # ---- CAMPAIGN INITIALISATION ---
    print("Initializing Campaign")
    # Set up a fresh campaign called "cooling"
    my_campaign = uq.Campaign(name='cooling', work_dir=tmpdir)

    (params, encoder, decoder, cooling_sampler, cooling_stats) = setup_cooling_app()

    my_campaign.add_app(name="cooling",
                        params=params,
                        encoder=encoder,
                        decoder=decoder)

    # Associate the sampler with the campaign
    my_campaign.set_sampler(cooling_sampler)

    # Will draw all (of the finite set of samples)
    my_campaign.draw_samples()

    my_campaign.populate_runs_dir()

    print("Preparing execution with QCG-PJ")
    qcgpjexec = Executor(my_campaign)

    # Create QCG PJ-Manager with 4 cores
    # (if you want to use all available resources remove resources parameter)
    qcgpjexec.create_manager(resources="4", log_level='debug')

    qcgpjexec.add_task(Task(
        TaskType.EXECUTION,
        TaskRequirements(cores=1),
        application='python3 ' + jobdir + "/" + APPLICATION + " " + ENCODED_FILENAME
    ))

    print("Starting execution with QCG-PJ")
    qcgpjexec.run(processing_scheme=ProcessingScheme.EXEC_ONLY)

    qcgpjexec.terminate_manager()

    print("Collating results")
    my_campaign.collate()

    print("Making analysis")

    my_campaign.apply_analysis(cooling_stats)

    results = my_campaign.get_last_analysis()

    stats = results.describe()['te'].loc['mean'], results.describe()['te'].loc['std']

    print("Processing completed")

    end_time = time.time()
    print('>>>>> elapsed time = ', end_time - start_time)

    return stats


if __name__ == "__main__":
    test_encoding_execution_step_oriented()
    test_encoding_execution_sample_oriented()
    test_encoding_execution_sample_oriented_condensed()
    test_execution()
