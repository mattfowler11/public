#!/usr/bin/python

''' 
Written by Matt Fowler (mattf@juniper.net).
Slack bot that interfaces with Mist API. Find a user/device. Create a PSK. Enable/disable a WxLAN policy.

'''

import os, time, re, json, requests, io, uuid, string, random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
requests.packages.urllib3.disable_warnings()
from PIL import Image
from slack_sdk.rtm_v2 import RTMClient
from mistconfig import *

# instantiate Slack client
rtm = RTMClient(token=SLACK_TOKEN)
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = 'fowler_bot'

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "find" or "Find"
BLOCK = "block"
UNBLOCK = "unblock"
PSK = "psk"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

class mist_find(object):

    def __init__(self, name, mist_token):
        self.name = name
        self.mist_api = mist_api
        self.org_id = org_id
        self.search_results = []
        self.mac_list = []
        self.detail_results = []
        self.map_data = {}
        self.mist_sites = mist_sites
        self.image_path = r"images/"
        self.buff = io.BytesIO()
        self.mac_and_image= {}

    def get_content(self, uri):
        # GET request to Mist based on the uri you provide.
        try:
          head = {'Authorization': 'token {}'.format(mist_token)}
          request = requests.get(url = self.mist_api+uri, headers = head, verify=False, timeout=2)
          return request.json()
        except requests.exceptions.RequestException as e:
          return "[]"

    def storeMemory(self, item):

        # Use cStringIO to write the item to memory.
        self.buff.write(item)

        # Go back to the start of the item.
        self.buff.seek(0)

        # Return the item we just stored.
        return self.buff.getvalue()


    def client_data(self):
        # Gets detailed client data for each MAC address with the hostname
        print(self.get_content(self.mist_sites))
        for site in self.get_content(self.mist_sites):
            site_id = site["id"]
            mist_client_search = "/api/v1/sites/"+ site_id +"/clients/search?username="+ self.name
            self.search_results.append(self.get_content(mist_client_search))

        for site in self.search_results:
            for result in site['results']:
                self.mac_list.append(result['mac'])

        print(self.mac_list)
        print(site_id)
        # overwrite until multi-site support
        site_id = home_site
        print(site_id)

        for mac in self.mac_list:
            mist_client_details = "/api/v1/sites/"+ site_id +"/stats/clients/"+ mac
            self.detail_results.append(self.get_content(mist_client_details))
        
        print(self.detail_results)
        self.detail_results[:] = [x for x in self.detail_results if 'hostname' in x]

        return self.detail_results[:]

    def maps(self):
        for host in self.detail_results:
            site_id = host["site_id"]
            map_id = host["map_id"]
            mist_map = "/api/v1/sites/"+ site_id +"/maps/"+ map_id
            self.map_data[host['mac']] = self.get_content(mist_map)
        return self.map_data

    def image(self):
        for mac in self.map_data:
            self.buff.seek(0)
            url = self.map_data[mac]['url']
            print(url)
            m = re.search('maps\\/(.+?)\\?', url)
            if m:
                found = m.group(1)
            if os.path.isfile(self.image_path + found) == True:
                file = self.image_path + found
                fh = open(file, "rb")
                image = self.storeMemory(fh.read()).strip()
                fh.close()
            else:
                image = requests.get(url = url, verify=False, timeout=2).content
                file = self.image_path + found
                fh = open(file, "wb")
                fh.write(image)
                fh.close()
                fh = open(file, "rb")
                image = self.storeMemory(fh.read()).strip()

            im = plt.imread(io.BytesIO(image), format='png')
    
            # Some images were showing red like http://stackoverflow.com/questions/21641822/ and this seems to fix it.
            convertedim=Image.open(io.BytesIO(image)).convert('P')

            # Draw a plot over the image that is the same size as the image.
            implot = plt.imshow(im, extent=[0, int(self.map_data[mac]['width']), 0, int(self.map_data[mac]['height'])], origin='lower', aspect=1)

            for host in self.detail_results:
                if host['mac'] == mac:
                    client_x = int(host['x'])
                    client_y = int(host['y'])

            print (client_x)
            print (client_y)
            print (self.map_data[mac]['height'])
            print (self.map_data[mac]['width'])

            # Mark the client's coordinates that we received from Mist. 
            # The first line will draw a dot at the x,y location and the second and third lines will draw circles around it.
            plt.scatter(client_x, client_y, facecolor='r', edgecolor='r')
            plt.scatter(client_x, client_y, s=1000, facecolors='none', edgecolor='r')
            plt.scatter(client_x, client_y, s=2000, facecolors='none', edgecolor='r')
            plt.scatter(client_x, client_y, s=3500, facecolors='none', edgecolor='r')

            plt.xlim(0,int(self.map_data[mac]['width']))
            plt.ylim(0,int(self.map_data[mac]['height']))

            # Currently the plot is the same size as the image, but the scale is off so we need to correct that.
            #ax = plt.gca()
            plt.gca().set_ylim([0,int(self.map_data[mac]['height'])])
            plt.gca().set_xlim([0,int(self.map_data[mac]['width'])])

            # The plot starts 0,0 from the bottom left corner but Mist uses the top left. 
            # So, we need to invert the y-axis and, to make it easier to read, move the x axis markings to the top (if you choose to show them).
            plt.gca().set_ylim(plt.gca().get_ylim()[::-1])
            plt.gca().xaxis.tick_top()
            plt.gca().grid(True,linestyle='-')

            # Use this to decide whether you want to show or hide the axis markings.
            plt.axis('off')

            # Save our new image with the plot overlayed to memory. The dpi option here makes the image larger.
            plt.savefig(self.buff, format='png', dpi=500)

            # Get the new image.
            newimage = self.buff.getvalue().strip()
            self.buff.seek(0)
            file = self.image_path + str(uuid.uuid4()) +".png"
            fh = open(file, "wb")
            fh.write(newimage)
            fh.close()
            plt.gcf().clear()

            self.mac_and_image[mac] = file

        return self.mac_and_image

