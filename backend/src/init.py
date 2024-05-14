from flask import Flask
from flask_cors import CORS
import os, threading
import sys
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from .services.telegraf_service import TelegrafService
from .routes import configure_routes


logger = logging.getLogger('application_logger')
logger.setLevel(logging.INFO)

# Rotating file handler for application-specific log files
file_handler = RotatingFileHandler('/var/log/plc-datalink-rfc1006.log', maxBytes=50 * 1024 * 1024, backupCount=1)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console logging without rotation
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Example log usage
logger.info('PLC-DATALINK-RFC1006 starting')


# Set the path to the .env file relative to this file's location
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

load_dotenv(dotenv_path)

app = Flask(__name__)

# Apply CORS to the entire app with a default configuration
CORS(app, resources={r"/*": {"origins": ["http://localhost", "*"]}})

# Apply additional configuration settings from environment variables
app.config.from_mapping(        
    DATABASE_USER=os.getenv('DATABASE_USER_NAME', 'default_user'),
    SECRET_KEY=os.getenv('DATABASE_SECRET_KEY', 'default_secret_key'),
    DATABASE_URL=os.getenv('DATABASE_URL', 'http://localhost:5984'),
    DATABASE_NAME=os.getenv('DATABASE_NAME', 'datalink'),
    TELEGRAF_CONFIG_FOLDER='/etc/telegraf/telegraf.d/'
)

# Register application routes
configure_routes(app)

# Initialize Telegraf services and start them if any configuration files are available

telegraf_service = TelegrafService(
    telegraf_config_folder=app.config['TELEGRAF_CONFIG_FOLDER'],
    machine_name=None,
    couchdb_service=None
)
    
#telegraf_service.initiate_telegraf_services()


if __name__ == '__main__':
    app.run(debug=False)
