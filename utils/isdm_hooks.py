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

# import shutil
import os
from pathlib import Path
from utils import parse_config as cfg, misc as m, printing as p

def check_if_custom(customvalue=False):
    """
    Retrieving custom value (custom section in the configfile)
    """
    config = cfg.parse_config()
    try:
        value = cfg.try_read_val(config, customvalue, 'custom')
    except cfg.configparser.NoSectionError as e:
        p.print_error("Section custom does not seem to exist in \
your configfile: {e}", e)
    except cfg.configparser.NoOptionError as e:
        p.print_error(f"{value} option does not seem to exist in \
your configfile: {e}")
    except Exception as e:
        p.print_error("Error while trying to get value from \
your configfile: %s", e)
    return value

def create_scratch_folders(user, groups=None, uid=None, gids=None):
    """
    Create scratch folders after creating the homedir
    Should call set_scratch_permissions at the end
    @Return True if ok
    """
    gid = 0
    user_scratch_path, endgroup_scratch_paths = retrieve_scratch_paths(user, \
        groups)
    if endgroup_scratch_paths:
        for scratch_group_path in endgroup_scratch_paths:
            found_group_name = None
            for g_name in groups:
                if scratch_group_path.endswith(f"/{g_name}"):
                    found_group_name = g_name
                    break
            if found_group_name:
                m.make_dir(scratch_group_path)
                m.set_permissions(scratch_group_path, "2770", 0, \
                    gids[found_group_name])
            else:
                p.print_error(f"Could not determine a valid group for \
{scratch_group_path} from available groups/gids.")
    if isinstance(gids, dict):
        if not gids:
            gid = 0
        else:
            gid = list(gids.values())[0]
    else:
        gid = gids
    if user_scratch_path:
        m.make_dir(user_scratch_path)
        m.set_permissions(user_scratch_path, "700", uid, gid)
    else:
        p.print_error("User scratch is not defined")
    return True

def create_symlinks(home_path, user, groups=None):
    """
    Basic function to check symbolic links in a homedir
    In order to create symlinks from home to all available scratchs
    for a specified user
    Should be called lastly, at the end of user_add, 
    after create_scratch_folders and set_scratch_permissions
    @Return True if ok
    """
    groups = [] if groups is None else groups
    found_scratch_groups = {}
    user_scratch_path, endgroup_scratch_paths = retrieve_scratch_paths(user, groups)
    if not os.path.isdir(home_path):
        return "Homedir does not exists !"
    if not os.path.isdir(user_scratch_path):
        p.print_error("Scratch User Path does not exists !")
    found_scratch_user = False
    for group in groups:
        found_scratch_groups[group] = False
    with os.scandir(home_path) as it:
        for entry in it:
            if entry.name.startswith('scratch_') and entry.is_symlink():
                if entry.name == f"scratch_{user}":
                    found_scratch_user = True
                for group in groups:
                    if entry.name == f"scratch_{group}":
                        found_scratch_groups[group] = True
    for scratch_group_path in endgroup_scratch_paths:
        group = os.path.basename(scratch_group_path)
        if not os.path.isdir(scratch_group_path):
            p.print_error("Scratch Group Path does not exists !")
        if os.path.isdir(scratch_group_path) and found_scratch_groups[group] is False:
            if group != user:
                os.symlink(scratch_group_path, f"{home_path}/scratch_{group}")
    if os.path.isdir(user_scratch_path) and found_scratch_user is False:
        os.symlink(user_scratch_path, f"{home_path}/scratch_{user}")
    return True

