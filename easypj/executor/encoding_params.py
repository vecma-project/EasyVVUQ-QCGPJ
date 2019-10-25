class EncodingParams:

    def __init__(self, cores=1):
        """Parameters for Encoding task executed within QCG Pilot Job

        Parameters
        ----------
        cores : int
            number of cores to use for an encoding task
        """

        self._cores = cores

    @property
    def cores(self):
        return self._cores
