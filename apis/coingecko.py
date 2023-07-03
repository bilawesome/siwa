import logging
from pydantic import BaseModel, ValidationError

from datetime import datetime
from typing import List, Optional
from typing import Any, Dict
from apis.crypto_api import CryptoAPI
import requests
from apis import utils

logger = logging.getLogger()


class CoinGeckoData(BaseModel):
    id: str
    symbol: str
    name: str
    image: str
    current_price: float
    market_cap: int
    market_cap_rank: int  # 12
    # fully_diluted_valuation: int  # 6289106594
    # total_volume: int  # 339054287
    # high_24h: float  # 75.5
    # low_24h: float  # 73.01
    # price_change_24h: float  # 1.43
    # price_change_percentage_24h: float
    # market_cap_change_24h: int
    # market_cap_change_percentage_24h: float
    # circulating_supply: float
    # total_supply: int
    # max_supply: int
    # ath: float
    # ath_change_percentage: float
    # ath_date: datetime
    # atl: float
    # atl_change_percentage: float
    # atl_date: datetime
    # roi: Optional[Dict] = None
    last_updated: datetime

    # class Config:
    #     extra = "forbid"


class CoinGeckoAPI(CryptoAPI):
    """
    Class to interact with the CoinGecko API.

    Inherits from:
        CryptoAPI: Parent class to provide a common interface for all crypto APIs.

    Methods:
        get_data(N: int) -> Dict[str, Any]:
            Gets data from CoinGecko API.
        extract_market_cap(data: Dict[str, Any]) -> Dict[float, Dict[str, str]]:
            Extracts market cap data from API response.
    """

    VS_CURRENCY = "usd"
    ORDER = "market_cap_desc"
    PAGE = 1
    SPARKLINE = False  # Don't pull last 7 days of data

    NAME_KEY = "name"
    LAST_UPDATED_KEY = "last_updated"
    MARKET_CAP_KEY = "market_cap"

    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the CoinGeckoAPI object.

        Link to API documentation: https://www.coingecko.com/en/api/documentation
        """
        super().__init__(
            url="https://api.coingecko.com/api/v3/coins/markets", source="coingecko"
        )

    @utils.handle_request_errors
    def get_data(self, N: int) -> Dict[str, Any]:
        """
        Gets data from CoinGecko API.

        Parameters:
            N (int): Number of cryptocurrencies to fetch.

        Returns:
            Dict[str, Any]: A dictionary with data fetched from API.
        """
        parameters = {
            "vs_currency": self.VS_CURRENCY,
            "order": self.ORDER,
            "per_page": N,
            "page": self.PAGE,
            "sparkline": self.SPARKLINE,
        }
        response = requests.get(self.url, params=parameters)
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

        self.validate_api_data(data)

        market_data = {}
        for coin in data:
            name = coin[self.NAME_KEY]
            last_updated = coin[self.LAST_UPDATED_KEY]
            market_cap = coin[self.MARKET_CAP_KEY]
            market_data[market_cap] = {
                "name": name,
                "last_updated": last_updated,
            }
        return market_data

    def validate_api_data(self, data: List[CoinGeckoData]):
        """Validate data returned by external API."""
        for coin in data:
            try:
                CoinGeckoData(**coin)
            except ValidationError as e:
                logger.warning(e)
                continue