def password_generator(size=8, chars=string.ascii_letters + string.digits):
    """
    Returns a string of random characters, useful in generating temporary
    passwords for automated password resets.
    
    size: default=8; override to provide smaller/larger passwords
    chars: default=A-Za-z0-9; override to provide more/less diversity
    
    Credit: Ignacio Vasquez-Abrams
    Source: http://stackoverflow.com/a/2257449
    """
    return ''.join(random.choice(chars) for i in range(size))

def get_content(uri, api):
    # GET request to Mist based on the uri you provide.
    try:
        head = {'Authorization': 'token {}'.format(mist_token)}
        request = requests.get(url = api+uri, headers = head, verify=False, timeout=2)
        return request.json()
    except requests.exceptions.RequestException as e:
        return "[]"

def post_content(uri, payload, api):
    # GET request to Mist based on the uri you provide.
    try:
        head = {'Authorization': 'token {}'.format(mist_token)}
        request = requests.post(url = api+uri, headers = head, json = payload, verify=False, timeout=2)
        return request.json()
    except requests.exceptions.RequestException as e:
        return "[]"

def wxlan_api(room, token, action, mist_sites, mist_api):
    for site in get_content(mist_sites, mist_api):
        site_id = site["id"]
        check_tag = get_content("/api/v1/sites/"+ site_id +"/wxtags", mist_api)
        for i in check_tag:
            print (i['name'])
            print (i['match'])
            if i['name'] == room and i['match'] == 'ap_id':
                check_rule = get_content("/api/v1/sites/"+ site_id +"/wxrules", mist_api)
                print (check_rule)
                for r in check_rule:
                    if 'name' in r and r['name'] == room:
                        if action == BLOCK:
                            if r['enabled'] == False:
                                payload = {'enabled': True}
                                uri = "/api/v1/sites/"+ site_id +"/wxrules/"+ r['id']
                                post = post_content(uri, payload, mist_api)
                                if post['enabled'] == True:
                                    wxlanresult = "Social media is now blocked for room "+ room
                                else:
                                    wxlanresult = "Something went wrong error:1"
                            elif r['enabled'] == True:
                                wxlanresult = "Social media is already being blocked for room "+ room
                        elif action == UNBLOCK:
                            if r['enabled'] == True:
                                payload = {'enabled': False}
                                uri = "/api/v1/sites/"+ site_id +"/wxrules/"+ r['id']
                                post = post_content(uri, payload, mist_api)
                                if post['enabled'] == False:
                                    wxlanresult = "Social media is now unblocked for room "+ room
                                else:
                                    wxlanresult = "Something went wrong error:2"
                            elif r['enabled'] == False:
                                wxlanresult = "Social media is already unblocked for room "+ room
                    else:
                        if action == BLOCK:
                            payload = {
                                "name": room,
                                "order": 1,
                                "src_wxtags": [i['id]']],
                                "dst_allow_wxtags": [],
                                "dst_deny_wxtags": [],
                                "blocked_apps": ["all-social"],
                                "action": "block",
                                "enabled": True
                                }
                            uri = "/api/v1/sites/"+ site_id +"/wxrules"
                            post = post_content(uri, payload, mist_api)
                            if post['enabled'] == True:
                                wxlanresult = "Social media is now blocked for room "+ room
                            else:
                                wxlanresult = "Something went wrong error:3" 

                        elif action == UNBLOCK:
                            payload = {
                                "name": room,
                                "order": 1,
                                "src_wxtags": [i['id]']],
                                "dst_allow_wxtags": [],
                                "dst_deny_wxtags": [],
                                "blocked_apps": ["all-social"],
                                "action": "block",
                                "enabled": False
                                }
                            uri = "/api/v1/sites/"+ site_id +"/wxrules"
                            post = post_content(uri, payload, mist_api)
                            if post['enabled'] == False:
                                wxlanresult = "Social media is now unblocked for room "+ room
                            else:
                                wxlanresult = "Something went wrong error:3"
                        
            else:
                wxlanresult = "Sorry, "+ room +" does not exist. Please check it is correct and try again."

    return wxlanresult

