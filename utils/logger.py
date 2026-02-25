
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

import logging

# import os
# dir_path = os.path.dirname(os.path.realpath(__file__))


#logging.basicConfig(level = logging.INFO)
# create a new logger instead of the default root logger
logger    = logging.getLogger('mylogger')

formatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")

# create file handler which logs even warn messages
# info messages are displayed to stdout
logger.setLevel(logging.INFO)
fhw = logging.FileHandler('/var/log/obol.log')
fhw.setLevel(logging.INFO)
logger.addHandler(fhw)
