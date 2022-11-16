#!/usr/bin/python

''' 
Written by Matt Fowler (mattf@juniper.net).
Python script to find non-wifi interferers.

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

def get_stats_devices(session, site_id):
	print('Getting devices for {}.'.format(site_id))
	url = '{}/sites/{}/stats/devices?type=ap'.format(api_url, site_id)
	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to GET')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return []

	result = json.loads(result.text)
	return result

def get_rrm_devices(session, site_id, device_id, band):
	print('Getting RRM data for {}.'.format(device_id))
	url = '{}/sites/{}/rrm/current/devices/{}/band/{}'.format(api_url, site_id, device_id, band)
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
        method_whitelist=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Create session
session = retry_session(retries=10)

# Get Sites
sites = get_sites(session)

no_rrm = 0

# Open csv and write first row
with open('interferers.csv', 'w') as f:
	writer = csv.writer(f, delimiter=',')
	writer.writerow(['Site', 'AP', '36', '40', '44', '48', '52', '56', '60', '64', '100', '104', '108', '112', '116', '132', '136', '140', '144', '149', '153', '157', '161', '165'])


	# For each site, get the APs and add data to csv
	for site in sites:
		devices = get_stats_devices(session, site['id'])
		for device in devices:
			found_interference = 0
			if device['status'] == 'connected':
				rrm_data = get_rrm_devices(session, site['id'], device['id'], '5')
				if 'results' in rrm_data:
					channel_non_wifi = {'36': '0', '40': '0', '44': '0', '48': '0', '52': '0', '56': '0', '60': '0', '64': '0', '100': '0', '104': '0', '108': '0', '112': '0', '116': '0', '120': '0', '124': '0', '128': '0', '132': '0', '136': '0', '140': '0', '144': '0', '149': '0', '153': '0', '157': '0', '161': '0', '165': '0'}
					for channel in rrm_data['results']:
						if channel['util_score_non_wifi'] > 0.2:
							channel_non_wifi[str(channel['channel'])] = int(channel['util_score_non_wifi']*100)
							found_interference += 1
						else:
							channel_non_wifi[str(channel['channel'])] = '0'
					data = [site['name'], device['name'], channel_non_wifi['36'], channel_non_wifi['40'], channel_non_wifi['44'], channel_non_wifi['48'], channel_non_wifi['52'], channel_non_wifi['56'], channel_non_wifi['60'], channel_non_wifi['64'], channel_non_wifi['100'], channel_non_wifi['104'], channel_non_wifi['108'], channel_non_wifi['112'], channel_non_wifi['116'], channel_non_wifi['132'], channel_non_wifi['136'], channel_non_wifi['140'], channel_non_wifi['144'], channel_non_wifi['149'], channel_non_wifi['153'], channel_non_wifi['157'], channel_non_wifi['161'], channel_non_wifi['165']]
					if found_interference > 0:
						print('Adding {} ({}).'.format(device['name'], site['name']))
						writer.writerow(data)
						print('Done')
					else:
						print('No interferers for {} ({}).'.format(device['name'], site['name']))
				else:
					print('No RRM data for {}'.format(device['name']))
					no_rrm += 1
			else:
				continue

f.close()
print(no_rrm)
