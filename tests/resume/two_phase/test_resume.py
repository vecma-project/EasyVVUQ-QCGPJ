import os
import time
import shutil
from glob import glob

import chaospy as cp
import easyvvuq as uq

import eqi

# author: Jalal Lakhlili / Bartosz Bosak
__license__ = "LGPL"


TEMPLATE = "tests/app_cooling/cooling.template"
APPLICATION = "tests/app_cooling/cooling_model.py"
ENCODED_FILENAME = "cooling_in.json"
CAMPAIGN_STATE_FILE = "state_before_eqi"
CAMPAIGN_INTERRUPTED_DIR = "campaign_interrupted"
CAMPAIGN_RESUMED_DIR = "campaign_resumed"

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

    # we get the first eqi-* dir
    eqi_dirs = glob(f'{tmpdir}{CAMPAIGN_RESUMED_DIR}/.eqi-*')
    state_file = f'{eqi_dirs[0]}/{eqi.StateKeeper.EQI_CAMPAIGN_STATE_FILE_NAME}'

    # Set up a fresh campaign called "cooling"
    my_campaign = uq.Campaign(
        state_file=state_file,
        work_dir=tmpdir,
        relocate={
            'work_dir': tmpdir,
            'campaign_dir': CAMPAIGN_RESUMED_DIR,
            'db_location': f'sqlite:////{tmpdir}{CAMPAIGN_RESUMED_DIR}/campaign.db'
        })

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
    output_columns = ["te"]

    analysis = uq.analysis.PCEAnalysis(sampler=my_sampler, qoi_cols=output_columns)

    my_campaign.apply_analysis(analysis)

    results = my_campaign.get_last_analysis()
    stats = results.describe()['te'].loc['mean'], results.describe()['te'].loc['std']

    print("Processing completed")
    return stats


def __prepare_data():
    shutil.rmtree(f'{tmpdir}{CAMPAIGN_RESUMED_DIR}', ignore_errors=True)
    shutil.copytree(f'tests/resume/two_phase/uncompleted_data/{CAMPAIGN_INTERRUPTED_DIR}', f'{tmpdir}{CAMPAIGN_RESUMED_DIR}')


if __name__ == "__main__":
    start_time = time.time()

    stats = test_cooling_pj()
    print(stats)

    end_time = time.time()
    print('>>>>> elapsed time = ', end_time - start_time)
