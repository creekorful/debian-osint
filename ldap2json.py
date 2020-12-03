#!/usr/bin/env python3

# This script is used to dump object from the debian LDAP (db.debian.org)
# into a json file for further analysis.
#
# This allows to keep a local cache of the Debian LDAP and allow work with local data
# instead of spamming the server for results.
# Therefore this script does NOT transform the received data.
#
# example usages:
# - ./ldap2json.py debianDeveloper developers.json
# - ./ldap2json.py debianServer servers.json
# - ./ldap2json.py debianGroup groups.json

import json
import sys

from ldap3 import Server, Connection
from ldap3.utils.conv import format_json

if __name__ == '__main__':
    s = Server('db.debian.org')
    conn = Connection(s)

    # Connect to the LDAP server
    if not conn.bind():
        print("unable to connect to the LDAP server")
        sys.exit(1)

    ok = conn.search('dc=debian,dc=org', "(objectclass={})".format(sys.argv[1]), attributes=['*'])
    if not ok:
        print("error while querying LDAP server")
        sys.exit(1)

    entries = []
    for entry in conn.entries:
        entries.append(entry.entry_attributes_as_dict)

    with open(sys.argv[2], 'w+') as outfile:
        json.dump(entries, outfile, ensure_ascii=True, default=format_json)
    print("successfully retrieved {} entries".format(len(entries)))
