# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import os
import glob
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
    uploader,
    database_import,
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


def cli_dbexport_single(session: Session, args: Namespace) -> None:
    identifier = " ".join(args.identifier)
    os.makedirs(args.folder, exist_ok=True)
    database_export(session, args.folder, identifier)
    

def cli_dbexport_all(session: Session, args: Namespace) -> None:
    os.makedirs(args.folder, exist_ok=True)
    database_export(session, args.folder, identifier=None)


def cli_dbimport_single(session: Session, args: Namespace) -> None:
    path = " ".join(args.input_file)
    log.info("Loading file %s", path)
    with open(path, "rb") as file_obj:
        database_import(session, file_obj)

def cli_dbimport_all(session: Session, args: Namespace) -> None:
    for path in glob.iglob("*.ecsv", root_dir=args.folder):
        path = os.path.join(args.folder, path)
        log.info("Loading file %s", path)
        with open(path, "rb") as file_obj:
            database_import(session, file_obj)


def cli_obsload_ecsv(session: Session, args: Namespace) -> None:
    path = " ".join(args.input_file)
    log.info("Loading file %s", path)
    with open(path, "rb") as file_obj:
        uploader(session, file_obj, extra_path=args.text)


def add_dbimport_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation", parents=[prs.ifile()], help="Import single database ECSV file"
    )
    p.set_defaults(func=cli_dbimport_single)
    p = subparser.add_parser(
        "all", parents=[prs.folder()], help="Export all database observations as ECSV files"
    )
    p.set_defaults(func=cli_dbimport_all)


def add_dbexport_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation", parents=[prs.ident(), prs.folder()], help="Export single database ECSV file"
    )
    p.set_defaults(func=cli_dbexport_single)
    p = subparser.add_parser(
        "all", parents=[prs.folder()], help="Export all database observations as ECSV files"
    )
    p.set_defaults(func=cli_dbexport_all)


def add_obsload_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation",
        parents=[prs.ifile(), prs.text()],
        help="Load a single TAS/SQL observation file",
    )
    p.set_defaults(func=cli_obsload_ecsv)


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
