#!/usr/bin/env python3

# This script is used to dump all existing Debian packages
# into a json file for further analysis.
#
# This allows to keep a local cache of the Debian packages and allow work with local data
# instead of spamming for results.
# Therefore this script does NOT transform the received data.
#
# This script need to be run on a Debian (unstable) machine, it works by dumping out the content of the DPKG database.
# See: /var/lib/dpkg/available
#
# Please note that you'll need to run sync-available(8) as root on your computer before running this script,
# in order to update the DPKG available database with the data in the APT database.

import sys
from email.parser import Parser
from typing import List

import json

if __name__ == '__main__':
    file = '/var/lib/dpkg/available'

    # Read raw packages from dpkg database
    # and group their definition
    raw_packages: List[str] = []
    with open(file, 'r') as file:
        current_package = ''
        for raw_package in file.readlines():
            # new package definition
            if len(raw_package.strip()) == 0:
                raw_packages.append(current_package.rstrip('\n'))
                current_package = ''
            else:
                current_package += raw_package

    # Parse the raw definition (RFC822) using email module
    packages = []
    p = Parser()
    for raw_package in raw_packages:
        m = p.parsestr(raw_package, headersonly=True)

        package = {}
        for key, value in m.items():
            package[key.lower()] = value

        # special cases with multiples values (comma separated)
        for key in ['depends', 'replaces', 'breaks', 'tag', 'conflicts', 'suggests', 'recommends']:
            if key in package:
                package[key] = package[key].replace(', ', ',').split(',')

        packages.append(package)

    with open(sys.argv[1], 'w+') as outfile:
        json.dump(packages, outfile)
    print("successfully retrieved {} packages".format(len(packages)))
