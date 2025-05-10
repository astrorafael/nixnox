import os
import functools

from lica.validators import vfile

def vextension(path: str, extension: str) -> str:
    _, ext = os.path.splitext(path)
    if ext != extension:
        # Can't use ValueError inside a functools.partial function
        raise Exception(f"Path does not end with {extension} extension")
    return path

vecsv = functools.partial(vextension, extension=".ecsv")
vtxt = functools.partial(vextension, extension=".txt")

def vecsvfile(path: str) -> str:
    path = vfile(path)
    return vecsv(path)

def vtxtfile(path: str) -> str:
    path = vfile(path)
    return vtxt(path)
