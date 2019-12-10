#
# Copyright (C) 2016-2019  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from django.utils.module_loading import import_string


def create_logger(logger_path, logger_corba_object):
    """
    Return logger instance or None when logger_path is not set.

    @param logger_path: Path to the logger module.
    @param logger_corba_object: Corba object of Logger.
    @param corba_ccreg: Corba object ccReg.
    @raise ImportError: If logger_path is invalid.
    """
    logger_class = import_string(logger_path)
    return logger_class(logger_corba_object)
