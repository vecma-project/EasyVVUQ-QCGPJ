import sys
from easypj.pj_configurator import PJConfigurator

if __name__ == "__main__":

    if len(sys.argv) != 3:
        sys.exit("Usage: python3 easyvvuq_encode.py CAMPAIGN_DIR RUN_ID")

    campaign_dir = sys.argv[1]
    run_id = sys.argv[2]

    pjc = PJConfigurator.load(campaign_dir)
    pjc.encode(run_id)
