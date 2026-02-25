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

import configparser
from pathlib import Path
from os import access, R_OK
import ast
import utils.logger as l

def file_readable(file):
    """
    :Param path to a file
    check if file is readable
    """
    assert(access(file, R_OK)), f"File {file} is not readable"
    return file

def parse_config():
    """
    Parse config main function
    :Return config
    """
    config = configparser.ConfigParser()
    paths = ["obol.conf", "/etc/obol.conf"]
    for p in paths:
        path = Path(p)
        if path.is_file():
            p = file_readable(p)
            config.read(p)
            break
    return config

def try_read_val(config, key, section):
    """
    :Param configuration content, key, section
    :Return value
    """
    try:
        val = config[section][key]
    except Exception as e:
        val = None
        l.logger.error(f"Value {key} in section {section} does not \
            seem to exist: {e}")
    return val

def try_read_int(config, key, section):
    """
    :Param configuration content, key, section
    :Return value
    """
    try:
        val = config.getint(section, key)
    except Exception as e:
        val = None
        l.logger.error(f"Value {key} in section {section} does not \
            seem to exist: {e}")
    return val

def try_read_list(config, key, section):
    """
    :Param configuration content, key, section
    :Return value
    """
    try:
        val = config[section][key]
        arr = ast.literal_eval(val)
    except Exception as e:
        val = None
        l.logger.error(f"Value {key} in section {section} does not \
            seem to exist: {e}")
    return arr