#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module runs all command line arguments."""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from argparse import ArgumentParser, Action
from logging import DEBUG
from sys import argv

from .assistant import Assistant
from .utils import config_logging


def main():
    """Does all the command line options available
    See top of file for in depth description"""

    parser = ArgumentParser(description="lib_assistant, see github")

    parser.add_argument("--assistant", dest="assistant", default=False, action='store_true')
    parser.add_argument("--demo", dest="demo", default=False, action='store_true')

    parser.add_argument("--debug", dest="debug", default=False, action='store_true')
    parser.add_argument("--test", dest="test", default=False, action='store_true')


    args = parser.parse_args()
    if args.debug:
        config_logging(DEBUG)

    if args.assistant:
        Assistant().run()

    if args.demo:
        if True:
            from multiprocessing import Process
            p = Process(target=run_assistant)
            p.start()
            run_app()
            p.join()
        else:
            from multiprocessing import Process
            p = Process(target=run_app)
            p.start()
            run_assistant()
            p.join()
def run_assistant():
    Assistant().run()

def run_app():
    from .demo import app
    import webbrowser
    webbrowser.open_new('http://127.0.0.1:3000/')
    import logging
    logging.getLogger('werkzeug').disabled=True
    app.run(port=3000)


if __name__ == "__main__":
    main()
