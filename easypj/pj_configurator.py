import json
import os
import sys
import easyvvuq.campaign as cn

# author: Bartosz Bosak
__license__ = "LGPL"

CONF_FILE = "pj_conf.json"
RUNS_DIR = "runs"


class PJConfigurator:

    @staticmethod
    def get_class(kls):
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m

    def __init__(self, campaign=None):
        if isinstance(campaign, cn.Campaign):
            self.__app_info = campaign.app_info
            self.__encoder = \
                type(campaign.encoder).__module__ + "." + type(campaign.encoder).__qualname__
            self.__conf_file = os.path.join(campaign.app_info['campaign_dir'], CONF_FILE)
            self.__runs_dir = os.path.join(self.__app_info['campaign_dir'], RUNS_DIR)
            self.__runs = campaign.runs

        if isinstance(campaign, str):
            self.__conf_file = os.path.join(campaign, CONF_FILE)

    @staticmethod
    def load(campaign_dir):
        print(f"Loading PJ Configuration from: {campaign_dir}")
        pjc = PJConfigurator(campaign_dir)

        with open(pjc.__conf_file, "r") as infile:
            input_json = json.load(infile)

        # Check that it contains an "app" and a "params" block
        if "app_info" not in input_json:
            raise RuntimeError("Input does not contain an 'app_info' block")

        if "encoder" not in input_json:
            raise RuntimeError("Input does not contain an 'encoder' block")

        if "runs_dir" not in input_json:
            raise RuntimeError("Input does not contain an 'runs_dir' block")

        if "runs" not in input_json:
            raise RuntimeError("Input does not contain an 'runs' block")

        pjc.__app_info = input_json["app_info"]
        pjc.__encoder = input_json["encoder"]
        pjc.__runs_dir = input_json["runs_dir"]
        pjc.__runs = input_json["runs"]
        return pjc

    def save(self):
        output_json = {
            "app_info": self.__app_info,
            "encoder": self.__encoder,
            "runs_dir": self.__runs_dir,
            "runs": self.__runs,
        }

        print(f"Saving PJ Configuration to: {self.__conf_file}")
        with open(self.__conf_file, "w") as outfile:
            json.dump(output_json, outfile, indent=4)

    def init_runs_dir(self):
        """Init runs directory for all runs

        This just creates a parent directory for runs

        Parameters
        ----------

        Returns
        -------

        """
        # Build a temp directory to store run files (unless it already exists)
        for run_id, run_data in self.__runs.items():
            run_data['run_dir'] = os.path.join(self.__runs_dir, run_id)

        runs_dir = self.__runs_dir
        if os.path.exists(runs_dir):
            raise RuntimeError(f"Cannot create a runs directory to "
                               f"populate, as it already exists: "
                               f"{runs_dir}")

        print(f"Creating temp runs directory: {runs_dir}")
        os.makedirs(runs_dir)

    def encode(self, run_id):
        """Encode given run from the universal form to the form understandable by application

        Takes the encoder established during the initialization phase
        to encode input data to the form understandable by the application

        Parameters
        ----------
        run_id: run identifier
        run_data: run data used by the encoder

        Returns
        -------

        """
        run = self.__runs[run_id]
        target_dir = os.path.join(self.__runs_dir, run_id)
        os.makedirs(target_dir)

        cwd = os.getcwd()
        print("CWD: " + cwd)

        print(f"Encoding {run_id} using encoder {self.__encoder}")
        encoder_class = self.get_class(self.__encoder)
        encoder = encoder_class(self.__app_info)
        encoder.encode(params=run, target_dir=target_dir)

    def execute(self, run_id, command):
        """Execute command in run directory

        Executes the command within a directory of specific run


        Parameters
        ----------
        run_id: run identifier
        command: command to execute

        Returns
        -------

        """
        target_dir = os.path.join(self.__runs_dir, run_id)

        print(f"Executing {command} in directory {target_dir}")
        full_cmd = 'cd ' + target_dir + '\n' + command + '\n'

        result = os.system(full_cmd)
        if result != 0:
            sys.exit("Non-zero exit code from command '" + full_cmd + "'\n")
