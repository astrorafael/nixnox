# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import logging
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

from ...lib.ecsv import (
    loader,
    loader_v2,
    database_export,
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


def cli_dbexport_ecsv(session: Session, args: Namespace) -> None:
    identifier = " ".join(args.identifier)
    folder = args.dir
    table = database_export(session, identifier)
    if table:
        path = identifier + ".ecsv"
        table.write(path, delimiter=args.delimiter, format="ascii.ecsv", overwrite=True)


def cli_dbimport_ecsv(session: Session, args: Namespace) -> None:
    path = " ".join(args.input_file)
    log.info("Loading file %s", path)
    with open(path, "rb") as file_obj:
        loader_v2(session, file_obj)


def cli_obsimport_ecsv(session: Session, args: Namespace) -> None:
    path = " ".join(args.input_file)
    log.info("Loading file %s", path)
    with open(path, "rb") as file_obj:
        loader(session, file_obj)


def add_dbimport_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation", parents=[prs.ifile()], help="Import single database ECSV file"
    )
    p.set_defaults(func=cli_dbimport_ecsv)


def add_dbexport_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation", parents=[prs.ident(), prs.folder()], help="Export single database ECSV file"
    )
    p.set_defaults(func=cli_dbexport_ecsv)


def add_obsload_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation",
        parents=[prs.ident(), prs.text()],
        help="Load a single TAS/SQL observation file",
    )
    p.set_defaults(func=cli_obsimport_ecsv)


def cli_main(args: Namespace) -> None:
    sqa_logging(args)
    with Session() as session:
        args.func(session, args)


def dbimport():
    """main entry point specified by pyproject.toml"""
    execute(
        main_func=cli_main,
        add_args_func=add_dbimport_args,
        name=__name__,
        version=__version__,
        description="Database import",
    )


def dbexport():
    """main entry point specified by pyproject.toml"""
    execute(
        main_func=cli_main,
        add_args_func=add_dbexport_args,
        name=__name__,
        version=__version__,
        description="Database export",
    )


def obsload():
    """main entry point specified by pyproject.toml"""
    execute(
        main_func=cli_main,
        add_args_func=add_obsload_args,
        name=__name__,
        version=__version__,
        description="Load TAS/SQM observation file",
    )
