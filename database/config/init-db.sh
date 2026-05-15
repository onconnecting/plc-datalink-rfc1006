#!/bin/bash
# Wait for CouchDB to start
until curl -s http://localhost:5984/ > /dev/null; do
  echo 'Waiting for CouchDB...'
  sleep 1
done

echo 'Initializing databases...'
# Credentials come from the COUCHDB_USER / COUCHDB_PASSWORD env vars
# that the official couchdb image already consumes for admin setup.
CREDS="${COUCHDB_USER}:${COUCHDB_PASSWORD}"
# Initialize _users, _replicator, _global_changes, and datalink databases
curl -X PUT "http://${CREDS}@localhost:5984/_users"
sleep 1
curl -X PUT "http://${CREDS}@localhost:5984/_global_changes"
sleep 1
curl -X PUT "http://${CREDS}@localhost:5984/_replicator"
sleep 1
curl -X PUT "http://${CREDS}@localhost:5984/datalink"
sleep 1
