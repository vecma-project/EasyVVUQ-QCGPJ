import os
import time
from tempfile import mkdtemp

import chaospy as cp
import easyvvuq as uq

from qcg.pilotjob.api.job import Jobs
from qcg.pilotjob.api.manager import LocalManager

# author: Jalal Lakhlili / Bartosz Bosak

__license__ = "LGPL"


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

    # Create an encoder, decoder and collation element for PCE test app
    encoder = uq.encoders.GenericEncoder(
        template_fname=jobdir + '/tests/cooling/cooling.template',
        delimiter='$',
        target_filename='cooling_in.json')

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
    else:
        my_sampler = uq.sampling.QMCSampler(vary=vary, n_samples=10)

    # Associate the sampler with the campaign
    my_campaign.set_sampler(my_sampler)

    # Will draw all (of the finite set of samples)
    my_campaign.draw_samples()

    # ---- QCG PILOT JOB INITIALISATION ---
    # set QCG-PJ temp directory
    qcgpj_tempdir = mkdtemp(None, ".qcgpj-", my_campaign.campaign_dir)

    # establish available resources
    cores = 4

    # switch on debugging of QCGPJ API (client part)
    client_conf = {'log_file': qcgpj_tempdir + '/api.log', 'log_level': 'DEBUG'}

    # create local LocalManager (service part)
    m = LocalManager(['--log', 'debug',
                      '--nodes', str(cores),
                      '--wd', qcgpj_tempdir],
                     client_conf)

    # This can be used for execution of the test using a separate (non-local) instance of PJManager
    #
    # get available resources
    # res = m.resources()
    # remove all jobs if they are already in PJM
    # (required when executed using the same QCG-Pilot Job Manager)
    # m.remove(m.list().keys())

    print("Available resources:\n%s\n" % str(m.resources()))

    # ---- EXECUTION ---
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
            'python3 ' + jobdir + "/tests/cooling/cooling_model.py", "cooling_in.json"
        ]

        encode_task = {
            "name": 'encode_' + key,
            "execution": {
                "exec": 'easyvvuq_encode',
                "args": enc_args,
                "wd": my_campaign.campaign_dir,
                "stdout": my_campaign.campaign_dir + '/encode_' + key + '.stdout',
                "stderr": my_campaign.campaign_dir + '/encode_' + key + '.stderr'
            },
            "resources": {
                "numCores": {
                    "exact": 1
                }
            }
        }

        execute_task = {
            "name": 'execute_' + key,
            "execution": {
                "exec": 'easyvvuq_execute',
                "args": exec_args,
                "wd": my_campaign.campaign_dir,
                "stdout": my_campaign.campaign_dir + '/execute_' + key + '.stdout',
                "stderr": my_campaign.campaign_dir + '/execute_' + key + '.stderr'
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

        m.submit(Jobs().add_std(encode_task))
        m.submit(Jobs().add_std(execute_task))

    # wait for completion of all PJ tasks and terminate the PJ manager
    m.wait4all()
    m.finish()
    m.kill_manager_process()
    m.cleanup()

    print("Syncing state of campaign after execution of PJ")

    def update_status(run_id, run_data):
        my_campaign.campaign_db.set_run_statuses([run_id], uq.constants.Status.ENCODED)

    my_campaign.call_for_each_run(update_status, status=uq.constants.Status.NEW)

    print("Collating results")
    my_campaign.collate()

    # Post-processing analysis
    print("Making analysis")
    if uqmethod == 'pce':
        analysis = uq.analysis.PCEAnalysis(sampler=my_sampler, qoi_cols=output_columns)
    else:
        analysis = uq.analysis.QMCAnalysis(sampler=my_sampler, qoi_cols=output_columns)

    my_campaign.apply_analysis(analysis)

    results = my_campaign.get_last_analysis()

    # Get Descriptive Statistics
    stats = results['statistical_moments']['te']

    print("Processing completed")
    return stats


if __name__ == "__main__":
    start_time = time.time()

    stats = test_cooling_pj()

    end_time = time.time()
    print('>>>>> elapsed time = ', end_time - start_time)
