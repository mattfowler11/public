#!/usr/bin/python

# Configuration file to set global variables


api_token = '' # Add your Mist API Token in the quotes
google_api = '' # Add your Google token - see https://developers.google.com/maps/documentation/geocoding/start

# To get Org ID and Site ID, go to the Live View and look at the URL ie: https://manage.mist.com/admin/?org_id={org_id}#!cliLocation/view/{floorplan_id}/{site_id}
org_id = '' # Add your Org ID in the quotes

# Select the environment by uncommenting your respective cloud.
#api_url = 'https://api.mist.com/api/v1' # Global01
api_url = 'https://api.gc1.mist.com/api/v1' # Global02
#api_url = 'https://api.ac2.mist.com/api/v1' # Global03
#api_url = 'https://api.gc2.mist.com/api/v1' # Global04
#api_url = 'https://api.eu.mist.com/api/v1' # Europe

headers = {
	'Content-Type': 'application/json; charset=utf-8', 'Accept-Encoding': 'gzip, deflate',
	'Authorization': 'Token ' + api_token
}