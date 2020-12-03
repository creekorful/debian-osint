# debian-osint

Funny little experiments to determinate how to exploit
efficiently [OSINT](https://en.wikipedia.org/wiki/Open-source_intelligence) about a public organization.

### Disclaimer

This project is only a little fun experiments to play with OSINT & graph database & isn't designed for a **BAD** usage.

I'm proud to be a Debian contributor and do not intend to harm the organization in any way. If the following project is
more harmful than everything else it will be taken down immediately.

The data collected by the various extractor are available to everyone (OSINT).

# Getting started

The project is designed like an [ETL](https://en.wikipedia.org/wiki/Extract,_transform,_load):

## Extract

First you'll need to extract the data from the sources, this can be done by issuing the following commands:

1. Create a target directory

```
$ mkdir json
```

2. Pull data from the LDAP

```
$ ./ldap2json.py debianDeveloper json/developers.json
$ ./ldap2json.py debianServer json/servers.json
$ ./ldap2json.py debianGroup json/groups.json
```

3. Pull packages list

```
$ ./pkg2json.py json/packages.json
```

4. Pull DM permissions

```
$ ./dm2json.py json/dm-permissions.json
```

## Transform

Once you have the data offline, you'll need to transform them in order to make them exploitable by ArangoDB. This can be
done by issuing the following commands:

1. Create a target directory

```
$ mkdir arango
```

2. Run the transform script

```
$ ./json2arango.py json arango
```

## Load

In order to load the data you'll need to spin up an Arango DB instance. This can be done by using the provided docker
compose:

```
$ docker-compose up -d
```

Then you'll need to head on http://localhost:8529, create the collections, import the json files from arango folder, and
then you'll be ready to query these data and hopefully make something fun of it.