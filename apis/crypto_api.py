from typing import Any
from apis import utils
import os
import json

import openai

import constants as c


class CryptoAPI:
    """
    Class to interact with a Crypto API (ex: coingecko, coinmarketcap, etc.)

    Attributes:
        url (str): URL of the API.
        source (str): Source of the data.

    Methods:
        fetch_data_by_mcap(N: int) -> dict:
            Fetch data by market capitalization and stores in a database.
        get_data(N: int):
            Abstract method to get data.
        extract_market_cap(data: Any):
            Abstract method to extract market cap data.
    """

    API_KEYS_FILE = "api_keys.json"

    def __init__(self, url: str, source: str) -> None:
        """
        Constructs all the necessary attributes for the CryptoAPI object.

        Parameters:
            url (str): URL of the API.
            source (str): Source of the data.
        """
        self.url = url
        self.source = source

    def fetch_data_by_mcap(self, N: int) -> dict:
        """
        Fetch data by market capitalization, store it in a database and return
        the data.

        Parameters:
            N (int): Number of cryptocurrencies to fetch.

        Returns:
            dict:
                Dictionary with market cap as keys and other details as values.
        """
        data = self.get_data(N)
        if data is None:
            return None
        else:
            self.validate_api_data(data)
            market_data = self.extract_market_cap(data)

        # Store market data in the database
        utils.create_market_cap_database(c.LOGGING_PATH)
        utils.store_market_cap_data(
            market_data=market_data, source=self.source, db_path=c.LOGGING_PATH
        )
        return market_data

    def get_data(self, N: int) -> Any:
        """
        Abstract method to get data from API.

        Parameters:
            N (int): Number of cryptocurrencies to fetch.

        Raises:
            NotImplementedError:
                If this method is not implemented by a subclass.
        """
        raise NotImplementedError

    def extract_market_cap(self, data: Any) -> dict:
        """
        Abstract method to extract market cap data from API response.

        Parameters:
            data (Any): Data received from API.

        Raises:
            NotImplementedError:
                If this method is not implemented by a subclass.
        """
        raise NotImplementedError

    def get_api_key(self, api_provider_name: str) -> str:
        """
        Retrieves the API key for the specified API provider.

        Parameters:
            api_provider_name (str): Name of the API provider.

        Returns:
            str: API key for the API provider.

        Raises:
            Exception: If the API key for the provider is not found in the
            environment variables.
        """
        api_key = os.environ.get(f"{api_provider_name.upper()}_API_KEY")
        if not api_key:
            raise Exception(
                f"No API key found for {api_provider_name}. "
                "Please set it in your environment variables as "
                f"{api_provider_name.upper()}_API_KEY."
            )
        return api_key

    def validate_api_data(self, data):
        """Validate data returned by external API."""
        try:
            self.validate_api_data_with_chatgpt(data)
        except utils.ChatGPTDataValidationError:
            # If ChatGPT fails validation of data, then validate data using pydantic
            # instead as a backup
            self.validate_api_data_with_pydantic(data)

    def validate_api_data_with_chatgpt(self, data):
        """Validate data returned by external API using ChatGPT.

        Parameters:
            data (obj): Data pulled from an external API.

        Returns:
            None.

        Raises:
            Exception: If the data is classified as garbage by ChatGPT.
        """
        try:
            # Use ChatGPT to validate data
            chat_completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": f"Does this data pulled from external API imply a successful response? answer yes or no only: {data}"[
                            0:500
                        ],
                    }
                ],
            )
            if "no" in chat_completion.choices[0].message.content.lower():
                raise utils.ExternalAPIDataValidationError(
                    f"Market cap data pulled from {self.source} failed ChatGPT validation!"
                )
        except Exception as e:
            raise utils.ChatGPTDataValidationError(
                f"ChatGPT failed validating data pulled from {self.source}. Unexpected error encountered: {e}"
            )

    def validate_api_data_with_pydantic(self, data):
        """Abstract method to validate data pulled from external API using Pydantic.

        Parameters:
            data (Any): Data received from API.

        Raises:
            NotImplementedError:
                If this method is not implemented by a subclass.
        """
        raise NotImplementedError
