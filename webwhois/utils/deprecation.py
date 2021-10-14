#
# Copyright (C) 2021  CZ.NIC, z. s. p. o.
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
#
"""Utilities for deprecation warnings."""
import warnings
from typing import Any

from django.utils.functional import SimpleLazyObject


def deprecated_context(value: Any, message: str) -> SimpleLazyObject:
    """Mark context variable as deprecated."""
    def _return_value() -> Any:
        warnings.warn(message, DeprecationWarning)
        return value
    return SimpleLazyObject(_return_value)
