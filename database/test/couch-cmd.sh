#!/bin/bash
# Manual CouchDB test commands.
# Source your project `.env` (or export COUCHDB_USER / COUCHDB_PASSWORD) before running:
#   set -a && source ../../.env && set +a && ./couch-cmd.sh
: "${COUCHDB_USER:?set COUCHDB_USER (see .env.example)}"
: "${COUCHDB_PASSWORD:?set COUCHDB_PASSWORD (see .env.example)}"
CREDS="${COUCHDB_USER}:${COUCHDB_PASSWORD}"

#Create System Databases
curl -X PUT "http://${CREDS}@localhost:5984/_users"
curl -X PUT "http://${CREDS}@localhost:5984/_replicator"
curl -X PUT "http://${CREDS}@localhost:5984/_global_changes"


# Creating a Bucket (Database) in couchDB
curl -X PUT "http://${CREDS}@localhost:5984/example_bucket"


# Insert JSON data into couchDB using the REST API
curl -X PUT "http://${CREDS}@localhost:5984/example_bucket/koeln1" -H "Content-Type: application/json" -d '{"name": "John Doe", "age": 31, "city": "koeln1"}'

## Update JSON data into using the REST API
###get the JSON document along with its revision ID (_rev)
curl -X GET "http://${CREDS}@localhost:5984/example_bucket/berlin"
# use the retrieved revision ID to update the document:
curl -X PUT "http://${CREDS}@localhost:5984/example_bucket/berlin" -H "Content-Type: application/json" -d '{"_rev": "latest_revision_id", "name": "John Doe", "age": 31, "city": "Berlin"}'


# Retrieving one JSON data couchDB
curl -X GET "http://${CREDS}@localhost:5984/datalink/berlin"

# Retrieving all JSON data documents couchDB
curl -X GET "http://${CREDS}@localhost:5984/datalink/_all_docs?include_docs=true"

# Delete DB
curl -X DELETE "http://${CREDS}@localhost:5984/datalink"
