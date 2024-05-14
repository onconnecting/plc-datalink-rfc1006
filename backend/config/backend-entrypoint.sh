#!/bin/bash
# Execute the dynamic startup script for Telegraf
/app/dynamic_startup_telegraf.sh

# Now run the original CMD from the Dockerfile
exec "$@"
