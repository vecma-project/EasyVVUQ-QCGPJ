from typing import Union


class Resources:
    """
    Stores typical for QCG Pilot Job resource requirements

    Parameters
    ----------
    exact: Number
        The exact number of resources
    min: Number
        The minimal acceptable number of resources
    max: Number
        The maximal acceptable number of resources
    split_into: Number
        The anticipated number of chunks to which the total resources should be split.
        The minimal number of resources in a chunk will be restricted by the value of 'min'.
    """
    def __init__(self, exact=None, min=None, max=None, split_into=None):
        # Establish settings for resources
        if not exact and not min and not max:
            exact = 1

        elif exact:
            if exact < 1:
                raise ValueError("The value of 'exact' parameter can't be lower than 1")
            if min or max:
                raise ValueError("The value of 'exact' parameter can't be used "
                                 "together with 'min' or 'max'")
        elif min:
            if not max and not split_into:
                raise ValueError("The value of 'min' parameter "
                                 "can't be used without 'max' or 'split_into")
            if max and min > max:
                raise ValueError(
                    "The value of 'min' parameter can't be larger "
                    "than the value of 'max' parameter")
            if split_into and split_into > min:
                raise ValueError("The value of 'split_nto' parameter "
                                 "can't be larger than 'min'")

        elif max:
            raise ValueError("The value of 'max' parameter "
                             "can't be used without 'min'")

        elif split_into:
            raise ValueError("The value of 'split_into' parameter "
                             "can't be used without 'min'")

        self._exact = exact
        self._min = min
        self._max = max
        self._split_into = split_into

    def get_dict(self):
        """

        Returns
        -------
        Dict:
            Dictionary of resource requirements.
        """
        _resources = {
        }

        if self._exact:
            _resources.update({
                "exact": self._exact
            })

        if self._min:
            _resources.update({
                "min": self._min
            })

        if self._max:
            _resources.update({
                "max": self._max
            })

        if self._split_into:
            _resources.update({
                "split-into": self._split_into
            })

        return _resources


class TaskRequirements:
    """
    Requirements for a task executed within QCG Pilot Job

    Parameters
    ----------
    cores : int or eqi.Resources
        the resource requirements for cores
    nodes : int or eqi.Resources
        the resource requirements for nodes
    """

    def __init__(self, cores: Union[int, Resources, None] = None,
                 nodes: Union[int, Resources, None] = None):

        if not cores and not nodes:
            raise ValueError("At least one of 'cores' or 'nodes' parameters should be specified")

        if isinstance(cores, int):
            cores = Resources(exact=cores)

        if isinstance(nodes, int):
            nodes = Resources(exact=nodes)

        self._resources = {
            "resources": {}
        }

        if cores:
            self._resources["resources"].update({"numCores": {}})
            cores_dict = cores.get_dict()
            self._resources["resources"]["numCores"].update(cores_dict)

        if nodes:
            self._resources["resources"].update({"numNodes": {}})
            nodes_dict = nodes.get_dict()
            self._resources["resources"]["numNodes"].update(nodes_dict)

    def get_resources(self):
        """
        Allows to get resource requirements in a form of dictionary understandable
        by QCG Pilot Job Manager

        Returns
        -------
            dict : dictionary with the resource requirements specification

        """
        return self._resources