def remove_user_folders(user_scratch_force_removal=False, \
    homedir_force_removal=False, user=None, home_path=None):
    """
    Remove the user's personal scratch folder if the 'force' option is true.
    Group scratch directories are NOT removed by this function.
    @param user_scratch_force_removal: Boolean flag. If True, the user's scratch directory will be removed.
                  If False, no action is taken.
    @param user_scratch_force_removal: Boolean flag. If True, the user's scratch directory will be removed.
                  If False, no action is taken.
    @param user: The username.
    @param home_path: path to the homeDirectory
    """
    if user:
        user_scratch_path = None
        if user_scratch_force_removal:
            user_scratch_path, endgroup_scratch_paths = retrieve_scratch_paths(user, None)
        if not home_path:
            p.print_error("Home folder is not defined !")
            return False
        if not homedir_force_removal:
            home_path = None
        for user_folder in (user_scratch_path, home_path):
            if not user_folder:
                p.print_error(f"User folder path for '{user}' is not defined, cannot remove.")
                continue
            path_obj = Path(user_folder)
            if not path_obj.exists():
                p.print_info(f"User folder '{user_folder}' does not exist, no need to remove.")
            p.print_info(f"Attempting to remove user folder (forced): {user_folder}")
            if not m.remove_dir(user_folder):
                p.print_error(f"Failed to remove user scratch folder: {user_folder}")
        return True
    else:
        p.print_error("Trying to remove user folders without the user...?!")
        return False


def remove_symlinks(home_dir, username, groups_to_del):
    """
    Remove symlinks from the user's home directory for groups that are being deleted.
    @param home_dir: The path to the user's home directory.
    @param username: optionnaly used for the scratch symbolic link (used for del_user)
    @param groups_to_del: A list of group names (strings) for which symlinks should be removed.
    @Return True if successful or no action needed, False if an error occurred.
    """
    if not home_dir:
        p.print_error("Home directory not provided for symlink removal.")
        return False
    if not Path(home_dir).is_dir():
        p.print_error(f"Home directory '{home_dir}' does not exist or is \
not a directory. Cannot remove symlinks.")
        return False
    if not groups_to_del:
        p.print_info("No groups to remove symlinks for.")
        return True
    p.print_info(f"Attempting to remove symlinks for groups: {groups_to_del} in {home_dir}")
    success = True
    for group_name in groups_to_del:
        symlink_name = f"scratch_{group_name}"
        symlink_path = Path(f"{home_dir}/{symlink_name}")
        p.print_info(f"Attempting to remove symlink: {symlink_path}")
        try:
            os.unlink(symlink_path)
        except Exception as e:
            p.print_info(f"Failed to delete the symlink: {symlink_path}\
Error: {e}")
            return False
    if username:
        symlink_name = f"scratch_{username}"
        symlink_path = Path(f"{home_dir}/{symlink_name}")
        p.print_info(f"Attempting to remove symlink: {symlink_path}")
        try:
            os.unlink(symlink_path)
        except Exception as e:
            p.print_info(f"Failed to delete the symlink: {symlink_path}\
Error: {e}")
            return False
    return success


def retrieve_scratch_paths(user, groups=None):
    """
    Retrieve scratch path values
    @Returns user scratch path and group scratch path
    """
    groups = [] if groups is None else groups
    endgroup_scratch_paths = []
    config = cfg.parse_config()
    try:
        scratch_path = cfg.try_read_val(config, 'scratch', 'custom')
        user_scratch_path = cfg.try_read_val(config, 'user_scratch', 'custom')
        group_scratch_path = cfg.try_read_val(config, 'group_scratch', 'custom')
    except cfg.configparser.NoSectionError as e:
        p.print_error("Section custom does not seem to exist in your \
configfile: %s", e)
    if group_scratch_path and groups:
        for group in groups:
            if group != user:
                endgroup_scratch_paths.append(f"{group_scratch_path}/{group}")
    else:
        if scratch_path and groups:
            for group in groups:
                if group != user:
                    endgroup_scratch_paths.append(f"{scratch_path}/{group}")
        else:
            p.print_error("No scratch_path, group_scratch_path or groups \
value defined")
    if user_scratch_path:
        user_scratch_path = f"{user_scratch_path}/{user}"
    elif scratch_path:
        user_scratch_path = f"{scratch_path}/{user}"
    else:
        p.print_error("No scratch_path or user_scratch_path value defined")
    return user_scratch_path, endgroup_scratch_paths
