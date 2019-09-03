import sys
import os
# from easypj.pj_configurator import PJConfigurator

if __name__ == "__main__":

    print("EASYPJ EXECUTE: ")
    print(sys.argv)

    if len(sys.argv) < 3:
        sys.exit("Usage: python3 easyvvuq_execute.py RUN_DIR COMMAND")

    run_dir = sys.argv[1]
    command = " ".join(sys.argv[2:])

    print(f"Executing {command} in directory {run_dir}")
    full_cmd = 'cd ' + run_dir + '\n' + command + '\n'

    result = os.system(full_cmd)
    if result != 0:
        sys.exit("Non-zero exit code from command '" + full_cmd + "'\n")
