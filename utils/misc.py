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

import os
import datetime
import shutil
from pathlib import Path
from utils import logger as l, printing as p

def calc_calendar(value):
    """Calendar function from a shadowExpire/shadowLastChange value"""
    epoch_date_time = datetime.datetime.fromtimestamp(int(value)*3600*24)
    return epoch_date_time

def rev_calendar(value):
    """Convert date to shadowExpire/shadowLastChange value"""
    year_month_day_formatted = [int(i) for i in value]
    dt = datetime.datetime(year_month_day_formatted[0], year_month_day_formatted[1], \
        year_month_day_formatted[2])
    epoch_days = dt.timestamp()/(3600*24)
    return round(epoch_days)


def create_homedir(uid, gid, home, skel):
    """Create the user's home directory"""
    if not os.path.exists(home):
        if skel is not None:
            try:
                shutil.copytree(skel, home)
            except Exception as e:
                p.print_error( \
                    f"Error while trying to copy the skeleton {skel} to the home {home} \
                    with error {e}")
        else:
            make_dir(home)
        set_permissions(home, "700", int(uid), int(gid))
    else:
        home_folder_uid = int(os.stat(home).st_uid)
        if home_folder_uid != int(uid):
            p.print_warning(
                f"Home directory {home} already exists and has wrong owner \
                uid {home_folder_uid}, should be {uid}"
            )

def make_dir(directory):
    """Create a directory"""
    path=Path(directory)
    try:
        path.mkdir(parents=True, exist_ok=True)
        p.print_info(f"Directory '{directory}' created successfully.")
    except PermissionError:
        p.print_error(f"Permission denied: Unable to create '{directory}'.")
    except Exception as e:
        p.print_error(f"An error occurred while trying to create \
            {directory}: {e}")

def set_permissions(directory, permissions, owner=None, group=0):
    """
    Set permissions on folders
    corresponding to user homedirs, scratch and group scratchs
    @Return True if ok
    """
    try:
        os.chmod(directory, int(permissions,8))
        #group = owner if group is None else group
        if owner is not None:
            recursive_chown(directory, owner, group)
    except Exception as e:
        p.print_error(f"Issue while trying to set permissions {permissions} \
        on {directory} with error: {e}")
    return True

def recursive_chown(path, owner, group=0):
    """
    Recursive pure python function
    from https://stackoverflow.com/a/57458550 (adding group needs)
    """
    owner = int(owner)
    group = int(group)
    for dirpath, dirnames, filenames in os.walk(path):
        try:
            shutil.chown(dirpath, owner, group)
            for filename in filenames:
                shutil.chown(os.path.join(dirpath, filename), owner, group)
        except Exception as e:
            p.print_error(f"Error while trying to change owner {owner} on \
dirpath {dirpath} ({e})")

def remove_dir(directory):
    """Recursively remove a directory if it exists"""
    path = Path(directory)
    if not path.exists():
        p.print_info(f"Directory '{directory}' does not exist, skipping removal.")
        return True
    try:
        shutil.rmtree(path)
        p.print_info(f"Directory '{directory}' removed successfully.")
        return True
    except PermissionError:
        p.print_error(f"Permission denied: Unable to remove '{directory}'.")
        return False
    except OSError as e:
        p.print_error(f"Error removing directory '{directory}': {e}")
        return False
    except Exception as e:
        p.print_error(f"An unexpected error occurred while removing '{directory}': {e}")
        return False
