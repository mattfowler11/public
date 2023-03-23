#!/usr/bin/python

''' 
Written by Matt Fowler (mattf@juniper.net).
Python script that creates Sites from a CSV file. Also moves and renames devices based on CSV.
'''

# =====
# IMPORTS
# =====

import re
import sys, requests
import csv, json
import time

from config import *


# =====
# FILES ETC
# =====

file = 'sites.csv' # Site creation CSV
assign_file = 'assign_file.csv' # Device assignment and naming CSV
epoch_time = int(time.time())


# =====
# FUNCTIONS
# =====

# Convert CSV file to JSON
def csv_to_json(file):
	csv_rows = []
	
	with open(file, 'r') as csv_file:
		reader = csv.DictReader(csv_file)
		title = reader.fieldnames

		for row in reader:
			csv_rows.extend([{title[i]: row[title[i]] for i in range(len(title))}])

	return csv_rows

# Create Site
def create_site(session, site):
	url = '{}/orgs/{}/sites'.format(api_url, org_id)
	payload = json.dumps(site)

	result = session.post(url, headers=headers, data=payload)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Payload: {}'.format(payload))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return None

	result = json.loads(result.text)
	return result['id']

# Claim APs
def update_inventory(session, setting):
	url = '{}/orgs/{}/inventory'.format(api_url, org_id)
	payload = json.dumps(setting)

	result = session.post(url, headers=headers, data=payload)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Payload: {}'.format(payload))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return None

	result = json.loads(result.text)
	return result

# Configure Site
def update_site_setting(session, site_id, setting):
	url = '{}/sites/{}/setting'.format(api_url, site_id)
	payload = json.dumps(setting)

	result = session.put(url, headers=headers, data=payload)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Payload: {}'.format(payload))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return False

	return True


# Get Site Group ID by Name (if it exists)
def get_sitegroup(session, name, result=[]):
	url = '{}/orgs/{}/sitegroups'.format(api_url, org_id)
	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to GET')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return (False, None, result)

	result = json.loads(result.text)
	try:
		# Return first matching sitegroup
		return next((True, r['id'], result) for r in result if r['name'] == name)
	except:
		return (True, None, result)


# Get all Site Groups
def get_sitegroups(session, result=[]):
	if result == []:
		url = '{}/orgs/{}/sitegroups'.format(api_url, org_id)
		result = session.get(url, headers=headers)
	
		if result.status_code != 200:
			print('Failed to GET')
			print('URL: {}'.format(url))
			print('Response: {} ({})'.format(result.text, result.status_code))

			return []

	result = json.loads(result.text)
	return result

# Get all RF Templates
def get_rf_templates(session):

	url = '{}/orgs/{}/rftemplates'.format(api_url, org_id)
	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to GET')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return []

	result = json.loads(result.text)
	return result

def get_sites(session):

	url = '{}/orgs/{}/sites'.format(api_url, org_id)
	result = session.get(url, headers=headers)

	if result.status_code != 200:
		print('Failed to GET')
		print('URL: {}'.format(url))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return []

	result = json.loads(result.text)
	return result

# Create Site Group
def create_sitegroup(session, name):
	url = '{}/orgs/{}/sitegroups'.format(api_url, org_id)

	payload = json.dumps({ 'name': name })

	result = session.post(url, headers=headers, data=payload)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Payload: {}'.format(payload))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return None

	result = json.loads(result.text)
	return result['id']

def get_geocode(address):
	address.replace(' ','+')
	url = 'https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'.format(address, google_api)

	result = requests.post(url)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Payload: {}'.format(payload))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return None

	result = json.loads(result.text)
	return result

def get_timezone(location):
	url = 'https://maps.googleapis.com/maps/api/timezone/json?location={}&timestamp={}&key={}'.format(location, epoch_time, google_api)

	result = requests.post(url)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Payload: {}'.format(payload))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return None

	result = json.loads(result.text)
	return result

def move_device(session, ap_setting):
	url = '{}/orgs/{}/inventory'.format(api_url, org_id)
	payload = json.dumps(ap_setting)

	result = session.put(url, headers=headers, data=payload)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Payload: {}'.format(payload))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return False

	return True

def update_device(session, device_setting, device_site_id, device_mac):
	device_id = '00000000-0000-0000-1000-{}'.format(device_mac)
	url = '{}/sites/{}/devices/{}'.format(api_url, device_site_id, device_id)
	payload = json.dumps(device_setting)

	result = session.put(url, headers=headers, data=payload)

	if result.status_code != 200:
		print('Failed to POST')
		print('URL: {}'.format(url))
		print('Payload: {}'.format(payload))
		print('Response: {} ({})'.format(result.text, result.status_code))

		return False

	return True

