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


def request_comments(petition_id=None, limit=10, offset=0):
    """Obtain comments from Change.org."""

    url = 'https://www.change.org/api-proxy/-/comments?' +\
        f'limit={limit}&offset={offset}&commentable_type=Event&' +\
        f'commentable_id={petition_id}&parent_id=0&' +\
        'role[]=comment&role%5B%5D=comment_psf&role%5B%5D=comment_dashboard'
        # 'before_datetime=2021-09-07T04:31:22Z'

    r = requests.get(url)
    assert r.ok, r.text
    data = r.json()
    assert 'items' in data, r.text
    
    return list(map(flatten_dict, data['items']))


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


parser = argparse.ArgumentParser(description="Obtain last signatures for a petition on Change.org")
parser.add_argument('--petition_slug', type=str,
                    help="The last part of the URL in https://www.change.org/p/[petition_slug]",
                    required=True)
parser.add_argument('--limit', type=int, default=20, help="How many comments to obtain?")
parser.add_argument('--offset', type=int, default=0, help="From which comment to start?")
parser.add_argument('--delay_ms', type=int, default=500, help="How much to wait between requests?")


if __name__ == "__main__":
    
    # obtaining arguments
    args = parser.parse_args()

    # obtaining petition ID
    id_ = petition_slug_to_id(args.petition_slug)
    print(f"Petition ID is {id_}")
    
    # obtain the dataframe
    data = list(limit(request_generator(f=request_comments,
                                    f_delay=lambda: sleep(1. * args.delay_ms / 1000),
                  offset=args.offset, petition_id=id_), nmax=args.limit))

    df = pd.DataFrame(data)
    
    # output filename for the csv file
    out_filename = f"change_org_comments_petition_slug_{args.petition_slug}" +\
                   f"_at_{time.strftime('%Y%m%d-%H%M%S')}"+\
                   f"_limit_{args.limit}" +\
                   f"_offset_{args.offset}" +\
                   f"_delay_ms_{args.delay_ms}.csv"
    
    # saving data
    df.to_csv(out_filename, index=False)
    print(f"Data saved to {out_filename}")
