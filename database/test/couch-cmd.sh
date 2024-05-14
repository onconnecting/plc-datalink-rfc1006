
#Create System Databases
curl -X PUT http://admin:password@localhost:5984/_users
curl -X PUT http://admin:password@localhost:5984/_replicator
curl -X PUT http://admin:password@localhost:5984/_global_changes


# Creating a Bucket (Database) in couchDB
curl -X PUT http://admin:password@localhost:5984/example_bucket


# Insert JSON data into couchDB using the REST API
curl -X PUT http://admin:password@localhost:5984/example_bucket/koeln1 -H "Content-Type: application/json" -d '{"name": "John Doe", "age": 31, "city": "koeln1"}'

## Update JSON data into using the REST API
###get the JSON document along with its revision ID (_rev)
curl -X GET http://admin:password@localhost:5984/example_bucket/berlin
# use the retrieved revision ID to update the document:
curl -X PUT http://admin:password@localhost:5984/example_bucket/berlin -H "Content-Type: application/json" -d '{"_rev": "latest_revision_id", "name": "John Doe", "age": 31, "city": "Berlin"}'


# Retrieving one JSON data couchDB
curl -X GET http://admin:password@localhost:5984/datalink/berlin

# Retrieving all JSON data documents couchDB
curl -X GET 'http://admin:password@localhost:5984/datalink/_all_docs?include_docs=true'

# Delete DB
curl -X DELETE http://admin:password@localhost:5984/datalink

