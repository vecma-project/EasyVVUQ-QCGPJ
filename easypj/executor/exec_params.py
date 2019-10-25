class ExecParams:

    def __init__(self, app, cores=1):
        """
        Parameters for Execution task executed within QCG Pilot Job

        Parameters
        ----------
        app : str
            the full command to run application
        cores : int
            number of cores to use for an exec task
        """
        self._app = app
        self._cores = cores

    @property
    def app(self):
        return self._app

    @property
    def cores(self):
        return self._cores
