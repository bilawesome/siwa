from typing import Any, Dict, List, Optional
from apis.crypto_api import CryptoAPI
import requests
import json

from pydantic import BaseModel, ValidationError

from apis import utils
import time


class CoinMarketCapMarketCapData(BaseModel):
    id: int
    name: str
    symbol: str
    slug: str
    num_market_pairs: int
    date_added: str
    tags: list[str]
    max_supply: Optional[float]
    circulating_supply: float
    total_supply: float
    platform: Optional[dict]
    cmc_rank: int
    last_updated: str
    quote: dict

    # class Config:
    #     allow_population_by_field_name = True


class CoinMarketCapAPI(CryptoAPI):
    """
    Class to interact with the CoinMarketCap API.

    Inherits from:
        CryptoAPI: Parent class to provide a common interface for all crypto APIs.

    Methods:
        get_data(N: int) -> Dict[str, Any]:
            Gets data from CoinMarketCap API.
        extract_market_cap(data: Dict[str, Any]) -> Dict[float, Dict[str, str]]:
            Extracts market cap data from API response.
    """

    LIMIT = "limit"
    DATA = "data"
    ID = "id"
    NAME = "name"
    LAST_UPDATED = "last_updated"
    QUOTE = "quote"
    USD = "USD"
    MARKET_CAP = "market_cap"
    CMC_PRO_API_KEY = "X-CMC_PRO_API_KEY"

    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the CoinMarketCapAPI object.
        """
        source = "coinmarketcap"
        super().__init__(
            url="https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
            source=source,
        )
        self.headers = {
            self.CMC_PRO_API_KEY: self.get_api_key(source),
        }

    @utils.handle_request_errors
    def get_data(self, N: int) -> Dict[str, Any]:
        """
        Gets data from CoinMarketCap API.

        Parameters:
            N (int): Number of cryptocurrencies to fetch.

        Returns:
            Dict[str, Any]: A dictionary with data fetched from API.
        """
        parameters = {self.LIMIT: N}
        response = requests.get(self.url, headers=self.headers, params=parameters)
        data = response.json()
        return data

    def extract_market_cap(self, data: Dict[str, Any]) -> Dict[float, Dict[str, str]]:
        """
        Extracts market cap data from API response.

        Parameters:
            data (Dict[str, Any]): Data received from API.

        Returns:
            Dict[float, Dict[str, str]]:
                A dictionary with market cap as keys and coin details as values.
        """
        market_data = {}
        for coin in data[self.DATA]:
            name = coin[self.NAME]
            last_updated = coin[self.LAST_UPDATED]
            market_cap = coin[self.QUOTE][self.USD][self.MARKET_CAP]
            market_data[market_cap] = {
                "name": name,
                "last_updated": last_updated,
            }
        return market_data

    def validate_api_data(self, data: List[CoinMarketCapMarketCapData]):
        """Validate data pulled from external API using Pydantic."""
        for coin in data[self.DATA]:
            print("coinmarketcap coind data", json.dumps(coin))
            try:
                CoinMarketCapMarketCapData(**coin)
            except ValidationError as e:
                raise utils.ExternalAPIDataValidationError(
                    f"Data pulled from {self.source} does not match pre-defined Pydantic data structure: {e}"
                )

    @utils.handle_request_errors
    def get_market_cap_of_token(self, id: int) -> Dict[str, float]:
        """
        Gets market cap data for the provided token id from CoinMarketCap API.

        Parameters:
            id (int): Token id for which to fetch market cap data.

        Returns:
            Dict[str, float]: A dictionary with market cap as keys and other metadata as values.
        """
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        parameters = {self.ID: id}
        response = requests.get(url, headers=self.headers, params=parameters)
        data = response.json()

        market_cap_data = {}
        if self.DATA in data:
            token_data = data[self.DATA][str(id)]
            name = token_data[self.NAME]
            last_updated = token_data[self.LAST_UPDATED]
            market_cap = token_data[self.QUOTE][self.USD][self.MARKET_CAP]
            market_cap_data = {
                "name": name,
                "market_cap": market_cap,
                "last_updated": last_updated,
            }
        return market_cap_data

    def get_market_caps_of_list(self, ids: List[int]) -> Dict[str, Dict[str, Any]]:
        """
        Gets market cap data for the provided list of token ids from CoinMarketCap API.

        Parameters:
            tokens (List[int]): List of token ids for which to fetch market cap data.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary with token names as keys and their respective market cap data as values.
        """
        market_caps = {}
        for id in ids:
            mcap_data = self.get_market_cap_of_token(id)
            if mcap_data:
                market_caps[mcap_data["market_cap"]] = {
                    "name": mcap_data["name"],
                    "last_updated": mcap_data["last_updated"],
                }
            time.sleep(0.2)  # To prevent hitting API rate limits

        return market_caps
