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
    relations = {}
    groups = []
    for raw_group in raw_groups:
        # Base fields that are always present
        group = {
            '_key': raw_group['gid'][0],  # The name is used everywhere so it's easier than using the gid
            'name': raw_group['gid'][0],  # internal display name for Arango
            'gid': raw_group['gidNumber'][0]
        }

        # Optional fields
        if 'description' in raw_group:
            group['description'] = raw_group['description'][0]

        groups.append(group)

        # Relationship

    print("{} groups processed!".format(len(groups)))

    return groups, relations


def transform_developer(raw_developers: list) -> (list, dict):
    relations = {}
    developers = []
    for raw_developer in raw_developers:
        # skip inactive account
        if 'accountStatus' in raw_developer:
            is_active = True
            for inactive_status in ['inactive', 'retiring', 'memorial']:
                if inactive_status in raw_developer['accountStatus'][0]:
                    is_active = False
                    break

            if not is_active:
                continue

        # Base fields that are always present
        developer = {
            '_key': raw_developer['uid'][0],
            'name': raw_developer['uid'][0],  # internal display name for Arango
            'cn': raw_developer['cn'][0],
            'sn': raw_developer['sn'][0]
        }

        # Optional fields
        if 'accountComment' in raw_developer:
            developer['comment'] = raw_developer['accountComment'][0]
        if 'accountStatus' in raw_developer:
            developer['status'] = raw_developer['accountStatus'][0]

        developers.append(developer)

        # Relationship
        if 'supplementaryGid' in raw_developer:
            for raw_group in raw_developer['supplementaryGid']:
                relations["developers_{}/groups_{}".format(developer['_key'], raw_group)] = {
                    '_from': "developers/{}".format(developer['_key']),
                    '_to': "groups/{}".format(raw_group)
                }
        if 'allowedHost' in raw_developer:
            for raw_server in raw_developer['allowedHost']:
                server = raw_server.split(' ')[0]
                relations["developers_{}/servers_{}".format(developer['_key'], server)] = {
                    '_from': "developers/{}".format(developer['_key']),
                    '_to': "servers/{}".format(server)
                }
        if 'keyFingerPrint' in raw_developer:
            for raw_key in raw_developer['keyFingerPrint']:
                relations["developers_{}/gpg_keys_{}".format(developer['_key'], raw_key)] = {
                    '_from': "developers/{}".format(developer['_key']),
                    '_to': "gpg_keys/{}".format(raw_key)
                }

    print("{} developers processed!".format(len(developers)))
    return developers, relations


def transform_server(raw_servers: list) -> (list, dict):
    relations = {}
    servers = []
    for raw_server in raw_servers:
        # Base fields that are always present
        server = {
            '_key': raw_server['hostname'][0],
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
            for raw_group in raw_server['allowedGroups']:
                relations["groups_{}/servers_{}".format(raw_group, server['_key'])] = {
                    '_from': "groups/{}".format(raw_group),
                    '_to': "servers/{}".format(server['_key'])
                }

    print("{} servers processed!".format(len(servers)))
    return servers, relations


def transform_gpg_key(raw_developers: list) -> (list, dict):
    relations = {}
    keys = []
    for raw_developer in raw_developers:
        if 'keyFingerPrint' in raw_developer:
            for raw_key in raw_developer['keyFingerPrint']:
                key = {
                    '_key': raw_key,
                    'name': raw_key,  # internal display name for Arango
                }
                keys.append(key)

    print("{} keys processed!".format(len(keys)))
    return keys, relations


if __name__ == '__main__':
    transformers = [
        ('groups.json', [('groups.json', transform_group)]),
        ('developers.json', [('developers.json', transform_developer), ('gpg-keys.json', transform_gpg_key)]),
        ('servers.json', [('servers.json', transform_server)])
    ]

    all_relations = {}
    for src_file, transformer in transformers:
        # Read source json
        with open(os.path.join(sys.argv[1], src_file)) as src:
            raw_data = json.load(src)

        # Call the transformer functions
        for dst_file, func in transformer:
            transformed_data, relations = func(raw_data)
            all_relations = all_relations | relations

            # Write transformed json
            with open(os.path.join(sys.argv[2], dst_file), 'w+') as dst:
                json.dump(transformed_data, dst)

    # Write the relations
    print("There is {} relations".format(len(all_relations)))
    with open(os.path.join(sys.argv[2], "relations.json"), 'w+') as dst_file:
        json.dump(list(all_relations.values()), dst_file)
