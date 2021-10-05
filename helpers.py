import requests
from time import sleep
import pandas as pd
import re
import time
from tqdm.auto import tqdm
import argparse


def petition_slug_to_id(slug):
    """Obtain a petition ID for a petition slug."""
    
    data = requests.get(f'https://www.change.org/p/{slug}/c')
    html = data.text
    
    assert data.ok, data.text
    
    regexp = 'data-petition_id="([0-9]+)"'
    return int(re.search(regexp, html).groups()[0])


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
