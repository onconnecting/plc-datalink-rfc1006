#!/bin/bash

# Path to the Telegraf configuration directory
CONFIG_DIR="/etc/telegraf/telegraf.d"
# Define the path to the directory
CONF_D_DIR="/etc/supervisor/conf.d/"

# Check if the file '*.conf' exists in the directory
if [ -f "${CONF_D_DIR}*.conf" ]; then
    echo "File '*.conf' exists. Deleting..."
    # Remove the file
    rm "${CONF_D_DIR}*.conf"
    echo "File '*.conf' deleted successfully."
else
    echo "File '*.conf' does not exist."
fi

# Loop through each .conf file in the CONFIG_DIR directory
for config_file in $CONFIG_DIR/*.conf; do
    # Extract the base name of the configuration file
    config_basename=$(basename $config_file .conf)
    conf_file="/etc/supervisor/conf.d/$config_basename.conf"

    echo "Processing file: $config_file with basename: $config_basename"

    # Check if the program entry already exists in the Supervisor configuration file
    if [ ! -f "$conf_file" ]; then
        # If the program entry does not exist, create a new configuration file
        cat <<EOF > $conf_file
[program:$config_basename]
command=/bin/bash -c "sleep 10 && /usr/bin/telegraf --config $config_file --watch-config $config_file"
autostart=true
autorestart=unexpected
startsecs=30
startretries=9999
stopwaitsecs=60
stdout_logfile=/var/log/telegraf/$config_basename.log
stderr_logfile=/var/log/telegraf/$config_basename_error.log
environment=PATH="/usr/bin:%(ENV_PATH)s"
EOF
    else
        echo "Program entry already exists for $config_basename. Skipping..."
    fi
done

# Notify Supervisor to reread and update services
supervisorctl reread
supervisorctl update
