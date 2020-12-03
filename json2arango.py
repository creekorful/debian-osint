#!/usr/bin/env python3

# This script is used to convert the 'raw' JSON files dumped from various sources (LDAP, etc...)
# into multiples json files ready-to-use for ArangoDB.
#
# The script will uses the following files to generate the ArangoDB collections / edges:
# - developers.json - the list of debian developers dumped using ldap2json
# - servers.json - the list of debian servers dumped using ldap2json
# - groups.json - the list of debian groups dumped using ldap2json
#
# example usage:
# - ./json2arango.py /tmp/json-files /tmp/arango-files
#
# where:
# - /tmp/json-files is the directory where the raw JSON files are.
# - /tmp/arango-files is the directory where the generated files will be placed

import os
import sys

import json


def transform_group(group_file: str) -> list:
    print("Transforming groups using file: {}".format(group_file))

    # read the json
    with open(group_file) as json_file:
        raw_groups = json.load(json_file)

    print("There is {} groups to proceed".format(len(raw_groups)))

    groups = []
    for raw_group in raw_groups:
        # Base fields that are always present
        group = {
            '_id': raw_group['gid'][0],  # The name is used everywhere so it's easier than using the gid
            'gid': raw_group['gidNumber'][0],
            'name': raw_group['gid'][0]
        }

        # Optional fields
        if 'description' in raw_group:
            group['description'] = raw_group['description'][0]

        groups.append(group)

    print("Groups processed!")

    return groups


if __name__ == '__main__':
    groups = transform_group(os.path.join(sys.argv[1], "groups.json"))

    with open(os.path.join(sys.argv[2], "groups.json"), 'w+') as outfile:
        json.dump(groups, outfile)
