import os
import json
import sqlite3
import time
from typing import Any, Dict, Callable, Optional
from requests.exceptions import RequestException
from functools import wraps
import datetime


class MissingDataException(Exception):
    """Raised when the expected data is missing in an API response"""

    pass


class ExternalAPIError(Exception):
    """ExternalAPIError.

    An error indicating that an external API (such as CoinGecko) returns
    an HTTP error response.
    """


class ExternalAPIDataValidationError(Exception):
    """ExternalAPIError.

    An error indicating that an external API (such as CoinGecko) returns
    data that implies an unsuccessful response.
    """

    pass


class ExternalAPIResponseBodyError(Exception):
    """ExternalAPIResponseBodyError.

    An error indicating that an external API (such as CoinGecko) returns
    a response with code 200 but that response does not contain data,
    it contains a message about an issue with the request.
    """


class ExternalAPIExpiredAccessTokenError(Exception):
    """ExternalAPIExpiredAccessTokenError.

    An error that can be raised if an external API (such as CoinMarketCap)
    responds that access token has expired, and needs to be refreshed.
    """


class ExternalAPIRateLimitReachedError(Exception):
    """ExternalAPIRateLimitReachedError.

    An error that can be raised if an external API (such as CoinGecko)
    responds that a rate limit has been reached, and a sleep period may be
    required.
    """


def convert_timestamp_to_unixtime(timestamp):
    """
    Takes a timestamp e.g. '2022-08-11T09:10:12.364Z' and
    returns a unix time 1660209012.364
    """
    unix_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f%z")
    return unix_datetime.timestamp()


def create_market_cap_database(db_path: str = "data.db") -> None:
    """
    Creates a SQLite database (if not exists) to store market cap data.

    Parameters:
        db_path (str, optional): Path to the SQLite database.
        Defaults to 'data.db'.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS "
        "market_cap_data "
        "(name TEXT, market_cap REAL, last_updated_time REAL, "
        "load_time REAL, source TEXT)"
    )
    conn.commit()
    conn.close()


def store_market_cap_data(
    market_data: Dict[float, Dict[str, Any]], source: str, db_path: str = "data.db"
) -> None:
    """
    Stores market cap data into the SQLite database.

    Parameters:
        market_data (Dict[float, Dict[str, Any]]): Market cap data to store.
        source (str): Source of the market cap data.
        db_path (str, optional): Path to the SQLite database. Defaults to 'data.db'.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for market_cap, md in market_data.items():
        cursor.execute(
            "INSERT INTO market_cap_data (name, market_cap, last_updated_time, load_time, source)"
            "VALUES (?, ?, ?, ?, ?)",
            (md["name"], market_cap, md["last_updated"], int(time.time()), source),
        )
    conn.commit()
    conn.close()


def handle_request_errors(func: Callable[..., Any]) -> Callable[..., Optional[Any]]:
    """
    Decorator function to handle request errors.

    Parameters:
        func (Callable[..., Any]): The function to be decorated.

    Returns:
        Callable[..., Optional[Any]]: The decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RequestException as e:
            print("Error occurred while making the API request:", str(e))
            print("Warning: Continuing with the rest of the execution.")
            return None

    return wrapper


def get_api_key(source: str) -> str:
    """
    Gets the API key from the environment variables.

    Parameters:
        source (str): Source of the data.

    Returns:
        str: API key.
    """

    key_name = f"{source.upper()}_API_KEY"
    key = os.environ.get(key_name)
    if key is None:
        raise Exception(f"API key '{key_name}' not found in env vars.")
    return key
