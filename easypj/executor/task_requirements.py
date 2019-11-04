class TaskRequirements:

    def __init__(self, cores=None, min_cores=None, max_cores=None):
        """
        Parameters for Execution task executed within QCG Pilot Job

        Parameters
        ----------
        cores : int
            the exact number of cores to use for an exec task
        """

        if cores:
            if min_cores or max_cores:
                raise ValueError("The 'cores' parameter can't be used "
                                 "together with 'min_cores' or 'max-cores' parameters")

        elif min_cores and max_cores:
            if min_cores >= max_cores:
                raise ValueError(
                    "The 'min_cores' parameter can't be larger than 'max_cores' parameter")

        if max_cores and max_cores < 1:
            raise ValueError("The 'max_cores' parameter can't be lower than 1")

        self._cores = cores
        self._min_cores = min_cores
        self._max_cores = max_cores

    def get_requirements(self):
        if self._cores:
            return {
                "resources": {
                    "numCores": {
                        "exact": self._cores
                    }
                }
            }
