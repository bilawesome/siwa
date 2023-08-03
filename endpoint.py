""" module documentation:
this is the HTTP server endpoint
returns datapoints as json
handles errors and returns json also
in c.DEBUG mode, will show traceback
"""

# stdlib
import logging
import traceback, sqlite3

# third party
import flask
from flask import Response
import time

from waitress import serve
from werkzeug.exceptions import HTTPException, NotFound

# our stuff
import constants as c
from apis import utils

_INF = float("inf")

app = flask.Flask(__name__)
logger = logging.getLogger("SQLLogger")


@app.route("/")
def blank():
    return "this is a siwa endpoint"


@app.route("/datafeed/<feedname>")
def json_route(feedname):
    """return (over http) latest datapoint as JSON"""
    print("app.all_feeds ", app.all_feeds)
    if feedname in app.all_feeds:
        feed = app.all_feeds[feedname]

        data_point = {}
        try:
            data_point = feed.get_most_recently_stored_data_point()
        except utils.ExternalAPIDataValidationError as e:
            logger.error(e)

        print("data_point ", data_point)
        if not data_point["data_point"]:
            # note, use data_point['data_point'] instead of just data_point
            # to ensure we return a NotFound if data_point['data_point'] not yet populated
            # note: this means deque empty
            raise NotFound(description="new feed / no data yet")
    else:
        raise NotFound(description="unknown feed name")

    return flask.jsonify(data_point)


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    """handle errors; return JSON so result still
    parseable by whatever connects to siwa"""

    error_dict = {
        "error": f"http {error.code}",
        "code": error.code,
        "description": error.description,
    }

    if c.DEBUG:
        # don't show in non-debug mode?
        # bad idea to show traceback to everyone?
        error_dict["stack_trace"] = traceback.format_exc()

    response = flask.jsonify(error_dict)
    response.status_code = error.code

    # TODO
    # log http errors / re-use SQLite_Handler
    # log_msg = f"HTTPException {error_dict.code}, Description: {error_dict.description}, Stack trace: {error_dict.stack_trace}"
    # logger.log(msg=log_msg)

    return response


@app.route("/logs")
def sqlite_logs_route():
    """return last 10 log entries as json"""
    # NOTE: we could easily change this to say "after ___",
    # e.g. so any tool could fetch all new-to-them logs after a given timestamp

    def dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    conn = sqlite3.connect(c.LOGGING_PATH)
    conn.row_factory = dict_factory
    rows = conn.execute("SELECT * FROM log ORDER BY created DESC LIMIT 10")
    result = rows.fetchall()
    conn.close()
    return flask.jsonify(result)


@app.route("/debug")
def trigger_error():
    logger.info("Debug endpoint called!")
    division_by_zero = 1 / 0


def run(*args, **kwargs):
    """run the webserver"""
    # TODO confirm below feeds reference acceptable w/r/t multithreading?
    # we never write from flask, only read, is that relevant?
    app.all_feeds = kwargs["all_feeds"]
    serve(app, host="0.0.0.0", port=16556, threads=c.WEBSERVER_THREADS)
