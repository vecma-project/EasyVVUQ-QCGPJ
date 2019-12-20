import os
import time

import chaospy as cp
import easyvvuq as uq
import easypj

from easypj import TaskRequirements, Resources
from easypj import Task, TaskType, SubmitOrder

from custom_encoder import CustomEncoder

# author: Jalal Lakhlili / Bartosz Bosak
__license__ = "LGPL"

jobdir = os.getcwd()

TEMPLATE = "tests/cooling/cooling.template"
APPLICATION = "tests/cooling/cooling_model.py"
ENCODED_FILENAME = "cooling_in.json"


def test_cooling_pj(tmpdir):
    tmpdir = str(tmpdir)

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
    # encoder = uq.encoders.GenericEncoder(
    encoder = CustomEncoder(
        template_fname=jobdir + '/' + TEMPLATE,
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
    my_sampler = uq.sampling.PCESampler(vary=vary, polynomial_order=3)
    # Associate the sampler with the campaign
    my_campaign.set_sampler(my_sampler)

    # Will draw all (of the finite set of samples)
    my_campaign.draw_samples()

    print("Starting execution")
    qcgpjexec = easypj.Executor()
    qcgpjexec.create_manager(dir=my_campaign.campaign_dir, resources='4')

    qcgpjexec.add_task(Task(
        TaskType.ENCODING,
        TaskRequirements(cores=Resources(exact=1))
    ))

    qcgpjexec.add_task(Task(
        TaskType.EXECUTION,
        TaskRequirements(cores=Resources(exact=1)),
        application='python3 ' + jobdir + "/" + APPLICATION + " " + ENCODED_FILENAME
    ))

    # qcgpjexec.add_task(Task(
    #     TaskType.ENCODING_AND_EXECUTION,
    #     TaskRequirements(cores=Resources(exact=1)),
    #     application='python3 ' + jobdir + "/" + APPLICATION + " " + ENCODED_FILENAME
    # ))

    qcgpjexec.run(
        campaign=my_campaign,
        submit_order=SubmitOrder.RUN_ORIENTED)
    #    submit_order=SubmitOrder.RUN_ORIENTED_CONDENSED)

    qcgpjexec.terminate_manager()

    print("Collating results")
    my_campaign.collate()

    print("Making analysis")
    pce_analysis = uq.analysis.PCEAnalysis(sampler=my_sampler,
                                           qoi_cols=output_columns)
    my_campaign.apply_analysis(pce_analysis)

    results = my_campaign.get_last_analysis()
    stats = results['statistical_moments']['te']
    sob1 = results['sobols_first']['te']

    print("Processing completed")
    return stats, sob1


if __name__ == "__main__":
    start_time = time.time()
    tmp_dir = os.environ['SCRATCH']
    if tmp_dir is None:
        tmp_dir = "/tmp/"

    stats, sob1 = test_cooling_pj(tmp_dir)

    end_time = time.time()
    print('Elapsed time = ', end_time - start_time)

    _PLOT=False
    if _PLOT:
        print("Save results in test_cooling.png plot")
        import matplotlib.pyplot as plt
        import numpy as np

        mean = stats["mean"]
        std = stats["std"]

        s1_kappa = sob1["kappa"]
        s1_t_env = sob1["t_env"]

        t = np.linspace(0, 200, 150)
        plt.switch_backend('agg')
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(16,6))

        ax1.plot(t, mean, 'g-', alpha=0.75, label='Mean')
        ax1.plot(t, mean-std, 'b-', alpha=0.25)
        ax1.plot(t, mean+std, 'b-', alpha=0.25)
        ax1.fill_between(t, mean-std, mean+std, alpha=0.25, label=r'Mean $\pm$ deviation')
        ax1.set_xlabel("time")
        ax1.set_ylabel("T", color='b')
        ax1.tick_params('y', colors='b')
        ax1.grid()
        ax1.legend()
        ax1.set_title('Statistical Moments')

        ax2.plot(t, s1_kappa, '-', color ='#248BF2', label=r'$\kappa$')
        ax2.plot(t, s1_t_env, '-', color ='#9402E8', alpha=0.6,label=r'$T_{env}$')
        ax2.set_xlabel('Time (min)')
        ax2.set_ylabel('First-order Sobol indices')
        ax2.set_title('Sensitivity Analysis')
        ax2.grid()
        ax2.legend()

        plt.subplots_adjust(wspace=0.35)
        fig.savefig("test_cooling")
        plt.close(fig)
