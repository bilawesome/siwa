import pandas as pd
import numpy as np
import requests
try:
    from apis.utils import get_api_key
except ModuleNotFoundError:
    from utils import get_api_key
from pydantic import BaseModel, ValidationError
from typing import Dict, List, Optional
from web3 import Web3
import json

import prometheus_metrics


class CSGOSkinsPrice(BaseModel):
    market: str
    price: int
    quantity: int
    updated_at: Optional[int]


class CSGOSkinsPrices(BaseModel):
    market_hash_name: str
    prices: List[CSGOSkinsPrice]


class CSGOSkinsPriceHistoryDate(BaseModel):
    date: str
    prices: List[CSGOSkinsPrice]


class CSGOSkinsPriceHistory(BaseModel):
    market_hash_name: str
    dates: List[CSGOSkinsPriceHistoryDate]


class CSGOSkinsPriceHistories(BaseModel):
    meta: Dict
    data: List[CSGOSkinsPriceHistory]


class CSGOSkins:
    """
    A class to interact with the CSGOSkins API to fetch and process skin
    prices.

    Attributes:
    ----------
    prices_endpoint : str
        The API endpoint for fetching current prices of CSGO skins.
    base_url : str
        The base URL for the CSGOSkins API.
    api_key : str
        The API key to authenticate with the CSGOSkins API.
    """
    API_PREFIX = 'CSGO'
    PRICES_ENDPOINT = 'api/v1/prices'
    PRICE_HISTORIES_ENDPOINT = 'api/v1/price-histories'
    PRICE_HISTORIES_RPM = 20
    DEFAULT_BASE_URL = 'https://csgoskins.gg/'
    MAPPING_PATH = 'apis/csgo/csgo_mapping.csv'
    DEFAULT_RANGE = 'current'
    DEFAULT_AGG = 'max'
    AUTH_TYPE = 'Bearer'
    CONTENT_TYPE = 'application/json'
    RANGE_KEY = "range"
    AGGREGATOR_KEY = "aggregator"
    DATA_KEY = 'data'
    PRICES_KEY = 'prices'
    PRICE_KEY = 'price'
    QUANTITY_KEY = 'quantity'
    QUANTITY_MAP_KEY = 'mapped_quantity'
    MARKET_HASH_NAME_KEY = 'market_hash_name'
    AUTHORIZATION_KEY = 'Authorization'
    CONTENT_TYPE_KEY = 'Content-Type'
    GOERLI_URL = 'https://goerli.infura.io/v3/'
    INFURA_PREFIX = 'INFURA'
    CONTRACT_ADD_FILE = 'apis/csgo/contract_address.txt'
    ABI_FILE = 'apis/csgo/abi.json'

    def __init__(self, base_url=DEFAULT_BASE_URL):
        """
        Initializes the CSGOSkins class with the base URL and API key.

        Parameters:
        ----------
        base_url : str, optional
            The base URL for the CSGOSkins API.
        api_key : str
            The API key to authenticate with the CSGOSkins API.
        """
        self.base_url = base_url
        self.api_key = get_api_key(self.API_PREFIX)
        self.infura_key = get_api_key(self.INFURA_PREFIX)
        self.headers = {
            self.AUTHORIZATION_KEY: f"{self.AUTH_TYPE} {self.api_key}",
            self.CONTENT_TYPE_KEY: self.CONTENT_TYPE
        }
        # Init web3
        self.w3 = Web3(Web3.HTTPProvider(self.GOERLI_URL + self.infura_key))

    def validate_api_data(self, model: BaseModel, data):
        """Validate data pulled from external API using Pydantic."""
        try:
            for item in data:
                model(**item)
        except ValidationError as e:
            raise Exception(
                f"Data pulled from {self.base_url} does not match "
                f"pre-defined Pydantic data structure: {e}"
            )

    def get_prices(self, range=DEFAULT_RANGE, agg=DEFAULT_AGG):
        """
        Fetches the current prices of CSGO skins from the API.

        Parameters:
        ----------
        range : str, optional
            The range of prices to fetch. Default is 'current'.
        agg : str, optional
            The aggregation method to use. Default is 'max'. As per API docs,
            this is ignored if `range` is set to "current".

        Returns:
        -------
        dict
            A dictionary containing the fetched data from the API.
        """
        url = self.base_url + self.PRICES_ENDPOINT
        payload = {
            self.RANGE_KEY: range,
            self.AGGREGATOR_KEY: agg
        }
        response = requests.request('GET', url,
                                    headers=self.headers, json=payload)
        data = response.json()
        self.validate_api_data(CSGOSkinsPrices, data["data"])
        return data

    def get_prices_df(self, range=DEFAULT_RANGE, agg=DEFAULT_AGG):
        """
        Fetches the prices of CSGO skins and returns them as a pandas
        DataFrame.

        Parameters:
        ----------
        range : str, optional
            The range of prices to fetch. Default is 'current'. As per API
            docs, this is ignored if `range` is set to "current".
        agg : str, optional
            The aggregation method to use. Default is 'max'.

        Returns:
        -------
        pd.DataFrame
            A DataFrame containing the fetched data from the API.
        """
        data = self.get_prices()
        df = pd.json_normalize(
            data[self.DATA_KEY],
            record_path=self.PRICES_KEY,
            meta=self.MARKET_HASH_NAME_KEY
        )
        df[self.PRICE_KEY] = df[self.PRICE_KEY]/100
        return df

    def agg_data(self, df):
        """
        Aggregates the data of a given DataFrame by 'market_hash_name',
        computing the minimum price and total quantity for each group.

        Parameters:
        ----------
        df : pd.DataFrame
            The input DataFrame containing the data to aggregate.

        Returns:
        -------
        pd.DataFrame
            A DataFrame containing the aggregated data.
        """
        df = df.groupby(self.MARKET_HASH_NAME_KEY)[self.PRICE_KEY, self.QUANTITY_KEY]\
            .agg(price=pd.NamedAgg(column=self.PRICE_KEY, aggfunc='min'),
                 quantity=pd.NamedAgg(column=self.QUANTITY_KEY, aggfunc='sum'))\
            .reset_index()
        for row in df.to_dict('records'):
            prometheus_metrics.csgo_price_gauge.labels(
                market_hash_name=row['market_hash_name']).set(row['price'])
        return df

    def get_caps(self,
                 mapping: pd.DataFrame,
                 k: float = None,
                 upper_multiplier: float = None,
                 lower_multiplier: float = None):
        """
        Derives the caps for each skin in the mapping.

        Parameters:
        ----------
        mapping : pd.DataFrame
            The input DataFrame containing skins and their avg and std dev of
            index share.
        upper_multiplier : float
            The multiplier to use for the upper cap.
        lower_multiplier : float
            The multiplier to use for the lower cap.

        Returns:
        -------
        pd.DataFrame
            Input dataframe with caps added.
        """
        # Get caps for each skin
        mapping = pd.read_csv(self.MAPPING_PATH, index_col=0)
        mapping = mapping.rename(columns={self.QUANTITY_KEY: self.QUANTITY_MAP_KEY})
        if (k is None) and (upper_multiplier is None and lower_multiplier is None):
            raise ValueError('Must specify either k or upper/lower multipliers')
        if (k is not None) and (upper_multiplier is not None or lower_multiplier is not None):
            raise ValueError('Cannot specify both k and upper/lower multipliers')
        if (upper_multiplier is not None and lower_multiplier is None):
            mapping['upper_cap_index_share'] = (
                mapping['avg_index_share']
                + upper_multiplier * mapping['std_index_share']
            )
            mapping['lower_cap_index_share'] = np.where(
                mapping['avg_index_share'] - lower_multiplier * mapping['std_index_share'] > 0,
                mapping['avg_index_share'] - lower_multiplier * mapping['std_index_share'],
                0
            )
        elif k is not None:
            mapping['multiplier'] = np.exp(-k*mapping['avg_index_share'])
            mapping['upper_cap_index_share'] = mapping['avg_index_share'] + mapping['multiplier']*mapping['std_index_share']
            mapping['lower_cap_index_share'] = mapping['avg_index_share'] - mapping['multiplier']*mapping['std_index_share']
            mapping['lower_cap_index_share'] = np.where(mapping['lower_cap_index_share'] < 0, 0, mapping['lower_cap_index_share'])
        return mapping

    def adjust_share(self, df, max_iter):
        # Initialize
        df['mean_cap_index_share'] = (df['lower_cap_index_share'] + df['upper_cap_index_share']) / 2
        elements = df.iloc[:, 0].tolist()
        min_percentages = df.loc[:, 'lower_cap_index_share'].tolist()
        max_percentages = df.loc[:, 'upper_cap_index_share'].tolist()
        mean_percentages = df.loc[:, 'mean_cap_index_share'].tolist()
        max_iterations = max_iter  # setting a limit to prevent infinite loops
        iterations = 0

        while iterations < max_iterations:
            # Calculate total sum
            sum_elements = sum(elements)
            # Calculate deviations
            deviations = []
            for i, num in enumerate(elements):
                current_percentage = num / sum_elements
                if current_percentage < min_percentages[i]:
                    deviation = current_percentage - min_percentages[i]
                elif current_percentage > max_percentages[i]:
                    deviation = current_percentage - max_percentages[i]
                else:
                    deviation = 0
                deviations.append(deviation)

            # Check if all deviations are zero (all elements within their acceptable ranges)
            if all(d == 0 for d in deviations):
                break

            # Sort by deviation
            sorted_indices = sorted(range(len(deviations)), key=lambda k: abs(deviations[k]), reverse=True)

            # Adjust the Most Deviating Element
            most_deviating_index = sorted_indices[0]
            if deviations[most_deviating_index] < 0:
                # Below the acceptable range
                target_value = min_percentages[most_deviating_index] * sum_elements
            else:
                # Above the acceptable range
                target_value = max_percentages[most_deviating_index] * sum_elements

            # Update the value in elements list
            elements[most_deviating_index] = target_value

            iterations += 1

        # Update the DataFrame
        df.iloc[:, 0] = elements

        return df

    def cap_compared_to_prev(self, index):
        '''
        Caps the index to be within 5% of the previous index.
        Parameters:
        ----------
        index : float
            The current index.
        Returns:
        -------
        float
            The capped index.
        '''
        # Read answer from chainlink contract using web3py
        # Get contract address from file
        with open(self.CONTRACT_ADD_FILE) as f:
            contract_address = f.read()
        # Read contract abi from file
        with open(self.ABI_FILE) as f:
            abi = json.load(f)
        # Init contract
        contract = self.w3.eth.contract(address=contract_address, abi=abi)
        # Get answer
        prev_index = contract.functions.latestAnswer().call()
        decimals = contract.functions.decimals().call()
        prev_index = prev_index / 10**decimals
        # If prev_index more/less by 5% of index, cap current index at 5% move
        if index < prev_index * 0.95:
            index = prev_index * 0.95
        elif index > prev_index * 1.05:
            index = prev_index * 1.05
        return index

    def get_index(self, df, caps):
        # Get caps
        df = df.merge(caps, on=self.MARKET_HASH_NAME_KEY, how='inner')
        df['index'] = df[self.PRICE_KEY] * df[self.QUANTITY_MAP_KEY]
        adjusted_df = self.adjust_share(
            df[['index', 'lower_cap_index_share', 'upper_cap_index_share']],
            max_iter=1000
        )
        index = adjusted_df['index'].sum()
        # index = self.cap_compared_to_prev(index)

        # Set prometheus metric to index
        print(f'Set prometheus metric to index {index}')
        prometheus_metrics.csgo_index_gauge.set(index)
        return index


if __name__ == '__main__':
    csgo = CSGOSkins()
    data = csgo.get_prices()
    df = csgo.get_prices_df()
    df = csgo.agg_data(df)
    caps = csgo.get_caps(df, k=100)
    index = csgo.get_index(df, caps)
    print('index: ', index)
