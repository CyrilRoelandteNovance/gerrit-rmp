#!/usr/bin/env python3

# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Author: Cyril Roelandt <cyril@redhat.com>

import configparser
import json
import sys

import requests
from requests.auth import HTTPDigestAuth


def add_reviewer(change, reviewer, base_url, credentials, verify_ssl=True):
    url = base_url + '/a/changes/' + change['id'] + '/reviewers'
    data = {
        "reviewer": reviewer
    }
    username, password = credentials
    r = requests.post(url, auth=HTTPDigestAuth(username, password),
                      data=data, verify=verify_ssl)
    assert r.status_code == requests.codes.ok


def main():
    if len(sys.argv) != 3:
        print("Usage: add_reviewers.py config_file remote")
        print("See the README file for more info.")
        sys.exit(1)

    config_file = sys.argv[1]
    remote = sys.argv[2]
    cp = configparser.ConfigParser()
    cp.read(config_file)

    base_url = cp[remote]['url']
    url = '%s/changes/?q=status:open+owner:%s' % (
            cp[remote]['url'], cp[remote]['user'])
    verify_ssl = cp[remote].getboolean('verify_ssl', fallback=False)

    headers = {
        'Accept': 'application/json, text/javascript, */*'
    }
    r = requests.get(url, headers=headers, verify=verify_ssl)
    assert r.status_code == requests.codes.ok

    changes = json.loads('\n'.join(r.text.split('\n')[1:]))
    selected_change = None
    while True:
        print('[ Id] Patch name')
        print('--------------------')
        for i, change in enumerate(changes):
            print("[%3d] %s" % (i, change['subject']))
        print("Type an id to select a patch, or 'q' to quit.")
        try:
            choice = input()
            if choice == 'q':
                sys.exit(0)
            selected_change = changes[int(choice)]
            break
        except TypeError:
            print("You must enter an integer")
        except (IndexError, ValueError):
            print("Invalid choice")

    print("Selected: %s" % selected_change['subject'])
    try:
        project = cp[remote+':'+selected_change['project']]
        reviewers = project['reviewers'].split()
    except KeyError:
        print('Could not find reviewers for %s' % selected_change['project'])
        sys.exit(1)

    credentials = (cp[remote]['user'], cp[remote]['password'])
    for reviewer in reviewers:
        print("Adding reviewer %s" % reviewer)
        add_reviewer(selected_change, reviewer, base_url, credentials)


if __name__ == '__main__':
    main()
