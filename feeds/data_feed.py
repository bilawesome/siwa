# stdlib
import os
import time
import logging
import typing as tp
from threading import Lock
from collections import deque
from datetime import datetime, timezone
from dataclasses import dataclass

# third party
import pandas as pd

# our stuff
import constants as c
import siwa_logging

#'%(asctime)s:%(thread)d - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SQLLogger")
logger.setLevel(logging.INFO)
logger.addHandler(siwa_logging.SQLite_Handler())
logger.propagate = False  # TODO determine if undesirable


@dataclass
class DataFeed:
    """The base-level implementation for all data feeds, which should inherit from DataFeed and implement the get_data_point method as required."""

    # NOTE: all child classes must define these class-level attributes
    CHAIN: str
    NAME: str
    ID: int
    HEARTBEAT: int  # in seconds
    START_TIME: float  # unix timestamp
    DATAPOINT_DEQUE: deque

    # NOTE: the below are default attrs inherited by child classes
    ACTIVE: bool = False
    COUNT: int = 0  # number of data points served since starting
    DATA_KEYS = (c.FEED_NAME, c.TIME_STAMP, c.DATA_POINT)

    @classmethod
    def get_data_dir(cls):
        return c.DATA_PATH / (cls.NAME + c.DATA_EXT)

    @classmethod
    def start(cls):
        """flag feed as active so it can start receiving/processing data"""
        cls.START_TIME = time.time()
        cls.ACTIVE = True

    @classmethod
    def stop(cls):
        """stop / pause feed from receiving/processing data
        for some feeds, this may involve some cleanup, disconnecting a stream etc.
        and would be handled in the overridden stop() method in that specific feed"""
        cls.ACTIVE = False

    @classmethod
    def run(cls):
        """run the data generating function(s)
        for some feeds this may be a loop,
        in others it may be handled by a library e.g. tweepy (twitter) stream
        in that case there would be an overridden run() method in that feed"""

        print("run!!")
        while cls.ACTIVE:
            print("run cls.ACTIVE!!")
            dp = cls.create_new_data_point()
            logger.info(f"\nNext data point for {cls.NAME}: {dp}\n")
            cls.DATAPOINT_DEQUE.append(dp)
            cls.COUNT += 1
            time.sleep(cls.HEARTBEAT)

    @classmethod
    def create_new_data_point(cls):
        """NOTE: this method must be implemented by the child class"""
        raise NotImplementedError

    @classmethod
    def get_most_recently_stored_data_point(cls):
        """pass"""
        print("cls.DATAPOINT_DEQUE", cls.DATAPOINT_DEQUE)
        # data_point = cls.DATAPOINT_DEQUE[-1] if len(cls.DATAPOINT_DEQUE) else None
        data_point = cls.create_new_data_point()
        to_serve = (cls.NAME, time.time(), data_point)
        return dict(zip(cls.DATA_KEYS, to_serve))

    # @staticmethod
    # def format_data(dp):
    #     timenow =  datetime.now(timezone.utc)
    #     strtime = timenow.strftime(c.DATEFORMAT)
    #     return f'{c.LINE_START}{strtime},{dp},\n'
