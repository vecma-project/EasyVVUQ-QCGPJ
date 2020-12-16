import sys
import os

if __name__ == "__main__":

    if len(sys.argv) < 3:
        sys.exit("Usage: python3 easyvvuq_execute.py RUN_DIR COMMAND")

    run_dir = sys.argv[1]
    command = " ".join(sys.argv[2:])

    exec_dir = os.path.dirname(os.path.abspath(os.getcwd()))
    print(f"Executing {command} in directory {exec_dir}/{run_dir}")
    full_cmd = f'cd {exec_dir}/{run_dir}\n {command}\n'

    result = os.system(full_cmd)
    if result != 0:
        sys.exit("Non-zero exit code from command '" + full_cmd + "'\n")
