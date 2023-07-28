from feeds.data_feed import DataFeed
from collections import deque

from apis.coinmarketcap import CoinMarketCapAPI as coinmarketcap
from apis.coingecko import CoinGeckoAPI as coingecko
from apis.cryptocompare import CryptoCompareAPI as cryptocompare


class MemeCoins(DataFeed):
    NAME = 'memecoins'
    ID = 7
    HEARTBEAT = 180
    DATAPOINT_DEQUE = deque([], maxlen=100)
    COINGECKO = 'coingecko'
    COINMARKETCAP = 'coinmarketcap'
    CRYPTOCOMPARE = 'cryptocompare'
    SOURCES = [COINGECKO, COINMARKETCAP, CRYPTOCOMPARE]
    TOKEN_MAP = {
        'dogecoin': {
            COINGECKO: 'dogecoin',
            COINMARKETCAP: 74,
            CRYPTOCOMPARE: 'DOGE'
        },
        'shiba-inu': {
            COINGECKO: 'shiba-inu',
            COINMARKETCAP: 5994,
            CRYPTOCOMPARE: 'SHIB'
        },
        'pepe': {
            COINGECKO: 'pepe',
            COINMARKETCAP: 24478,
            CRYPTOCOMPARE: 'PEPE'
        },
        'floki': {
            COINGECKO: 'floki',
            COINMARKETCAP: 10804,
            CRYPTOCOMPARE: 'FLOKI'
        }
    }

    @classmethod
    def process_source_data_into_siwa_datapoint(cls):
        '''
        Process source data into siwa datapoint
        '''
        res = []
        sources = [globals().get(obj) for obj in cls.SOURCES]
        for i, source in enumerate(sources):
            ids = []
            for item in cls.TOKEN_MAP:
                ids.append(cls.TOKEN_MAP[item][cls.SOURCES[i]])
            market_data = source().fetch_mcap_by_list(ids)
            if market_data is None:
                continue
            mcaps = sorted(list(market_data.keys()), reverse=True)
            res.append(sum(mcaps))
        if sum(res) == 0:
            return cls.DATAPOINT_DEQUE[-1]  # Should fail if DEQUE is empty
        else:
            # Take average of values from all sources
            return sum(res) / len(res)

    @classmethod
    def create_new_data_point(cls):
        return cls.process_source_data_into_siwa_datapoint()
