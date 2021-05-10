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
"""Utilities for constants."""
from enum import Enum, IntFlag, unique
from typing import Set, Tuple, cast


class _DnskeyMixin:
    """Base mixin for DnskeyAlgorithm and DnskeyFlag."""

    label: str

    # mypy doesn't detect enum items, if generated dynamically.
    # Define __getattribute__ to mask that.
    def __getattribute__(self, name: str) -> '_DnskeyAlgorithmBase':
        return cast('_DnskeyAlgorithmBase', super().__getattribute__(name))


@unique
class _DnskeyAlgorithmBase(_DnskeyMixin, int, Enum):
    """Base class for DnskeyAlgorithm."""

    def __new__(cls, value: int, label: str):
        """Construct item with label."""
        obj = super().__new__(cls, value)
        obj._value_ = value

        obj.label = label
        return obj


@unique
class _DnskeyFlagBase(_DnskeyMixin, IntFlag):  # type: ignore[misc]
    """Base class for DnskeyFlag."""

    def __new__(cls, value: int, label: str):
        """Construct item with label."""
        obj = super().__new__(cls, value)
        obj._value_ = value

        obj.label = label
        return obj

    @property
    def flags(self) -> Set['_DnskeyFlagBase']:
        """Return individual flags."""
        return {f for f in cast(Tuple['_DnskeyFlagBase', ...], tuple(self.__class__)) if f in self}
