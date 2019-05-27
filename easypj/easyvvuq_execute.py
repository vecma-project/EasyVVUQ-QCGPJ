import sys
from easypj.pj_configurator import PJConfigurator

if __name__ == "__main__":

    if len(sys.argv) < 4:
        sys.exit("Usage: python3 easyvvuq_execute.py CAMPAIGN_DIR RUN_ID COMMAND")

    campaign_dir = sys.argv[1]
    run_id = sys.argv[2]
    command = " ".join(sys.argv[3:])

    pjc = PJConfigurator.load(campaign_dir)
    pjc.execute(run_id, command)
