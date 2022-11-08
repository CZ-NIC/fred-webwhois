#
# Copyright (C) 2021-2022  CZ.NIC, z. s. p. o.
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
import warnings
from typing import Any, Optional

_DEPRECATED_MSG = "Dictionary interface on 'server_exception' variable is deprecated. Use attributes instead."


class WebwhoisError(Exception):
    """Represents an error in searching an object from Whois.

    Attributes:
        code: An error code.
        title: A human readable error title.
        message: A human readable error message.
    """

    def __init__(self, code: str, *, title: str, message: Optional[str] = None, **kwargs):
        self.code = code
        self.title = title
        self.message = message
        # Data for backwards compatible dictionary interface.
        self._data = dict(code=code, title=title, message=message, **kwargs)
        super().__init__(code, title, message)

    def __getitem__(self, key: Any) -> Any:
        warnings.warn(_DEPRECATED_MSG, DeprecationWarning)
        return self._data[key]

    def get(self, key: Any, default: Any = None) -> Any:
        """Return a value or default."""
        warnings.warn(_DEPRECATED_MSG, DeprecationWarning)
        return self._data.get(key, default)
