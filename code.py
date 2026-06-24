#!/usr/bin/env python3

import datetime
import requests
import os
import json
import logging
import sys

'''
For more information, check out the 1Password support page:
https://support.1password.c
om/events-reporting


Events API Documentation: https://developer.1password.com/docs/events-api/reference/

** Setup this script as a scheduled task or Cronjob. If running on linux, stage the script in /root
and create/update the crontab for the root user **

'''

#SETTING LOGGING INFORMATION; WILL WRITE LOG FILE IN SAME DIRECTORY WHERE THIS SCRIPT RESIDES
logging.basicConfig(
	filename = "1PassIngestion_logs.log",
	format = '%(asctime)s - %(levelname)s - %(message)s',
	filemode = 'a'
)

#SETTING TIME MINUS 1H DELTA FOR API REQUESTS RESET CURSOR//
start_time = datetime.datetime.now() - datetime.timedelta(hours=1)

#SETTING REQUESTS DETAILS
api_token = os.environ.get("EVENTS_API_TOKEN")
url = "https://events.1password.com"
cursor = ""
if not api_token:
	logging.error("Please set the EVENTS_API_TOKEN environment variable.")
	exit(1)
headers = {
	"Content-Type": "application/json",
	"Authorization": f"Bearer {api_token}"
}

#ARRAY FOR API ENDPOINTS
api_endpoints = ['/api/v2/signinattempts', '/api/v2/auditevents', '/api/v2/itemusages']

#EMPTY ARRAY FOR LOGS FROM ECH API ENDPOINT
entries = []

try:
	#GET OPERATING SYSTEM AND SET LOG FILE & PATH ACCORDINGLY
	operating_system = sys.platform
	if operating_system == "win32":
		dir = "C:\\ProgramData\\1PassIngest\\"
	elif operating_system == "linux" or operating_system == "darwin":
		dir = f"/opt/1PassIngest/"
	if not os.path.isdir(dir):
		os.mkdir(dir)
	log_file = dir + "1PassLogs.log"

#GET LOGS FROM ALL API ENDPOINTS AND CHECK FOR OK RESPONSE
	for endpoint in api_endpoints:
		has_more = True
		payload = {
			"limit": 20,
			"start_time": start_time.astimezone().replace(microsecond=0).isoformat()
		}
		while has_more:
			r = requests.post(f"{url}{endpoint}", headers=headers, json=payload)
			r.raise_for_status() # Raise an exception if the request fails
			json_resp = r.json()
			has_more = json_resp.get("has_more", False) # default to False if key does not exist
			cursor = json_resp.get("cursor", "") # default to empty string if key does notexist
			items = json_resp.get("items", "") # default to empty string if key does not exist
			# delete keys that are not needed in the logs
			del json_resp["has_more"]
			del json_resp["cursor"]
			if len(items) != 0: # Only append the json_resp if the value of the items key is not empty.
				entries.append(json.dumps(items) + "\n")
			if has_more:
				payload = {
					"cursor": cursor
				}
	if len(entries) == 0:
		logging.info("No events found")
		exit(1)
	with open(log_file, 'a') as f:
		f.writelines(entries)
except requests.exceptions.RequestException as e:
	logging.error(f"Error in request to API: {e}")
except Exception as e:
	logging.error(f"Error writing logs to file. Error: {e}")