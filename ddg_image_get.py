#!/usr/bin/env python3
"""
ddg_image_get.py
Duckduckgo image download module for TruFetch
Based on https://github.com/joeyism/duckduckgo-images-api
which was forked from
https://github.com/deepanprabhu/duckduckgo-images-api
"""

import sys
import os
import requests
import re
import json
import time # Used for sleep
import datetime
import shutil
from datetime import date # Used for timestamp
from python_settings import settings
from typing import Dict
sys.path.insert(0, settings.TF_HOME + '/lib')
from TruFetch import get_random_line



tf_home = settings.TF_HOME
# Set these to your liking. -jfadams1963
PAGES = 1
IMAGES = 50

terms = sys.argv[1]
if len(sys.argv) != 2:
    print('Useage:')
    print('ddg_image_get.py <terms>')
    sys.exit(0)


def search(keywords: str, max_results=None) -> Dict:
    url = 'https://duckduckgo.com/'
    params = {'q': keywords}

    with open(tf_home + 'lists/user_agents.txt') as f:
        user_agent = get_random_line(f)[:-2]

    hdrs = {'user-agent': user_agent}

    print('Hitting DuckDuckGo for Token')

    # First make a request to above URL, and parse out the 'vqd'
    # This is a special token, which should be used in the subsequent request
    res = requests.post(url, data=params, headers=hdrs)
    searchObj = re.search(r'vqd=([\d-]+)\&', res.text, re.M|re.I)

    if not searchObj:
        print('Token Parsing Failed')
        return -1
    #print('Obtained Token')

    # Let's use random user-agents for fun. -jfadams1963
    with open(tf_home + 'lists/user_agents.txt') as f:
        user_agent = get_random_line(f)[:-2]

    headers = {
        'authority': 'duckduckgo.com',
        'accept': 'application/json, text/javascript, */* q=0.01',
        'sec-fetch-dest': 'empty',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': user_agent,
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': 'https://duckduckgo.com/',
        'accept-language': 'en-US,enq=0.9',
    }

    params = (
        ('l', 'us-en'),
        ('o', 'json'),
        ('q', keywords),
        ('vqd', searchObj.group(1)),
        ('f', ',,,'),
        ('p', '1'),
        ('v7exp', 'a'),
    )

    requestUrl = url + "i.js"

    #print('Hitting Url :', requestUrl)
    results = []
    while True:
        while True:
            try:
                res = requests.get(requestUrl, headers=headers, params=params)
                data = json.loads(res.text)
                break
            except ValueError as e:
                print('Hitting Url Failure - Sleep and Retry:', requestUrl)
                time.sleep(5)
                continue
        #print('Hitting Url Success :', requestUrl)

        # This fix by https://github.com/peterwilli to accumulate. -jfadams1963
        results += data["results"]
        #### Might be needed again if the DDG layout changes. -jfadams1963
        #print(json.dumps(results, indent=2, sort_keys=True))
        #sys.exit()
        ####

        # These fixes by https://github.com/peterwilli
        # to fix broken max_results and return a Dict object. -jfadams1963
        if "next" not in data:
            print('No Next Page - Exiting')
            return { 'results': results }

        if max_results is not None and len(results) >= max_results:
            #print('Hit max results - Exiting')
            return { 'results': results }
            
        requestUrl = url + data["next"]
# End search


def print_image_URLs(obj):
    """
    This will print a list of the URLs for testing.
    But what we will do is download them all into a dir.
    -jfadams1963
    """
    print([r["image"] for r in obj["results"]])


def download_images(obj: list, imgcnt: int):
    """
    Download and save each image from URLs in results object
    """
    # We need to create a unique dload dir.
    # We'll timestamp it, replacing colons with dashes. -jfadams1963
    tstamp =  datetime.datetime.now().replace(microsecond=0).isoformat().replace(':','-')
    dir = './ddg_images' + tstamp

    if not os.path.exists(dir):
        os.makedirs(dir)
    dir = dir + "/"
    print("Created Directory:", dir)

    # Randomized user-agents might not be needed. I don't think that will be an
    # issue with DDG. It's still fun to to though! -jfadams1963
    for r in obj['results']:
        if imgcnt == 0:
            break
        with open(tf_home + 'lists/user_agents.txt') as f:
            user_agent = get_random_line(f)[:-2]

        hdrs = {'user-agent': user_agent}
        iurl = r['image']
        image_name = iurl.split('/')[-1]
        #### For testing. -jfadams1963
        #print(iurl)
        #print(image_name)
        #sys.exit()
        ####

        file_name = dir + image_name
        #print('Full path image name:', file_name)
        img = requests.get(iurl,
                           headers = hdrs,
                           stream = True,
                           timeout = 5)

        # Sometimes the filenames are too long.
        try:
            with open(file_name,'wb') as f:
                shutil.copyfileobj(img.raw, f) 
        except OSError as e:
            print(e)
            continue

        saved = os.path.isfile(file_name)
        if saved:
            print(">>>> ",saved)
            print('Image sucessfully Downloaded: ',file_name)
        else:
            print('Image Couldn\'t be retrieved')

        # Decriment image count
        imgcnt -= 1
# End download_images


def main():
    res = search(terms, max_results=PAGES)
    #print_image_URLs(res) # These all look good
    download_images(res, IMAGES)
# End main

if __name__ == "__main__":
    main()

