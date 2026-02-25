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

import sys
from typing import List, Dict, Union

from utils import misc as m



def print_table(item: Union[List, Dict]):
    """Print a list of dicts as a table, dict as a transposed table"""
    list_fields = ["uid", "cn", "uidNumber", "gidNumber", "member", "memberOf"]

    if isinstance(item, list):
        if len(item) == 0:
            print("No results")
            return
        keys = [ k for k in item[0].keys() if k in list_fields]
        widths = [len(key) for key in keys]

        for row in item:
            for i, key in enumerate(keys):
                widths[i] = max(widths[i], len(str(row.get(key, ""))))

        print(" | ".join([key.ljust(widths[i]) for i, key in enumerate(keys)]))
        print("-+-".join(["-" * widths[i] for i, key in enumerate(keys)]))
        for row in item:
            keys_last_index = len(keys)-1
            content = []
            for i, key in enumerate(keys):
                if i == keys_last_index:
                    content.append(str(row.get(key, "")).ljust(widths[i]).rstrip())
                else:
                    content.append(str(row.get(key, "")).ljust(widths[i]))
            print(" | ".join(content))

    elif isinstance(item, dict):
        keys = item.keys()
        widths = [len(key) for key in keys]

        max_width = max(widths)
        for key in keys:
            if key in ("shadowExpire", "shadowLastChange") and item[key] != "-1":
                human_dateval = m.calc_calendar(item[key])
                print(key.ljust(max_width), "|", human_dateval)
            else:
                print(key.ljust(max_width), "|", item[key])

def print_error(msg, name="Error"):
    """Print an error message to stderr"""
    print(f"[{name}] {msg}", file=sys.stderr)

def print_info(msg, name="Info"):
    """Print information message"""
    print(f"[{name}] {msg}", file=sys.stdout)

def print_warning(msg, name="Warning"):
    """Print a warning message to stderr"""
    print(f"[{name}] {msg}", file=sys.stderr)
