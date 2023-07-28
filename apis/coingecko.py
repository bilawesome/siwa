import logging
from pydantic import BaseModel, ValidationError
from datetime import datetime
from typing import Any, Dict, List, Optional
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


class CoinGeckoMarketCapData(BaseModel):
    id: str
    symbol: str
    name: str
    image: str
    current_price: float
    market_cap: float
    market_cap_rank: int
    fully_diluted_valuation: Optional[float]
    total_volume: float
    high_24h: float
    low_24h: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap_change_24h: float
    market_cap_change_percentage_24h: float
    circulating_supply: float
    total_supply: Optional[float]
    ath: float
    ath_change_percentage: float
    ath_date: str
    roi: Optional[dict]
    last_updated: str

    class Config:
        allow_population_by_field_name = True


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

    def validate_api_data(self, data: List[CoinGeckoMarketCapData]):
        """Validate data pulled from external API using Pydantic."""
        for coin in data:
            try:
                CoinGeckoMarketCapData(**coin)
            except ValidationError as e:
                raise utils.ExternalAPIDataValidationError(
                    f"Data pulled from {self.source} does not match pre-defined Pydantic data structure: {e}"
                )

    @utils.handle_request_errors
    def get_market_caps_of_list(self, tokens: List[str]) -> Dict[str, float]:
        """
        Gets market cap data for the provided list of tokens from CoinGecko API.

        Parameters:
            tokens (List[str]): List of token names for which to fetch market cap data.

        Returns:
            Dict[str, float]: A dictionary with token names as keys and their market cap as values.
        """
        market_caps = {}

        tokens_comma_sep = ",".join(tokens)

        parameters = {
            "vs_currency": self.VS_CURRENCY,
            "ids": tokens_comma_sep,
        }
        response = requests.get(self.url, params=parameters)
        data = response.json()

        if data:
            for d in data:
                market_cap = d.get(self.MARKET_CAP_KEY)
                name = d.get(self.NAME_KEY)
                last_updated = d.get(self.LAST_UPDATED_KEY)
                market_caps[market_cap] = {
                    "name": name,
                    "last_updated": last_updated,
                }
        return market_caps
