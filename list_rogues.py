#!/usr/bin/python

''' 
Written by Matt Fowler (mattf@juniper.net).
Python script to list all wired rogues.

'''


# =====
# IMPORTS
# =====

import sys, requests
import csv, json

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# =====
# VARIABLES
# =====

api_token = '' # Add your API Token in the quotes

org_id = '' # Add your Org ID in the quotes

# Choose your cloud by uncommenting
api_url = "https://api.mist.com/api/v1"
#api_url = "https://api.gc1.mist.com/api/v1"
#api_url = "https://api.gc2.mist.com/api/v1"
#api_url = "https://api.ac2.mist.com/api/v1"
#api_url = "https://api.eu.mist.com/api/v1"

headers = {
	'Content-Type': 'application/json; charset=utf-8', 'Accept-Encoding': 'gzip, deflate',
	'Authorization': 'Token ' + api_token
}

# =====
# FUNCTIONS
# =====

def get_sites(session):
	print('Getting sites.')

	url = '{}/orgs/{}/sites'.format(api_url, org_id)
	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to GET')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return []

	result = json.loads(result.text)
	return result

def get_rogue_insights(session, site_id):
	print('Getting rogues for {}.'.format(site_id))
	url = '{}/sites/{}/insights/rogues?limit=100&duration=1d&type=lan'.format(api_url, site_id)
	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to GET')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return []

	result = json.loads(result.text)
	return result

def retry_session(retries, session=None, backoff_factor=1.5):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        allowed_methods=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Create session
session = retry_session(retries=10)

# Get Sites
sites = get_sites(session)

rogue_count = 0

# Open csv and write first row 
with open('rogues.csv', 'w') as f:
    writer = csv.writer(f, delimiter=',')
    writer.writerow(['Site', 'SSID', 'BSSID', 'Band'])


    # For each site, get the APs and add data to csv
    for site in sites:
        rogues = get_rogue_insights(session, site['id'])
        if rogues['results']:
            print('Found rogues at {}'.format(site['name']))
            for rogue in rogues['results']:
                    rogue_count += 1
                    data = [site['name'], rogue['ssid'], rogue['bssid'], rogue['band']]
                    print('Adding {} ({}).'.format(rogue['ssid'], rogue['bssid']))
                    writer.writerow(data)
                    print('Done')
        else:
            print('No rogues at {}'.format(site['name']))

f.close()
print('\n\n{} total rogues found.'.format(rogue_count))
