#!/bin/bash

# Background the initialization script if needed
/docker-entrypoint-initdb.d/init-db.sh &


# Now call the original entrypoint script
exec /usr/local/bin/docker-entrypoint.sh "$@"



