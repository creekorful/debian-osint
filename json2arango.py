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


def transform_group(raw_groups: list) -> (list, dict):
    print("There is {} groups to process".format(len(raw_groups)))

    relations = {}
    groups = []
    for raw_group in raw_groups:
        # Base fields that are always present
        group = {
            '_id': raw_group['gid'][0],  # The name is used everywhere so it's easier than using the gid
            'name': raw_group['gid'][0],  # internal display name for Arango
            'gid': raw_group['gidNumber'][0]
        }

        # Optional fields
        if 'description' in raw_group:
            group['description'] = raw_group['description'][0]

        groups.append(group)

        # Relationship

    print("Groups processed!")

    return groups, relations


def transform_developer(raw_developers: list) -> (list, dict):
    print("There is {} developers to process".format(len(raw_developers)))

    relations = {}
    developers = []
    for raw_developer in raw_developers:
        # skip inactive account
        if 'accountStatus' in raw_developer and 'inactive' in raw_developer['accountStatus'][0]:
            continue

        # Base fields that are always present
        developer = {
            '_id': raw_developer['uid'][0],
            'name': raw_developer['uid'][0],  # internal display name for Arango
            'cn': raw_developer['cn'][0],
            'sn': raw_developer['sn'][0]
        }

        # Optional fields
        if 'keyFingerPrint' in raw_developer:
            developer['gpg_key'] = raw_developer['keyFingerPrint']
        if 'accountComment' in raw_developer:
            developer['comment'] = raw_developer['accountComment'][0]
        if 'accountStatus' in raw_developer:
            developer['status'] = raw_developer['accountStatus'][0]

        developers.append(developer)

        # Relationship
        if 'supplementaryGid' in raw_developer:
            for group in raw_developer['supplementaryGid']:
                relations["developers_{}/groups_{}".format(developer['_id'], group)] = {
                    '_from': "developers/{}".format(developer['_id']),
                    '_to': "groups/{}".format(group)
                }
        if 'allowedHost' in raw_developer:
            for server in raw_developer['allowedHost']:
                server = server.split(' ')[0]
                relations["developers_{}/servers_{}".format(developer['_id'], server)] = {
                    '_from': "developers/{}".format(developer['_id']),
                    '_to': "servers/{}".format(server)
                }

    print("Developers processed!")
    return developers, relations


def transform_server(raw_servers: list) -> (list, dict):
    print("There is {} servers to process".format(len(raw_servers)))

    relations = {}
    servers = []
    for raw_server in raw_servers:
        # Base fields that are always present
        server = {
            '_id': raw_server['hostname'][0],
            'name': raw_server['hostname'][0],  # internal display name for Arango
        }

        # Optional fields
        if 'distribution' in raw_server:
            server['distribution'] = raw_server['distribution'][0]
        if 'admin' in raw_server:
            server['admin'] = raw_server['admin'][0]
        if 'access' in raw_server:
            server['access'] = raw_server['access'][0]
        if 'purpose' in raw_server:
            server['purpose'] = raw_server['purpose'][0]
        if 'architecture' in raw_server:
            server['architecture'] = raw_server['architecture'][0]
        if 'sshRSAHostKey' in raw_server:
            server['ssh_keys'] = raw_server['sshRSAHostKey']
        if 'description' in raw_server:
            server['description'] = raw_server['description'][0]
        if 'ipHostNumber' in raw_server:
            server['ips'] = raw_server['ipHostNumber']
        if 'memory' in raw_server:
            server['memory'] = raw_server['memory']
        if 'disk' in raw_server:
            server['disks'] = raw_server['disk'][0]
        if 'sponsor' in raw_server:
            server['sponsors'] = raw_server['sponsor']

        servers.append(server)

        # Relationship
        if 'allowedGroups' in raw_server:
            for group in raw_server['allowedGroups']:
                relations["servers_{}/groups_{}".format(server['_id'], group)] = {
                    '_from': "servers/{}".format(server['_id']),
                    '_to': "groups/{}".format(group)
                }

    print("Servers processed!")
    return servers, relations


if __name__ == '__main__':
    transformers = [
        ('groups.json', transform_group),
        ('developers.json', transform_developer),
        ('servers.json', transform_server)
    ]

    all_relations = {}
    for file, func in transformers:
        # Read source json
        with open(os.path.join(sys.argv[1], file)) as src_file:
            raw_data = json.load(src_file)

        # Call the transformer function
        transformed_data, relations = func(raw_data)
        all_relations = all_relations | relations

        # Write transformed json
        with open(os.path.join(sys.argv[2], file), 'w+') as dst_file:
            json.dump(transformed_data, dst_file)

    # Write the relations
    print("There is {} relations".format(len(all_relations)))
    with open(os.path.join(sys.argv[2], "relations.json"), 'w+') as dst_file:
        json.dump(list(all_relations.values()), dst_file)
