#!/usr/bin/python

''' 
Written by Matt Fowler (mattf@juniper.net).
Python script to get AP inventory with IP address.

'''


# =====
# IMPORTS
# =====

import sys, requests
import csv, json


# =====
# VARIABLES
# =====

api_token = '' # Add your API Token in the quotes

org_id = '' # Add your Org ID in the quotes

# Choose your cloud by uncommenting
api_url = "https://api.mist.com/api/v1"
#api_url = "https://api.gc1.mist.com/api/v1"
#api_url = "https://api.gc2.mist.com/ap1/v1"
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
	url = '{}/sites/{}/stats/devices?type=switch'.format(api_url, site_id)
	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to GET')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return []

	result = json.loads(result.text)
	return result

# Create session
session = requests.Session()

# Get Sites
sites = get_sites(session)


# Open csv and write first row
with open('inventory.csv', 'w') as f:
	writer = csv.writer(f, delimiter=',')
	writer.writerow(['Name', 'Serial', 'IP Address', 'MAC Address', 'Site', 'Status', 'Version'])


	# For each site, get the APs and add data to csv
	for site in sites:
		devices = get_stats_devices(session, site['id'])
		for device in devices:
			if 'ip_stat' in device:
				data = [device['name'], device['serial'], device['ip_stat']['ip'], device['mac'], site['name'], device['status'], device['version']]
				print('Adding {} ({}).'.format(device['name'], site['name']))
				writer.writerow(data)
				print('Done')
			else:
				data = [device['mac'], device['serial'], '0.0.0.0', device['mac'], site['name'], device['status'], 'N/A']
				print('Adding {} ({}).'.format(device['name'], site['name']))
				writer.writerow(data)
				print('Done. But it had no IP - marking it 0.0.0.0.')

f.close()
