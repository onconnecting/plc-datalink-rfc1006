FROM couchdb:3.3.3

# Copy the custom entrypoint script
COPY config/database-entrypoint.sh /database-entrypoint.sh
RUN chmod +x /database-entrypoint.sh

# Copy the initialization script
COPY config/init-db.sh /docker-entrypoint-initdb.d/init-db.sh
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh

# Copy the custom local.ini file
COPY config/local.ini /opt/couchdb/etc/local.ini

# Set the custom entrypoint script as the entrypoint
ENTRYPOINT ["/database-entrypoint.sh"]
CMD ["couchdb"]
