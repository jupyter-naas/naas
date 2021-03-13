from sanic.views import HTTPMethodView
from sanic.response import json
from naas.runner.env_var import n_env

from pathlib import Path


def get_folder_size(folder):
    return ByteSize(sum(file.stat().st_size for file in Path(folder).rglob("*")))


class ByteSize(int):

    _kB = 1024
    _suffixes = "B", "kB", "MB", "GB", "PB"

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        self.bytes = self.B = int(self)
        self.kilobytes = self.kB = self / self._kB ** 1
        self.megabytes = self.MB = self / self._kB ** 2
        self.gigabytes = self.GB = self / self._kB ** 3
        self.petabytes = self.PB = self / self._kB ** 4
        *suffixes, last = self._suffixes
        suffix = next(
            (suffix for suffix in suffixes if 1 < getattr(self, suffix) < self._kB),
            last,
        )
        self.readable = suffix, getattr(self, suffix)

        super().__init__()

    def __str__(self):
        return self.__format__(".2f")

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, super().__repr__())

    def __format__(self, format_spec):
        suffix, val = self.readable
        return "{val:{fmt}} {suf}".format(val=val, fmt=format_spec, suf=suffix)

    def __sub__(self, other):
        return self.__class__(super().__sub__(other))

    def __add__(self, other):
        return self.__class__(super().__add__(other))

    def __mul__(self, other):
        return self.__class__(super().__mul__(other))

    def __rsub__(self, other):
        return self.__class__(super().__sub__(other))

    def __radd__(self, other):
        return self.__class__(super().__add__(other))

    def __rmul__(self, other):
        return self.__class__(super().__rmul__(other))


class SizeController(HTTPMethodView):
    def __init__(self, *args, **kwargs):
        super(SizeController, self).__init__(*args, **kwargs)

    async def get(self, request):
        data = {
            "size": str(get_folder_size(n_env.server_root)),
        }
        return json(data)
