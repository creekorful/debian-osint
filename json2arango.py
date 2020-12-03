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


def transform_group(raw_groups: list) -> list:
    print("There is {} groups to process".format(len(raw_groups)))

    groups = []
    for raw_group in raw_groups:
        # Base fields that are always present
        group = {
            '_id': raw_group['gid'][0],  # The name is used everywhere so it's easier than using the gid
            'gid': raw_group['gidNumber'][0],
            'name': raw_group['gid'][0]  # internal display name for Arango
        }

        # Optional fields
        if 'description' in raw_group:
            group['description'] = raw_group['description'][0]

        groups.append(group)

    print("Groups processed!")

    return groups


def transform_developer(raw_developers: list) -> list:
    print("There is {} developers to process".format(len(raw_developers)))

    developers = []
    for raw_developer in raw_developers:
        # Base fields that are always present
        developer = {
            '_id': raw_developer['uid'][0],
            'cn': raw_developer['cn'][0],
            'sn': raw_developer['sn'][0],
            'name': raw_developer['uid'][0]  # internal display name for Arango
        }

        # Optional fields
        if 'keyFingerPrint' in raw_developer:
            developer['gpg_key'] = raw_developer['keyFingerPrint']

        developers.append(developer)

    print("Developers processed!")
    return developers


if __name__ == '__main__':
    transformers = [
        ('groups.json', transform_group),
        ('developers.json', transform_developer)
    ]

    for file, func in transformers:
        # Read source json
        with open(os.path.join(sys.argv[1], file)) as src_file:
            raw_data = json.load(src_file)

        # Call the transformer function
        transformed_data = func(raw_data)

        # Write transformed json
        with open(os.path.join(sys.argv[2], file), 'w+') as dst_file:
            json.dump(transformed_data, dst_file)
