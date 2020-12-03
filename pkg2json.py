#!/usr/bin/env python3

# This script is used to dump all existing Debian packages
# into a json file for further analysis.
#
# This allows to keep a local cache of the Debian packages and allow work with local data
# instead of spamming the server for results.
# Therefore this script does NOT transform the received data.
#
# See: https://packages.debian.org/unstable/allpackages?format=txt.gz

import gzip
import urllib.request

import json

if __name__ == '__main__':
    url = 'https://packages.debian.org/unstable/allpackages?format=txt.gz'
    packages = []
    with urllib.request.urlopen(url) as response:
        with gzip.GzipFile(fileobj=response) as uncompressed:
            raw_packages = uncompressed.readlines()
            for raw_package in raw_packages:
                parts = raw_package.decode('utf-8').strip('\n').split(' ')
                if len(parts) == 0 or (len(parts) == 1 and parts[0] == ''):
                    continue

                package = {
                    'name': parts[0],
                }

                # TODO: improve
                if '(' in parts[1] and ')' in parts[1]:
                    package['version'] = parts[1].replace('(', '').replace(')', '')

                packages.append(package)

    with open('packages.json', 'w+') as outfile:
        json.dump(packages, outfile)
    print("successfully retrieved {} packages".format(len(packages)))
