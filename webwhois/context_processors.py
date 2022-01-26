#!/usr/bin/python
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
from functools import lru_cache
from typing import Any, Dict, List, Tuple, cast

from django.http import HttpRequest

from .utils import WHOIS


@lru_cache()
def _get_managed_zones() -> Tuple[str, ...]:
    """Return managed zones."""
    return tuple(cast(List[str], WHOIS.get_managed_zone_list()))


def managed_zones(request: HttpRequest) -> Dict[str, Any]:
    """Return a context with managed zones."""
    return {
        'managed_zones': _get_managed_zones(),
    }
