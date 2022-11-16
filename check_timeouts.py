#!/usr/bin/python

''' 
Written by Matt Fowler (mattf@juniper.net).
Python script to find orgs with non-default idle or session timers.

'''

import requests
import json

api_token = ''
api_url_g01 = 'https://api.mist.com/api/v1'
api_url_g02 = 'https://api.gc1.mist.com/api/v1'
api_url_g03 = 'https://api.ac2.mist.com/api/v1'
api_url_g04 = 'https://api.gc2.mist.com/api/v1'
api_url_eu01 = 'https://api.eu.mist.com/api/v1'


def get_self(session, headers):
	url = '{}/self'.format(api_url)

	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return (False, None, result)

	result = json.loads(result.text)
	return result

def get_org(session, headers, org_id):
	url = '{}/orgs/{}'.format(api_url, org_id)

	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return (False, None, result)

	result = json.loads(result.text)
	return result

def get_org_setting(session, headers, org_id):
	url = '{}/orgs/{}/setting'.format(api_url, org_id)

	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return (False, None, result)

	result = json.loads(result.text)
	return result

session = requests.Session()

# Main
if __name__ == '__main__':

	print ("""
	This script will check timeouts on all Orgs attached to your account.
	""")
	ans = 'invalid'
	while ans == 'invalid':
		ans=input("""
		Which cloud is this for?
		1.Global 01
		2.Global 02
		3.Global 03
		4.Global 04
		5.Europe 01
		""")
		if ans=="1": 
			api_url = api_url_g01
		elif ans=="2":
			api_url = api_url_g02
		elif ans=="3":
			api_url = api_url_g03
		elif ans=="4":
			api_url = api_url_g04
		elif ans=="5":
			api_url = api_url_eu01
		elif ans !="":
			print("\n Not Valid Choice Try again")
			ans = 'invalid'

	api_token = input("""
		Please enter your API Token:
		""")

	headers = {
	'Content-Type': 'application/json; charset=utf-8', 'Accept-Encoding': 'gzip, deflate',
	'Authorization': 'Token ' + api_token
	}

	result = get_self(session, headers)
	lowest_idle = 99999999
	lowest_session = 99999999
	non_default_list = []
	for i in result['privileges']:
		if i['scope'] == 'org':
			org_id = i['org_id']
			org_config = get_org(session, headers, org_id)
			org_name = org_config['name']
			session_expiry = org_config['session_expiry']
			org_setting = get_org_setting(session, headers, org_id)
			if 'ui_idle_timeout' in org_setting:
				idle_timeout = org_setting['ui_idle_timeout']
			else:
				idle_timeout = 0
			print('Checked {}'.format(org_name))
			if idle_timeout != 0 or session_expiry != 1440:
				non_default_list.append('{} ({}) Idle: {} Session: {}'.format(org_name, org_id, idle_timeout, session_expiry))
				print('{}\nSession Expiry: {}\nIdle Timeout: {}\n\n'.format(org_name, session_expiry, idle_timeout))
				print('{} NOT STANDARD!! Please Check!\n\n'.format(org_name))
				if 0 < idle_timeout < lowest_idle:
					lowest_idle = idle_timeout
					lowest_idle_org = org_name
				if session_expiry < lowest_session:
					lowest_session = session_expiry
					lowest_session_org = org_name
	
	if non_default_list:
		print("""\n\n
		##########################################
		Here are the Orgs with one or more non-default timers:
		""")
		print(*non_default_list, sep='\n')
		print("""
		##########################################
		\n\n""")

	if lowest_idle == 99999999:
		print('No org has a non-default idle timeout')
	else:
		print('{} has the lowest idle timeout of {} minutes.'.format(lowest_idle_org, lowest_idle))
	
	if lowest_session >= 1440:
		print('No org has a session expiry below 1440 minutes.')
	else:
		print('{} has the lowest session expiry of {} minutes.'.format(lowest_session_org, lowest_session))