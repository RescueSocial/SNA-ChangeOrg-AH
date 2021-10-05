import requests
from time import sleep
import pandas as pd
import re
import time
from tqdm.auto import tqdm
import argparse
from helpers import petition_slug_to_id, flatten_dict, limit, request_generator
from urllib.parse import quote


def search_petitions(query, offset=0, **kwargs):
    """Get petitions with a given search query."""
    query_quoted = quote(query)
    
    r = requests.get(f'https://www.change.org/api-proxy/-/petitions/search?q={query_quoted}&offset={offset}')
    assert r.ok, r.text
    r_json = r.json()
    assert 'items' in r_json, r.text
    
    return list(map(flatten_dict, r_json['items']))


parser = argparse.ArgumentParser(description="Search for petitions on Change.org")
parser.add_argument('--search_query', type=str,
                    help="Search query on Change.org",
                    required=True)
parser.add_argument('--limit', type=int, default=20, help="How many petitions to obtain?")
parser.add_argument('--offset', type=int, default=0, help="From which petition to start?")
parser.add_argument('--delay_ms', type=int, default=500, help="How much to wait between requests?")


if __name__ == "__main__":
    
    # obtaining arguments
    args = parser.parse_args()

    # obtain the dataframe
    data = list(limit(request_generator(f=search_petitions,
                                    f_delay=lambda: sleep(1. * args.delay_ms / 1000),
                  offset=args.offset, query=args.search_query), nmax=args.limit))

    df = pd.DataFrame(data)
    
    # output filename for the csv file
    petitions_escaped = args.search_query.replace(' ', '_')
    out_filename = f"change_org_petitions_{petitions_escaped}" +\
                   f"_at_{time.strftime('%Y%m%d-%H%M%S')}"+\
                   f"_limit_{args.limit}" +\
                   f"_offset_{args.offset}" +\
                   f"_delay_ms_{args.delay_ms}.csv"
    
    # saving data
    df.to_csv(out_filename, index=False)
    print(f"Data saved to {out_filename}")
