# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import logging
import hashlib
from argparse import ArgumentParser, Namespace

from datetime import datetime
from typing import Optional

# -------------------
# Third party imports
# -------------------

import astropy.io.ascii

from lica.sqlalchemy import sqa_logging
from lica.sqlalchemy.dbase import Session
from lica.cli import execute

# --------------
# local imports
# -------------

from ... import __version__
from ..util import parser as prs

from ...lib.table import (
    create_measurements,
    get_measurements,
)

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


def cli_export_ecsv(session: Session, args: Namespace) -> None:
    identifier = " ".join(args.identifier)
    get_measurements(session, identifier)


def cli_import_ecsv(session: Session, args: Namespace) -> None:
    path = " ".join(args.input_file)
    log.info("Loading file %s", path)
    file_obj = open(path, "rb")
    create_measurements(session, file_obj)


def add_import_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation", parents=[prs.ifile()], help="Import to database one ECSV observation file "
    )
    p.set_defaults(func=cli_import_ecsv)


def add_export_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation", parents=[prs.ident()], help="Export one ECSV observation file from database"
    )
    p.set_defaults(func=cli_export_ecsv)


def cli_import(args: Namespace) -> None:
    sqa_logging(args)
    with Session() as session:
        args.func(session, args)


def cli_export(args: Namespace) -> None:
    sqa_logging(args)
    with Session() as session:
        args.func(session, args)


def importa():
    """main entry point specified by pyproject.toml"""
    execute(
        main_func=cli_import,
        add_args_func=add_import_args,
        name=__name__,
        version=__version__,
        description=DESCRIPTION,
    )


def export():
    """main entry point specified by pyproject.toml"""
    execute(
        main_func=cli_export,
        add_args_func=add_export_args,
        name=__name__,
        version=__version__,
        description=DESCRIPTION,
    )
