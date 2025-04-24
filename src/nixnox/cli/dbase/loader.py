# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import logging
from datetime import datetime, timedelta
from argparse import ArgumentParser, Namespace

# -------------------
# Third party imports
# -------------------

from lica.sqlalchemy import sqa_logging
from lica.sqlalchemy.dbase import Session
from lica.cli import execute

# --------------
# local imports
# -------------

from ... import __version__
from ..util import parser as prs
from ...lib import ObserverType, Temperature, Humidity, Timestamp, ValidState
from ...lib.dbase.model import Date, Time, Flags, Observer, Location
# ----------------
# Module constants
# ----------------

DESCRIPTION = "NIXNOX Database load ECSV tool"

# -----------------------
# Module global variables
# -----------------------


# get the root logger
log = logging.getLogger(__name__.split(".")[-1])

# -------------------
# Auxiliary functions
# -------------------


# -------------
# CLI Functions
# -------------



def cli_load_obs(session: Session, args: Namespace) -> None:
   pass


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation", parents=[prs.ifiles()], help="Load one or more ECSV observation files"
    )
    p.set_defaults(func=cli_load_obs)
    


def cli_main(args: Namespace) -> None:
    sqa_logging(args)
    with Session() as session:
        with session.begin():
            args.func(session, args)


def main():
    """The main entry point specified by pyproject.toml"""
    execute(
        main_func=cli_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
