import requests
from time import sleep
import pandas as pd
import re
import time
from tqdm.auto import tqdm
import argparse
from collections.abc import MutableMapping
from filecache import filecache
import os


def file_exists(pattern):
    """Check if a file already exists."""
    files = os.listdir()
    return any([pattern in fn for fn in files])
    

@filecache
def petition_slug_to_id(slug):
    """Obtain a petition ID for a petition slug."""
    
    data = requests.get(f'https://www.change.org/p/{slug}/c')
    html = data.text
    
    assert data.ok, data.text
    
    regexp = 'data-petition_id="([0-9]+)"'
    id_ = int(re.search(regexp, html).groups()[0])
    print(f"Petition slug {slug} resolved to id {id_}")
    return id_


def flatten_dict(dct, delimeter="__"):
    """Make a flat dictionary out of a nested one."""
    
    def flatten_dict_g(dct, delimeter=delimeter):
        assert isinstance(dct, dict), dct

        for key, val in dct.items():
            if isinstance(val, dict):
                for subkey, subval in flatten_dict_g(val):
                    yield key + delimeter + subkey, subval
            else:
                yield key, val
    return dict(list(flatten_dict_g(dct)))


def limit(g, do_tqdm=True, nmax=10):
    """Limit entries from a generator."""
    for i, item in tqdm(enumerate(g), total=nmax):
        if i >= nmax:
            break
        yield item


def request_generator(f, f_delay=None, offset=0, batch_size=10, **kwargs):
    """Call f repeatedly with increasing offset, then call f_delay."""
    
    offset_current = offset
    
    while True:
        try:
            data = f(offset=offset_current, limit=batch_size, **kwargs)
        except Exception as e:
            print(f'Download failed at offset {offset_current}')
            print(e)
            break

        if not len(data):
            break
        for elem in data:
            yield elem
        offset_current += len(data)
        if f_delay is not None:
            f_delay()


def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str ='.') -> MutableMapping:
    """Flatten a dictionary.
    
    
    Taken from https://www.freecodecamp.org/news/how-to-flatten-a-dictionary-in-python-in-4-different-ways/
    """
    
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)