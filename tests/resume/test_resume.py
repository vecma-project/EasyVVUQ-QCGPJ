import os
import time
import shutil

import chaospy as cp
import easyvvuq as uq

import eqi

# author: Jalal Lakhlili / Bartosz Bosak
__license__ = "LGPL"


TEMPLATE = "tests/APP_COOLING/cooling.template"
APPLICATION = "tests/APP_COOLING/cooling_model.py"
ENCODED_FILENAME = "cooling_in.json"
CAMPAIGN_STATE_FILE = "state_before_eqi"
UNCOMPLETED_CAMPAIGN_DIR = "cooling64nwm83c"

if "SCRATCH" in os.environ:
    tmpdir = os.environ["SCRATCH"]
else:
    tmpdir = "/tmp/"

jobdir = os.getcwd()


def test_cooling_pj():
    print("Job directory: " + jobdir)
    print("Temporary directory: " + tmpdir)

    __prepare_data()

    # ---- CAMPAIGN RE-INITIALISATION ---
    print("Loading Campaign")
    # Set up a fresh campaign called "cooling"
    my_campaign = uq.Campaign(
        state_file=f'{tmpdir}/{UNCOMPLETED_CAMPAIGN_DIR}/{CAMPAIGN_STATE_FILE}',
        work_dir=tmpdir)

    print("Starting execution")
    qcgpjexec = eqi.Executor(my_campaign)

    # Create QCG PJ-Manager with 4 cores
    # (if you want to use all available resources remove resources parameter)
    qcgpjexec.create_manager(resources="4", log_level='debug')

    qcgpjexec.terminate_manager()

    print("Collating results")
    my_campaign.collate()

    print("Making analysis")

    my_sampler = my_campaign.get_active_sampler()
    output_columns = ["te", "ti"]

    analysis = uq.analysis.QMCAnalysis(sampler=my_sampler, qoi_cols=output_columns)

    my_campaign.apply_analysis(analysis)

    results = my_campaign.get_last_analysis()
    stats = results.describe()['te']['mean'], results.describe()['te']['std']

    print("Processing completed")
    return stats


def __prepare_data():
    shutil.rmtree(f'{tmpdir}/{UNCOMPLETED_CAMPAIGN_DIR}', ignore_errors=True)
    shutil.copytree(f'tests/resume/uncompleted_data/{UNCOMPLETED_CAMPAIGN_DIR}', f'{tmpdir}/{UNCOMPLETED_CAMPAIGN_DIR}')


if __name__ == "__main__":
    start_time = time.time()

    stats = test_cooling_pj()
    print(stats)

    end_time = time.time()
    print('>>>>> elapsed time = ', end_time - start_time)
