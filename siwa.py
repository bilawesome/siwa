# stdlib
import os
import sys
import logging
import argparse
import threading
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from sentry_sdk import capture_exception, capture_message

# third party
import cmd2

# our stuff
from all_feeds import all_feeds
import constants as c
import endpoint

load_dotenv()

datafeed_threads = {}

endpoint_thread = threading.Thread(
    target=endpoint.run, daemon=True, kwargs={"all_feeds": all_feeds}
)
endpoint_thread.start()


def get_params():
    """
    Get parameters from command line
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--datafeeds",
        nargs="+",
        default=[],
        help="List of datafeeds to start, separated by commas. Call like this: python siwa.py --datafeeds feed1 feed2 feed3",
    )

    args = parser.parse_args()
    datafeeds = [all_feeds[f] for f in args.datafeeds]
    return datafeeds


def start_feeds(feeds):
    """start all feeds in feeds list"""
    for feed in feeds:
        # (re)activate feed / allow it to start or resume processing
        feed.start()

        # print datafeed startup message to CLI
        print(c.start_message(feed))

        # create new thread *only if* one doesn't already exist
        if not feed.NAME in datafeed_threads:
            thread = threading.Thread(target=feed.run)
            thread.start()
            datafeed_threads[feed.NAME] = thread


def stop_feeds(feeds):
    """stop *and kill thread for* all feeds in a list"""
    for feed in feeds:
        feed.stop()
        datafeed_threads[feed.NAME].join()
        del datafeed_threads[feed.NAME]


class Siwa(cmd2.Cmd):
    """siwa CLI: allows user to start/stop datafeeds, list feed statuses"""

    prompt = "\nSIWA> "

    def __init__(self):
        super().__init__()
        # Make maxrepeats settable at runtime
        self.maxrepeats = 1
        self.init_time = time.time()
        self.debug = c.DEBUG
        if self.debug:
            self.poutput(":::DEBUG MODE ENABLED:::")

    def do_status(self, args: cmd2.Statement):
        """show status (active, inactive) for all datafeeds,
        if debug enabled, also show status of threads;
        inactive datafeeds merely sleep, they do not close their threads"""
        # if -v then shows params too

        self.poutput(c.init_time_message(self))

        for feed in all_feeds.values():
            self.poutput(c.status_message(feed))
            self.poutput(f"{feed.NAME} deque len: {len(feed.DATAPOINT_DEQUE)}")

        if c.DEBUG:
            threadcount = threading.active_count()
            datafeed_threadcount = (
                threading.active_count() - 1 - 1 - c.WEBSERVER_THREADS
            )
            endpoint_threadcount = 1 + c.WEBSERVER_THREADS
            self.poutput(
                f"""
                --- THREAD DEBUG INFO ---
                datafeed threads running: {datafeed_threadcount}
                total threads: {threadcount} (1 main, {endpoint_threadcount} endpoint, and {datafeed_threadcount} feeds)
                feeds threads running: {list(datafeed_threads.keys()) or '[none]'}"""
            )

    def do_start(self, args: cmd2.Statement):
        """start specified feed, if none specified start all;
        create new thread for feed if none extant"""
        if args:
            # start specific feed, if given
            feeds = [all_feeds[f] for f in args.arg_list]
        else:
            # else start all feeds
            feeds = all_feeds.values()

        start_feeds(feeds)

    def do_stop(self, args: cmd2.Statement):
        """stop datafeed processing
        (thread remains running in case we want to re-activate)"""
        if args:
            # stop specific feed, if given
            feeds = [all_feeds[f] for f in args.arg_list]
        else:
            # else stop all active feeds
            feeds = [f for f in all_feeds.values() if f.ACTIVE]
        for feed in feeds:
            self.poutput(c.stop_message(feed))
            stop_feeds([feed])

    def do_quit(self, args: cmd2.Statement):
        """Exit the application"""
        self.poutput("quitting; waiting for heartbeat timeout")
        for feed in all_feeds.values():
            feed.stop()
        return True


if __name__ == "__main__":
    args = get_params()
    if args:
        start_feeds(args)
    else:
        sys.exit(Siwa().cmdloop())
