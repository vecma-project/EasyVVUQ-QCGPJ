import os
import json

EQI_STATE_FILE_NAME = '.eqi_state.json'


class StateKeeper:

    EQI_CAMPAIGN_STATE_FILE_NAME = '.eqi_campaign_state.json'

    """ Stores information about EQI execution

    Parameters
    ----------
    directory : string
        the root directory where the information will be stored
    campaign : Campaign
        the EasyVVUQ Campaign object from which the StateKeeper will be inited

    """
    def __init__(self, directory):
        self.directory = directory

    def setup(self, campaign):
        """ Initialises StateKeeper with campaign

        Parameters
        ----------
        campaign : Campaign
            the EasyVVUQ Campaign object from which the StateKeeper will be inited
        """

        _dict = {
            'campaign_db_location': campaign.db_location,
            'campaign_db_type': campaign.db_type,
            'campaign_write_to_db': 'FALSE',
            'campaign_name': campaign.campaign_name,
            'campaign_active_app_name': campaign._active_app_name
        }

        self.write_to_state_file(_dict)

        # Safe state of a campaign to state_file
        campaign.save_state(self.directory + "/" + StateKeeper.EQI_CAMPAIGN_STATE_FILE_NAME)

    def write_to_state_file(self, data):

        eqi_file_loc = f'{self.directory}/{EQI_STATE_FILE_NAME}'

        if os.path.exists(eqi_file_loc):
            with open(eqi_file_loc, 'r') as eqi_file:
                state_dict = json.load(eqi_file)
                state_dict.update(data)
        else:
            state_dict = data

        with open(eqi_file_loc, 'w') as eqi_file:
            json.dump(state_dict, eqi_file)

    def get_from_state_file(self):

        eqi_file_loc = f'{self.directory}/{EQI_STATE_FILE_NAME}'
        if os.path.exists(eqi_file_loc):
            with open(eqi_file_loc, 'r') as eqi_file:
                state_dict = json.load(eqi_file)
        else:
            state_dict = {}

        return state_dict
