import os
import time
import easyvvuq as uq
import chaospy as cp
import eqi
from eqi import TaskRequirements, Resources
from eqi import Task, TaskType, SubmitOrder


# Global params
TEMPLATE_1 = "tests/multi_app/app1.template"
APPLICATION_1 = "tests/multi_app/app1.py"
ENCODED_FILENAME_1 = "app1_in.json"

TEMPLATE_2 = "tests/multi_app/app2.template"
APPLICATION_2 = "tests/multi_app/app2.py"
ENCODED_FILENAME_2 = "app2_in.json"

tmpdir = "/tmp/"
jobdir = os.getcwd()


# The 1st model
def setup_app1():
    params = {
        "a0": {
            "type": "float",
            "default": 0.5},
        "a1": {
            "type": "float",
            "default": 1.5},
        "out_file": {
            "type": "string",
            "default": "output1.csv"}}

    vary = {
        "a0": cp.Normal(0.5, 0.15),
        "a1": cp.Uniform(0.5, 2.5),
    }

    output_filename = params["out_file"]["default"]
    output_columns = ["u1"]

    encoder = uq.encoders.GenericEncoder(
        template_fname=TEMPLATE_1,
        delimiter='$',
        target_filename=ENCODED_FILENAME_1)
    decoder = uq.decoders.SimpleCSV(target_filename=output_filename,
                                    output_columns=output_columns,
                                    header=0)
    collater = uq.collate.AggregateSamples(average=False)

    sampler = uq.sampling.PCESampler(vary=vary, polynomial_order=2)
    action = uq.actions.ExecuteLocal(APPLICATION_1 + " " + ENCODED_FILENAME_1)
    stats = uq.analysis.PCEAnalysis(sampler=sampler, qoi_cols=output_columns)

    return params, encoder, decoder, collater, sampler, action, stats


# The 1st model
def setup_app2():
    params = {
        "b0": {
            "type": "float",
            "default": 0.5},
        "b1": {
            "type": "float",
            "default": 0.05},
        "out_file": {
            "type": "string",
            "default": "output2.csv"}}

    vary = {
        "b0": cp.Normal(0.5, 0.15),
        "b1": cp.Uniform(0.03, 0.07)
    }

    output_filename = params["out_file"]["default"]
    output_columns = ["u2"]

    encoder = uq.encoders.GenericEncoder(
        template_fname=TEMPLATE_2,
        delimiter='$',
        target_filename=ENCODED_FILENAME_2)
    decoder = uq.decoders.SimpleCSV(target_filename=output_filename,
                                    output_columns=output_columns,
                                    header=0)
    collater = uq.collate.AggregateSamples(average=False)

    sampler = uq.sampling.PCESampler(vary=vary, polynomial_order=2)
    stats = uq.analysis.PCEAnalysis(sampler=sampler, qoi_cols=output_columns)

    return params, encoder, decoder, collater, sampler, stats


def exec_pj(campaign, cores, app, encoded_filename):
    qcgpjexec = eqi.Executor(campaign)
    qcgpjexec.create_manager(resources=cores, log_level='debug')
    qcgpjexec.add_task(Task(
        TaskType.EXECUTION,
        TaskRequirements(cores=Resources(exact=1)),
        application='python3 ' + jobdir + "/" + app + " " + encoded_filename
    ))
    qcgpjexec.run(submit_order=SubmitOrder.EXEC_ONLY)
    qcgpjexec.terminate_manager()


def test_multi_app_pj():
    # Campaign for mutli-app
    campaign = uq.Campaign(name='multiapp_', work_dir=tmpdir)

    # 1st application
    (params1, encoder1, decoder1, collater1, sampler1, action1, stats1) = setup_app1()

    campaign.add_app(name="app1",
                     params=params1,
                     encoder=encoder1,
                     decoder=decoder1,
                     collater=collater1)

    campaign.set_app("app1")
    campaign.set_sampler(sampler1)
    campaign.draw_samples()
    campaign.populate_runs_dir()
    campaign.apply_for_each_run_dir(action1)
    campaign.collate()
    campaign.apply_analysis(stats1)
#    results1 = campaign.get_last_analysis()

#    stat_1 = results1['statistical_moments']["u1"]

    # 2st application
    (params2, encoder2, decoder2, collater2, sampler2, stats2) = setup_app2()

    campaign.add_app(name="app2",
                     params=params2,
                     encoder=encoder2,
                     decoder=decoder2,
                     collater=collater2)

    campaign.set_app("app2")
    campaign.set_sampler(sampler2)
    campaign.draw_samples()
    campaign.populate_runs_dir()
    # use QCG-PJ for this model
    exec_pj(campaign, '4', APPLICATION_2, ENCODED_FILENAME_2)

    campaign.collate()
    campaign.apply_analysis(stats2)
#    results2 = campaign.get_last_analysis()

#    stat_2 = results2['statistical_moments']["u2"]


# Main
if __name__ == "__main__":
    start_time = time.time()

    test_multi_app_pj()

    end_time = time.time()
    print('>>>>> elapsed time = ', end_time - start_time)