def psk(site_name, name, mist_token, mist_sites, mist_api):
    for site in get_content(mist_sites, mist_api):
        print(site_name) 
        print(name)
        print(site['name'])
        if site['name'] == site_name:
            payload = {
                "name": name,
                "passphrase": password_generator(),
                "ssid": psk_ssid,
                "usage": "multiple",
                }
            uri = "/api/v1/sites/"+ site['id'] +"/psks"
            print(payload)
            post = post_content(uri, payload, mist_api)
            print(post)
            result = "Done. The password for "+ post['name'] +" at "+ site['name'] +" is "+ post['passphrase'] +"."
            return result
        else:
            result = "Sorry, the site you entered does not exist. Please check the spelling and use the format <psk site name>"
            return result

def parse_bot_commands(event):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    if event["type"] == "message" and not "subtype" in event:
        user_id, message = parse_direct_mention(event["text"])
        if user_id == starterbot_id:
            return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)
 

if __name__ == "__main__":
    starterbot_id = rtm.web_client.auth_test()["user_id"]
    print("Connected as {}".format(starterbot_id))
    @rtm.on("message")
    def handle(client: RTMClient, event: dict):
        print("Message received.")
        print(event['text'])
        """
            Executes bot command if the command is known
        """
        # Default response is help text for the user
        default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)
        command = event['text']
        channel = event['channel']
        # Finds and executes the given command, filling in response
        response = None
        # This is where you start to implement more commands!

        try:
                command, channel = parse_bot_commands(event)
                if command:
                
                    if command.startswith(EXAMPLE_COMMAND): 
                        query = mist_find(command.split(EXAMPLE_COMMAND+" ",1)[1], mist_token)
                        client_data = query.client_data()
                        maps = query.maps()
                        location = query.image()
                        client_count = len(client_data)
                        hostnames = ''
                        for i in client_data:
                            hostnames = hostnames +'\n'+ i['hostname']
                        if client_count == 0:
                            response = str(client_count) +' client(s) found matching your query.\n'+ hostnames +"\n\nPlease try again."
                        else:
                            response = str(client_count) +' client(s) found matching your query.\n'+ hostnames +"\n\nI'll be back with their location shortly."

                        # Sends the response back to the channel
                        client.web_client.chat_postMessage(
                            channel=channel,text=response or default_response
                        )

                        for i in client_data:
                            for k in location:
                                if k == i['mac']:
                                    print (location[k])
                                    print (i['hostname'])
                                    with open(location[k], "rb") as file_content:
                                        client.web_client.files_upload(
                                            channels=channel,file=file_content,title=i['hostname']
                                        )
                                    os.remove(location[k])
                    elif command.startswith(BLOCK):
                        response = wxlan_api(command.split(BLOCK+" ",1)[1], mist_token, BLOCK, mist_sites, mist_api)
                        client.web_client.chat_postMessage(
                            channel=channel,text=response or default_response
                        )

                    elif command.startswith(UNBLOCK):
                        response = wxlan_api(command.split(BLOCK+" ",1)[1], mist_token, UNBLOCK, mist_sites, mist_api)
                        client.web_client.chat_postMessage(
                            channel=channel,text=response or default_response
                        )

                    elif command.startswith(PSK):
                        split_command = command.split(" ")
                        response = psk(split_command[1], split_command[2], mist_token, mist_sites, mist_api)
                        client.web_client.chat_postMessage(
                            channel=channel,text=response or default_response
                        )


                    else:
                        # Sends the response back to the channel
                        client.web_client.chat_postMessage(
                            channel=channel,text=response or default_response
                        )

                time.sleep(RTM_READ_DELAY)
        except Exception as e:
            print(e)
            time.sleep(RTM_READ_DELAY)

    rtm.start()
    
