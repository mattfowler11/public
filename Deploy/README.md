
## About The Project

This Mist deployment script has 2 main capabilities:

1. Add Sites
2. Add Devices to Sites, Rename, and assign Switch Role

Sites are added based on the configuration in sites.csv
<br>
Devices (APs, Switches and WAN Edges) are added to sites based on assign_file.csv


### Requirements

1. Python modules - re, sys, requests, csv, json, time
2. Google Geocoding API token - https://developers.google.com/maps/documentation/geocoding/start
3. Mist API token - https://api-class.mist.com/rest/create/api_tokens/
4. Mist Org ID - https://www.mist.com/documentation/find-org-site-id/

### Setup

Ensure assign_file.csv, config.py, mist-deploy.py and sites.csv are all in the same directory.

In the config.py file add the following:

1. Mist API token
   ```py
   api_token = '' # Add your Mist API Token in the quotes
   ```
2. Google Geocoding token
   ```py
   google_api = '' # Add your Google token - see https://developers.google.com/maps/documentation/geocoding/start
   ```
3. Mist Org ID
   ```py
   org_id = '' # Add your Org ID in the quotes
   ```
4. Select the Mist cloud environment that your Org belongs to
   ```py
    # Select the environment by uncommenting your respective cloud.
    #api_url = 'https://api.mist.com/api/v1' # Global01
    api_url = 'https://api.gc1.mist.com/api/v1' # Global02
    #api_url = 'https://api.ac2.mist.com/api/v1' # Global03
    #api_url = 'https://api.gc2.mist.com/api/v1' # Global04
    #api_url = 'https://api.eu.mist.com/api/v1' # Europe
   ```

In sites.csv follow the format:
```csv
Site Name,Site Group,Address,Country,RF Template
Site A,Offices,123 Test St Sydney Australia,AU,TestRFTemplate
```
Note: 'Country' should be set based on the 2-letter code for the country in https://api.gc1.mist.com/api/v1/const/countries (this is for Global02 - change the URL for your cloud environment - see step 4 above for the URLs)

In assign_file.csv follow the format:
```csv
Site Name,MAC Address,Name,Type,Switch Role
Site A,112233445566,TestDevice,Switch,access_switch
```

### Usage

Run mist-deploy.py and follow the on-screen prompts.

```sh
python3 mist-deploy.py


    1.Add Sites
    2.Add Devices to Sites, Rename and assign Switch Role
    3.Exit/Quit

What would you like to do?
```