from enum import Enum


class ResumeLevel(Enum):
    """ Typically the resumed task will start in a working directory of the previous, not-completed run.
    Sometimes the partially generated output or intermediate files could be a problem. Therefore
    EQI tries to help in this matter by providing dedicated mechanisms for automatic recovery.
    However, this depends on the use case, how much the automatism can interfere with the resume logic.
    Therefore there are a few levels of automatic recovery available.
    """

    DISABLED = \
        "Automatic resume is fully disabled"
    BASIC = \
        "For the tasks creating run directories, the resume checks if an unfinished task " \
        "created such directory. If such directory is available, this is automatically removed before " \
        "the start of the resumed task"
    MODERATE = \
        "This level processes all operations offered by BASIC level, and adds the following." \
        "At the beginning of a task's execution, the list of directories and files in a run directory " \
        "is generated and stored. The resumed task checks for the differences and remove new files and directories" \
        "in order to resurrect the initial state."
