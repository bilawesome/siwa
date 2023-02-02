#!/usr/bin/env python3
"""guideline

Usage:
siwa.py start <feed> [<print>]
siwa.py stop <feed>
siwa.py feeds
siwa.py display [<task>] [-d <date>]
siwa.py view <task>
siwa.py network

Options:
-p, --print                 Print a feeds data and activity
-h, --help                  Show this screen
"""

#TODO:

import os
import logging
import threading
from docopt import docopt
from all_feeds import all_feeds


if __name__ == '__main__':
    kwargs = docopt(__doc__, version='siwa 0.1')
    # print(kwargs)

    #Display all enabled feeds with args
    if kwargs['feeds']:
        ...

    if kwargs['start']:
        feed_name = kwargs['<feed>']
        Feed = all_feeds[feed_name]
        printdata = kwargs.get('<print>', False)

        thread = threading.Thread(
                target=Feed.run,
                kwargs={'printdata':printdata}
                )

        thread.start()

        Feed.active = True
        print(Feed.active)
        print(all_feeds[feed_name].active)

