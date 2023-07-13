from typing import Any, Dict
from apis.crypto_api import CryptoAPI
import requests
from apis import utils


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

    def validate_api_data_with_pydantic(self, data):
        """Validate data pulled from external API using Pydantic."""
        # TODO: Add pydantic validation here
        pass
