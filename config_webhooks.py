#!/usr/bin/python

''' 
Written by Matt Fowler (mattf@juniper.net).
Python script to configure a webhook across multiple sites.

'''

# =====
# IMPORTS
# =====

import requests, json


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

# Sites to exclude from config. Add site names to the list.
excluded_sites = []

# Enter Webhook config

webhook_config = {
	"name": "",
    "url": "",
    "topics": [
        "location"
    ],
    "verify_cert": False,
    "enabled": True,
    "secret": "",
    "headers": {
        "Authorization": ""
    }
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

def config_site_webhook(session, config, ap_site_id):
	url = '{}/sites/{}/webhooks'.format(api_url, ap_site_id)
	payload = json.dumps(config)

	result = session.post(url, headers=headers, data=payload)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Payload: {}'.format(payload))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return False

	return True

# Create session
session = requests.Session()

# Get Sites
sites = get_sites(session)

for site in sites:
	if site['name'] not in excluded_sites:
		webhook = config_site_webhook(session,webhook_config, site['id'])
		if webhook:
			print('Done for {}'.format(site['name']))
	else:
		print('{} is an excuded site. Skipping.'.format(site['name']))

	