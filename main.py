#!/usr/bin/env python3
# -*- coding: utf-8 -*-

######################################################################
# Obolix user management tool
#
# From original work from ClusterVision / Diego Sonaglia
# https://github.com/clustervision/obol
# forked from Hans
# https://github.com/hansthen/obol/, version 1.2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License (included with the sources) for more
# details.
######################################################################

__author__ = "Rémy Dernat"
__copyright__ = ""
__license__ = "GPL"
__version__ = "1.8"
__maintainer__ = "Rémy Dernat"
__email__ = "remy.dernat@umontpellier.fr"
__status__ = "Development"

import argparse
import sys

from utils import logger as l, printing as p
from src import Obol as o

def run():
    """
    Runs the CLI
    """
    # Parser
    parser = argparse.ArgumentParser(prog="obol", description="Manage Cluster Users.")

    # LDAP bind parameters override
    parser.add_argument("--bind-dn", "-D", metavar="BIND_DN", help="LDAP bind DN")
    parser.add_argument(
        "--bind-pass", "-w", metavar="BIND_PASSWORD", help="LDAP bind password"
    )
    parser.add_argument("--host", "-H", metavar="HOST", help="LDAP host")
    parser.add_argument("--base-dn", "-b", metavar="BASE_DN", help="LDAP base DN")
    # Output format
    parser.add_argument(
        "--json",
        "-J",
        action="store_const",
        const="json",
        dest="output_type",
        default="table",
        help="Output in JSON format",
    )

    # Subparsers and subcommands
    subparsers = parser.add_subparsers(help="subcommands", dest="command")
    user_parser = subparsers.add_parser(
        "user",
        help="User subcommands",
    )
    group_parser = subparsers.add_parser("group", help="Group subcommands")
    user_subcommands = user_parser.add_subparsers(dest="subcommand")
    group_subcommands = group_parser.add_subparsers(dest="subcommand")
    _ = subparsers.add_parser("import", help="Import all users and groups")
    _ = subparsers.add_parser("export", help="Export all users and groups")
    # _ = subparsers.add_parser("erase", help="Erase all users and groups")

    # User add command
    user_addsubcommand = user_subcommands.add_parser("add", help="Add a user")
    user_addsubcommand.add_argument("username")
    user_addsubcommand_password_group = user_addsubcommand.add_mutually_exclusive_group()
    user_addsubcommand_password_group.add_argument("--password", "-p")
    user_addsubcommand_password_group.add_argument(
        "--prompt-password", "-P", action="store_true"
    )
    user_addsubcommand_password_group.add_argument(
        "--autogen-password", "--autogen", action="store_true"
    )
    user_addsubcommand.add_argument("--cn", metavar="COMMON NAME")
    user_addsubcommand.add_argument("--sn", metavar="SURNAME")
    user_addsubcommand.add_argument("--givenName", dest="given_name")
    user_addsubcommand.add_argument(
        "--group", "-g", metavar="PRIMARY GROUP", dest="groupname"
    )
    user_addsubcommand.add_argument("--uid", metavar="USER ID")
    user_addsubcommand.add_argument("--gid", metavar="GROUP ID")
    user_addsubcommand.add_argument("--mail", metavar="EMAIL ADDRESS")
    user_addsubcommand.add_argument("--phone", metavar="PHONE NUMBER")
    # changing here
    user_addsubcommand.add_argument("--mail_lists",action="store_true")
    user_addsubcommand.add_argument("--shell")
    user_addsubcommand.add_argument("--skel")
    user_addsubcommand.add_argument(
        "--groups",
        type=lambda s: [i for i in s.split(",") if s ],
        help="A comma separated list of group names",
    )
    user_addsubcommand.add_argument(
        "--expire",
        metavar="DAYS or YYYY-MM-DD",
        help=(
            "Number of days after which the account expires. " "Set to -1 to disable"
        ),
    )
    user_addsubcommand.add_argument("--home", metavar="HOME")

    # User modify command
    user_modifysubcommand = user_subcommands.add_parser(
        "modify", help="Modify a user attribute"
    )
    user_modifysubcommand.add_argument("username")
    user_modifysubcommand_password_group = (
        user_modifysubcommand.add_mutually_exclusive_group()
    )
    user_modifysubcommand_password_group.add_argument("--password", "-p")
    user_modifysubcommand_password_group.add_argument(
        "--prompt-password", "-P", action="store_true"
    )
    user_modifysubcommand_password_group.add_argument(
        "--autogen-password", "--autogen", action="store_true"
    )
    user_modifysubcommand.add_argument("--cn", metavar="COMMON NAME")
    user_modifysubcommand.add_argument("--sn", metavar="SURNAME")
    user_modifysubcommand.add_argument("--givenName", dest="given_name")
    user_modifysubcommand.add_argument(
        "--group", "-g", metavar="PRIMARY GROUP", dest="groupname"
    )
    user_modifysubcommand.add_argument("--uid", metavar="USER ID")
    user_modifysubcommand.add_argument("--gid", metavar="GROUP ID")
    user_modifysubcommand.add_argument("--shell")
    user_modifysubcommand.add_argument("--skel")
    user_modifysubcommand.add_argument("--mail", metavar="EMAIL ADDRESS")
    user_modifysubcommand.add_argument("--phone", metavar="PHONE NUMBER")
        # changing here
    user_modifysubcommand.add_argument("--mail_lists",action="store_true")
    user_modifysubcommand.add_argument(
        "--groups",
        type=lambda s: [i for i in s.split(",") if s ],
        help="A comma separated list of group names",
    )
    user_modifysubcommand.add_argument(
        "--expire",
        metavar="DAYS or YYYY-MM-DD",
        help=(
            "Number of days after which the account expires. " "Set to -1 to disable"
        ),
    )
    user_modifysubcommand.add_argument("--home", metavar="HOME", \
        help="Set the new $HOME env variable and creating the new \
             directory (data need to be copied))")

    # User show command
    user_showsubcommand = user_subcommands.add_parser("show", help="Show user details")
    user_showsubcommand.add_argument("username")

    # User delete command
    user_deletesubcommand = user_subcommands.add_parser("delete", help="Delete a user")
    user_deletesubcommand.add_argument("username")

    # User list command
    _ = user_subcommands.add_parser("list", help="List users")

    # Group add command
    group_addsubcommand = group_subcommands.add_parser("add", help="Add a group")
    group_addsubcommand.add_argument("groupname")
    group_addsubcommand.add_argument("--gid", metavar="GROUP ID")
    group_addsubcommand.add_argument(
        "--users",
        type=lambda s: [i for i in s.split(",") if s ],
        help="A comma separated list of usernames",
    )

    # Group modify command
    group_modifysubcommand = group_subcommands.add_parser("modify", help="Modify a group")
    group_modifysubcommand.add_argument("groupname")
    group_modifysubcommand.add_argument("--gid", metavar="GROUP ID")
    group_modifysubcommand.add_argument(
        "--users",
        type=lambda s: [i for i in s.split(",") if s ],
        help="A comma separated list of usernames",
    )

    # Group rename command
    group_adduserssubcommand = group_subcommands.add_parser(
        "rename", help="Rename group but keep its GID and users"
    )
    group_adduserssubcommand.add_argument("groupname")
    group_adduserssubcommand.add_argument("new_groupname")

    # Group addusers command
    group_adduserssubcommand = group_subcommands.add_parser(
        "addusers", help="Add users to a group"
    )
    group_adduserssubcommand.add_argument("groupname")
    group_adduserssubcommand.add_argument("usernames", nargs="+")

    # Group delusers command
    group_deluserssubcommand = group_subcommands.add_parser(
        "delusers", help="Delete users from a group"
    )
    group_deluserssubcommand.add_argument("groupname")
    group_deluserssubcommand.add_argument("--force", action='store_true',
        help="Delete User from group even if the users does not exist anymore.")
    group_deluserssubcommand.add_argument("usernames", nargs="+")

    # Group show command
    group_showsubcommand = group_subcommands.add_parser("show", help="Show group details")
    group_showsubcommand.add_argument("groupname")

    # Group delete command
    group_deletesubcommands = group_subcommands.add_parser("delete", help="Delete a group")
    group_deletesubcommands.add_argument("--force", action='store_true',
        help="Delete group even if there are still users in it.")
    group_deletesubcommands.add_argument("groupname")

    # Group list command
    _ = group_subcommands.add_parser("list", help="List groups")

    # Run command
    try:
        # log executed command but redact password
        logged_cmd = ""
        password_argument = False

        for arg in sys.argv:
            if password_argument:
                logged_cmd += "<REDACTED> "
            else:
                logged_cmd += f"{arg} "
            password_arguments = ["--password", "-p", "--bind-pass", "-w"]
            password_argument = arg in password_arguments
        l.logger.info(f"Executing command '{logged_cmd}'")

        args = vars(parser.parse_args())
        obol = o("/etc/obol.conf", overrides=args)
        
        method_name = f"{args['command']}_{ args.get('subcommand', '')}"
        function = getattr(obol, method_name, None)
        #changed here
        if args.mail_lists:
            print('Adding to mail lists')
        if function is not None:
            function(**args, warn=True)
            l.logger.info(f"Command '{logged_cmd}' succeeded")
        else:
            if args["command"] == "user":
                user_parser.print_help()
            elif args["command"] == "group":
                group_parser.print_help()
            else:
                parser.print_help()
            sys.exit(1)
    
    except Exception as exc:
        l.logging.error(f"Command '{logged_cmd}' failed: {exc}")
        p.print_error(
            exc,
            name=type(exc).__name__,
        )
        # raise exc
        sys.exit(1)


if __name__ == "__main__":
    run()
