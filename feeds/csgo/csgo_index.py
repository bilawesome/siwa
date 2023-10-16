from feeds.data_feed import DataFeed
from collections import deque

from apis.csgoskins import CSGOSkins


class CSGOIndex(DataFeed):
    NAME = 'csgo_index'
    ID = 9
    HEARTBEAT = 300
    DATAPOINT_DEQUE = deque([], maxlen=100)

    @classmethod
    def process_source_data_into_siwa_datapoint(cls):
        '''
        Process source data into siwa datapoint
        '''
        res = []
        csgo = CSGOSkins()
        df = csgo.get_prices_df()
        df = csgo.agg_data(df)
        caps = csgo.get_caps(df, k=100)
        index = csgo.get_index(df, caps)
        if index == 0:
            return cls.DATAPOINT_DEQUE[-1]  # Should fail if DEQUE is empty
        else:
            res.append(index)
            return index

    @classmethod
    def create_new_data_point(cls):
        return cls.process_source_data_into_siwa_datapoint()
