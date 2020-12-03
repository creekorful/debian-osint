#!/usr/bin/env python3

# This script is used to convert the 'raw' JSON files dumped from various sources (LDAP, etc...)
# into multiples json files ready-to-use for ArangoDB.
#
# The script will uses the following files to generate the ArangoDB collections / edges:
# - developers.json - the list of debian developers dumped using ldap2json
# - servers.json - the list of debian servers dumped using ldap2json
# - groups.json - the list of debian groups dumped using ldap2json
# - packages.json - the list of debian packages dumped using pkg2json
# - dm-permissions.json - the list of debian DM permissions dumped using dm2json
#
# example usage:
# - ./json2arango.py /tmp/json-files /tmp/arango-files
#
# where:
# - /tmp/json-files is the directory where the raw JSON files are.
# - /tmp/arango-files is the directory where the generated files will be placed

import hashlib
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
                    '_to': "groups/{}".format(raw_group),
                    'kind': 'Is member of'
                }
        if 'allowedHost' in raw_developer:
            for raw_server in raw_developer['allowedHost']:
                server = raw_server.split(' ')[0]
                relations["developers_{}/servers_{}".format(developer['_key'], server)] = {
                    '_from': "developers/{}".format(developer['_key']),
                    '_to': "servers/{}".format(server),
                    'kind': 'Can access'
                }
        if 'keyFingerPrint' in raw_developer:
            for raw_key in raw_developer['keyFingerPrint']:
                relations["developers_{}/gpg-keys_{}".format(developer['_key'], raw_key)] = {
                    '_from': "developers/{}".format(developer['_key']),
                    '_to': "gpg-keys/{}".format(raw_key),
                    'kind': 'Has key'
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
                    '_to': "servers/{}".format(server['_key']),
                    'kind': 'Can access'
                }

    print("{} servers processed!".format(len(servers)))
    return servers, relations


def transform_user_gpg_key(raw_developers: list) -> (list, dict):
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


def transform_server_ssh_key(raw_servers: list) -> (list, dict):
    relations = {}
    keys = []
    for raw_server in raw_servers:
        if 'sshRSAHostKey' in raw_server:
            for raw_key in raw_server['sshRSAHostKey']:
                parts = raw_key.strip().split(' ')
                if len(parts) >= 3:
                    # hash key fingerprint using SHA-256 (cannot use key fingerprint as document key)
                    key_id = hashlib.sha256(parts[1].encode('utf-8')).hexdigest()

                    key = {
                        '_key': key_id,
                        'name': parts[2],  # internal display name for Arango
                        'kind': parts[0],
                        'fingerprint': parts[1],
                    }

                    if len(parts) == 4:
                        key['comment'] = parts[3]
                    keys.append(key)

                    # Relationship
                    relations["servers_{}/ssh-keys_{}".format(raw_server['hostname'][0], key['_key'])] = {
                        '_from': "servers/{}".format(raw_server['hostname'][0]),
                        '_to': "ssh-keys/{}".format(key['_key']),
                        'kind': 'Has key'
                    }

    print("{} keys processed!".format(len(keys)))
    return keys, relations


def transform_package(raw_packages: list) -> (list, dict):
    packages = []
    for raw_package in raw_packages:
        # Base fields that are always present
        package = {
            '_key': raw_package['name'],
            'name': raw_package['name'],
        }

        if 'version' in raw_package:
            package['version'] = raw_package['version']

        packages.append(package)

    print("{} packages processed!".format(len(packages)))
    return packages, {}


def transform_dm_permission(raw_permissions: list) -> (list, dict):
    relations = {}

    for raw_permission in raw_permissions:
        for raw_package in raw_permission['allow']:
            relations["gpg-keys_{}/packages_{}".format(raw_permission['fingerprint'], raw_package['name'])] = {
                '_from': "gpg-keys/{}".format(raw_permission['fingerprint']),
                '_to': "packages/{}".format(raw_package['name']),
                'kind': 'Has DM permission'
            }
            relations["gpg-keys_{}/packages_{}".format(raw_package['giver'], raw_package['name'])] = {
                '_from': "gpg-keys/{}".format(raw_package['giver']),
                '_to': "packages/{}".format(raw_package['name']),
                'kind': 'Give DM permission'
            }

    print("{} DM permissions processed!".format(len(relations)))
    return [], relations


if __name__ == '__main__':
    transformers = [
        ('groups.json', [('groups.json', transform_group)]),
        ('developers.json', [('developers.json', transform_developer), ('gpg-keys.json', transform_user_gpg_key)]),
        ('servers.json', [('servers.json', transform_server), ('ssh-keys.json', transform_server_ssh_key)]),
        ('packages.json', [('packages.json', transform_package)]),
        ('dm-permissions.json', [('', transform_dm_permission)])
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

            # Write transformed json if needed
            if dst_file != '':
                with open(os.path.join(sys.argv[2], dst_file), 'w+') as dst:
                    json.dump(transformed_data, dst)

    # Write the relations
    print("There is {} relations".format(len(all_relations)))
    with open(os.path.join(sys.argv[2], "relations.json"), 'w+') as dst_file:
        json.dump(list(all_relations.values()), dst_file)
