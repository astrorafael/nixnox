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
    TableBuilder,
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
    builder = TableBuilder(session)
    table = builder.build(identifier)
    if table:
        path = "EXPORTED_" + identifier + '.ecsv'
        table.write(path, delimiter=args.delimiter, format="ascii.ecsv", overwrite=True)


def cli_import_ecsv(session: Session, args: Namespace) -> None:
    path = " ".join(args.input_file)
    log.info("Loading file %s", path)
    with open(path, "rb") as file_obj:
        if args.new:
            loader_v2(session, file_obj)
        else:
            loader(session, file_obj)


def add_import_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation", parents=[prs.ifile(), prs.new()], help="Import to database one ECSV observation file "
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
