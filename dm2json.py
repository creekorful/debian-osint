#!/usr/bin/env python3

# This script is used to dump all DM permissions
# into a json file for further analysis.
#
# See: https://ftp-master.debian.org/dm.txt
import sys
import urllib.request

import json

if __name__ == '__main__':
    url = 'https://ftp-master.debian.org/dm.txt'

    entries = []
    with urllib.request.urlopen(url) as response:
        lines = response.read().decode('utf-8')

        current = {}
        for line in lines.split('\n'):
            line = line.strip()
            parts = line.split(' ')

            if len(parts) == 0 or (len(parts) == 1 and parts[0] == ''):
                continue

            if parts[0] == 'Fingerprint:':
                if 'fingerprint' in current:
                    # entry fully processed
                    entries.append(current)
                    current = {}
                current['fingerprint'] = parts[1]
            elif parts[0] == 'Uid:':
                current['uid'] = line.replace('Uid: ', '')
            else:
                if 'allow' not in current:
                    current['allow'] = []

                if parts[0] == 'Allow:':
                    parts.pop(0)
                current['allow'].append({
                    'name': parts[0],
                    'giver': parts[1].replace('(', '').replace(')', '').replace(',', '')
                })

    with open(sys.argv[1], 'w+') as outfile:
        json.dump(entries, outfile)
    print("successfully retrieved {} permissions".format(len(entries)))
