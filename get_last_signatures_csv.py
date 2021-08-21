import pandas as pd
import requests
from collections.abc import MutableMapping
import json
import time
import argparse


def petition_signatures_request(petitionSlug, maxSigners):
    """Obtain the request to obtain the requested number of signatures for a given petition (by slug)."""

    # string below copied from Developer Tools
    petition_signatures_graphql_post_request = \
    \
    "[{\"operationName\":null,\"variables\":{\"locale\":\"en-US\",\"countryCode\":\"CH\"},\"query\":\"query ($locale: String!, $countryCode: String!) {\\n  featureConfigs {\\n    gdpr_cookie_prefs: featureConfig(\\n      name: \\\"gdpr_cookie_prefs\\\"\\n      groups: [$locale, $countryCode]\\n    )\\n  }\\n}\\n\"},{\"operationName\":null,\"variables\":{\"locale\":\"en-US\",\"countryCode\":\"CH\"},\"query\":\"query ($locale: String!, $countryCode: String!) {\\n  featureConfigs {\\n    maintenance_banner: featureConfig(\\n      name: \\\"maintenance_banner\\\"\\n      groups: [$locale, $countryCode]\\n    )\\n  }\\n}\\n\"},{\"operationName\":null,\"variables\":{\"locale\":\"en-US\",\"countryCode\":\"CH\"},\"query\":\"query ($locale: String!, $countryCode: String!) {\\n  featureConfigs {\\n    show_csat_survey_banner: featureConfig(\\n      name: \\\"show_csat_survey_banner\\\"\\n      groups: [$locale, $countryCode]\\n    )\\n    show_csat_survey_banner_sampling: featureConfig(\\n      name: \\\"show_csat_survey_banner_sampling\\\"\\n      groups: [$locale, $countryCode]\\n    )\\n  }\\n}\\n\"},{\"operationName\":null,\"variables\":{\"locale\":\"en-US\",\"countryCode\":\"CH\"},\"query\":\"query ($locale: String!, $countryCode: String!) {\\n  featureConfigs {\\n    gdpr_consent_optin_banner: featureConfig(\\n      name: \\\"gdpr_consent_optin_banner\\\"\\n      groups: [$locale, $countryCode]\\n    )\\n    gdpr_consent_optin_banner_copy: featureConfig(\\n      name: \\\"gdpr_consent_optin_banner_copy\\\"\\n      groups: [$locale, $countryCode]\\n    )\\n  }\\n}\\n\"},{\"operationName\":null,\"variables\":{\"locale\":\"en-US\",\"countryCode\":\"CH\"},\"query\":\"query ($locale: String!, $countryCode: String!) {\\n  featureConfigs {\\n    supporter_petition_tabs_update_count: featureConfig(\\n      name: \\\"supporter_petition_tabs_update_count\\\"\\n      groups: [$locale, $countryCode]\\n    )\\n  }\\n}\\n\"},{\"operationName\":null,\"variables\":{},\"query\":\"{\\n  session: viewer {\\n    consentResponses {\\n      globalConsentInitialEu\\n    }\\n  }\\n}\\n\"},{\"operationName\":\"PetitionStats\",\"variables\":{\"petitionSlug\":\"hollywood-boycott-aquaman-2-amber-heard\",\"maxSigners\":20,\"shouldFetchRecruiter\":false,\"recruiterId\":\"\"},\"query\":\"query PetitionStats($petitionSlug: String!, $maxSigners: Int!, $shouldFetchRecruiter: Boolean!, $recruiterId: ID!) {\\n  petitionStats: petitionBySlug(slug: $petitionSlug) {\\n    id\\n    signatureCount {\\n      displayed\\n    }\\n    signatureGoal {\\n      displayed\\n    }\\n    recentSignersConnection(first: $maxSigners) {\\n      edges {\\n        timestamp\\n        node {\\n          id\\n          displayName\\n          photo {\\n            id\\n            userSmall {\\n              url\\n            }\\n          }\\n        }\\n      }\\n    }\\n  }\\n  recruiter: userById(id: $recruiterId) @include(if: $shouldFetchRecruiter) {\\n    id\\n    displayName\\n    photo {\\n      id\\n      userSmall {\\n        url\\n      }\\n    }\\n  }\\n}\\n\"}]"
    
    petition_signatures_graphql_post_request_template = \
        petition_signatures_graphql_post_request.\
        replace('"petitionSlug":"hollywood-boycott-aquaman-2-amber-heard"', '"petitionSlug":"%s"').\
        replace('"maxSigners":20', '"maxSigners":%d')
    
    return petition_signatures_graphql_post_request_template % (petitionSlug, maxSigners)


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


def get_signatures_dataframe(petition_slug: str, number_signatures: int):
    """Obtain a dataframe with the signatures."""

    # see above how we got it
    url = 'https://www.change.org/api-proxy/graphql'

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.change.org/p/' + petition_slug,
        'content-type': 'application/json',
        'X-Requested-With': 'http-link',
        'Origin': 'https://www.change.org',

        # this we can get via Selenium
        # but actually we don't even need it
    #     'Cookie': '_change_session=0ccbdae59ad205509a87d4ccaac10b22; _change_lang=%7B%22locale%22%3A%22en-US%22%2C%22countryCode%22%3A%22CH%22%7D; __cfruid=52df2690810b7adc3fab2488ce9bc11daad0b5d1-1629521373; optimizelyEndUserId=oeu1629521378944r0.34965887355134595; G_ENABLED_IDPS=google',


        'Sec-GPC': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'TE': 'Trailers'
    }

    # the POST request
    data_str = petition_signatures_request(petitionSlug=petition_slug,
                                           maxSigners=number_signatures).strip()

    # issuing the request
    x = requests.post(url, data=data_str, headers=headers)
    
    print(f"Response: {x.status_code} {x.reason}")
    
    if not x.ok:
        raise ValueError(f"The request to Change.org has failed: {x.text} {x.status_code}")
    
    try:
        # extract signatures
        data = x.json()[6]['data']['petitionStats']['recentSignersConnection']['edges']

        # as dataframe
        df = pd.DataFrame(map(flatten_dict, data))
    except TypeError as w:
        raise ValueError(f"The response contains unknown data: {w}")
    
    return df
    
    
parser = argparse.ArgumentParser(description="Obtain last signatures for a petition on Change.org")
parser.add_argument('--petition_slug', type=str,
                    help="The last part of the URL in https://www.change.org/p/[petition_slug]",
                    required=True)
parser.add_argument('--number_signatures', type=int, default=20, help="Number of last signatures to obtain")


if __name__ == "__main__":
    
    # obtaining arguments
    args = parser.parse_args()
    
    # obtain the dataframe
    df = get_signatures_dataframe(petition_slug=args.petition_slug,
                                  number_signatures=args.number_signatures)
    
    # output filename for the csv file
    out_filename = f"change_org_petition_slug_{args.petition_slug}" +\
                   f"_at_{time.strftime('%Y%m%d-%H%M%S')}"+\
                   f"_max_number_signatures_{args.number_signatures}.csv"
    
    # saving data
    df.to_csv(out_filename, index=False)
    print(f"Data saved to {out_filename}")