def add_sites():

	# Ensure variables are defined
	if api_token == '' or org_id == '' or file == '' or api_url == '':
		print('Missing variables:')
		print('api_token={}'.format(api_token))
		print('org_id={}'.format(org_id))
		print('file={}'.format(file))
		print('api_url={}'.format(api_url))

		sys.exit(1)

	# Create session
	session = requests.Session()

	# Convert sites.csv file to json
	csv_data = csv_to_json(file)

	existing_sites = get_sites(session)

	existing_sitegroups = get_sitegroups(session)

	existing_rf_templates = get_rf_templates(session)

	existing_site_names = []
	for site in existing_sites:
		existing_site_names.append(site['name'])

	# Create site for each row in the file
	for row in csv_data:
		# Ensure CSV Row contains 'Site Name', else skip to the next row
		if row['Site Name'] != '':
			# Ensure site doesn't already exist
			if row['Site Name'] not in existing_site_names:

				# Create Site Group, unless it already exists
				sitegroup_ids = []
				if 'Site Group' in row and row['Site Group'] != '':
					sitegroups = [x.strip() for x in row['Site Group'].split(',')]

					for sitegroup in sitegroups:
						if sitegroup == '':
							continue

						(found, sitegroup_id, existing_sitegroups) = get_sitegroup(session, sitegroup, existing_sitegroups)
						if found == False:
							print('Failed to get site group')

							continue

						if sitegroup_id != None:
							print('Found existing site group \'{}\' ({})'.format(sitegroup, sitegroup_id))

							sitegroup_ids.append(sitegroup_id)
						else:
							sitegroup_id = create_sitegroup(session, sitegroup)

							if sitegroup_id == None:
								print('Failed to create site group {}'.format(sitegroup))
							else:
								print('Created site group \'{}\' ({})'.format(sitegroup, sitegroup_id))

								sitegroup_ids.append(sitegroup_id)

							existing_sitegroups = get_sitegroups(session)

				# Get ID of RF Template if it exists
				rf_template_id = ''
				if 'RF Template' in row and row['RF Template'] != '':
					for template in existing_rf_templates:
						if template['name'] == row['RF Template']:
							rf_template_id = template['id']
						

				# Create Site
				## Construct the site object
				## Uses Google's Geocoding API to determine the address, timezone, country_code, and latlng
				## https://developers.google.com/maps/documentation/geocoding/start
				location = get_geocode(row['Address'])
				lat = location['results'][0]['geometry']['location']['lat']
				lng = location['results'][0]['geometry']['location']['lng']
				timezone = get_timezone('{}, {}'.format(lat, lng))['timeZoneId']
				site = {
					'country_code': row['Country'],
					'timezone': timezone,
					'address': row['Address'],
					'latlng': {  
						'lat': lat,
						'lng': lng
					},
					'name': row['Site Name'].strip(),
					'sitegroup_ids': list(set(sitegroup_ids)),
					'rftemplate_id': rf_template_id
				}

				site_id = create_site(session, site)
				if site_id == None:
					print('Failed to create site {}'.format(site['name']))

					continue
				else:
					print('Created site \'{}\' ({})'.format(site['name'], site_id))


				# Update Site Setting
				## Construct the site setting object
				site_setting = {
					'auto_upgrade': {
						"enabled": False
					},
					'rogue': {
						'min_rssi': -80,
						'enabled': True,
						'honeypot_enabled': True
					},
					"persist_config_on_device": True
				}
				result = update_site_setting(session, site_id, site_setting)
				if result:
					print('Updated site setting {} ({})'.format(site['name'], site_id))
				else:
					print('Failed to update site setting {} ({})'.format(site['name'], site_id))
			else:
				print('Site {} Exists, skipping'.format(row['Site Name']))
		else:
			print('Missing: Site Name')
		print()
	return

def move_aps():
	if api_token == '' or api_url == '':
		print('Missing variables:')
		print('api_token={}'.format(api_token))
		print('api_url={}'.format(api_url))

		sys.exit(1)

	# Create session
	session = requests.Session()

	# Convert sites.csv file to json
	csv_data = csv_to_json(assign_file)

	# Get Site IDs and names
	sites = get_sites(session)
	site_name_id = {}
	for site in sites:
		site_name_id[site['name']] = site['id']

	# Bundle all the device MACs per site
	site_macs = {}
	for row in csv_data:
		desired_site = row['Site Name']
		device_mac = row['MAC Address']

		if desired_site in site_name_id:
			desired_site_id = site_name_id[desired_site]
			if desired_site_id in site_macs:
				site_macs[desired_site_id].append(device_mac)
			else:
				site_macs[desired_site_id] = [device_mac]
	
	# Move the devices to each site
	for site in site_macs:

		inventory_setting = {
			"op": "assign",
			"site_id": site,
			"macs": site_macs[site],
			"no_reassign": False,
			"managed": True
		}

		result = move_device(session, inventory_setting)

		if result:
				print('Updated APs {} with site {}'.format(site_macs[site], site))
		else:
				print('Failed to update AP {} with site {}'.format(site_macs[site], site))

		# Name the device based on the CSV
		for row in csv_data:
			device_mac = row['MAC Address']
			device_name = row['Name']
			desired_site = row['Site Name']
			desired_site_id = site_name_id[desired_site]

			if site == desired_site_id:

				if re.search('switch', row['Type'], re.IGNORECASE):
					
					device_role = row['Switch Role']

					device_setting = {
							"name": device_name,
							"role": device_role
					}

				else:

					device_setting = {
						"name": device_name
					}

				result = update_device(session, device_setting, site, device_mac)

				if result:
					print('Updated device {} with name {}'.format(device_mac, device_name))
				else:
					print('Failed to update device {} with name {}'.format(device_mac, device_name))



# =====
# MAIN
# =====

if __name__ == '__main__':
	ans=True
	while ans:
		print ("""
		1.Add Sites
		2.Add Devices to Sites, Rename and assign Switch Role
		3.Exit/Quit
		""")

		ans=input("What would you like to do? ") 
		if ans=="1": 
			print("\n Adding Sites")
			add_sites()
		elif ans=="2":
			print("\n Adding Devices to Sites") 
			move_aps()
		elif ans=="3":
			print("\n Goodbye")
			sys.exit(0)
		elif ans !="":
			print("\n Not Valid Choice Try again") 

