import logging, json
from flask import request, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from requests.exceptions import HTTPError
from .services.couchdb_service import CouchDBService
from .services.telegraf_service import TelegrafService
from .services.machine_configuration_service import MachineConfigurationService
from .plc_datalink_rfc1006_model import PlcDatalinkRFC1006Model



# Logger instance defined in `init.py`
logger = logging.getLogger('application_logger')

SWAGGER_URL = '/swagger'
API_URL = '/static/openapi/plc_datalink_rfc1006_api.yml'

def configure_routes(app):
    # Initialize CouchDBService once and reuse across routes
    couchdb_service = CouchDBService(
        app.config['DATABASE_URL'],
        app.config['DATABASE_USER'],
        app.config['SECRET_KEY'],
        app.config['DATABASE_NAME']        
    )

    # Initialize swaggerui_blueprint
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "PLC Datalink RFC1006 API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.route('/static/openapi/plc_datalink_rfc1006_api.yml')
    def send_openapi_spec():
        return send_from_directory('/app/openapi', 'plc_datalink_rfc1006_api.yml')

        
    @app.route('/config/read/all', methods=['GET'])
    def read_all_config():
        """Endpoint to read all available configurations."""
        try:
            configurations = couchdb_service.get_all_docs()
            return jsonify(configurations), 200
        except HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": f"Configurations not available"}), 404
            else:
                return jsonify({"error": str(e)}), e.response.status_code
        except Exception as e:
            logger.error(f"Error reading all configurations: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/config/read/one', methods=['GET'])
    def read_one_config():
        """Endpoint to read specific machine configurations."""
        machine_name = request.args.get('machine_name')
        if not machine_name:
            return jsonify({"error": "Machine name is required"}), 400

        try:
            configuration = couchdb_service.get_doc(machine_name)
            return jsonify(configuration), 200
        except HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": f"Machine {machine_name} does not exist."}), 404
            else:
                return jsonify({"error": str(e)}), e.response.status_code
        except Exception as e:
            logger.error(f"Error reading configuration for {machine_name}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/config/create', methods=['POST'])
    def store_config():
        """Create a configuration for a specific machine."""
        try:
            raw_data= request.get_json()
            machine_configuration_data = json.loads(raw_data)
            if not machine_configuration_data:
                return jsonify({"error": "Configuration data must be a valid JSON object"}), 400

            try:
                configuration_model = PlcDatalinkRFC1006Model.from_dict(machine_configuration_data).to_json_dict()
                logger.info(f"configuration_model: {configuration_model}")
            except ValueError as e:
                logger.error(f"Error converting to model: {str(e)}")
                return jsonify({"error": str(e)}), 400

            try:
                machine_configuration_model = couchdb_service.create_doc(configuration_model)
                return jsonify(machine_configuration_model), 200
            except HTTPError as e:
                if e.response.status_code == 409:
                    return jsonify({"error": f"Configuration already exists for: {configuration_model['machineData']['machineName']}"}), 409
                else:
                    return jsonify({"error": str(e)}), e.response.status_code
            except Exception as e:
                logger.error(f"Error creating configuration: {str(e)}")
                return jsonify({"error": str(e)}), 500

        except Exception as e:
            logger.error(f"Error parsing configuration data: {str(e)}")
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    @app.route('/config/update', methods=['PUT'])
    def update_config():
        """Update an existing configuration for a specific machine."""
        machine_configuration_data, error_response = _validate_json_input(['machineData'])
        if error_response:
            return jsonify(error_response), 400

        machine_name = machine_configuration_data['machineData'].get('machineName')
        if not machine_name:
            return jsonify({"error": "Machine name is required"}), 400

        try:
            existing_doc = couchdb_service.get_doc(machine_name)
            machine_configuration_data['_rev'] = existing_doc['_rev']
            update_response = couchdb_service.update_doc(machine_name, machine_configuration_data)
            return jsonify(update_response), 200
        except HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": f"Configuration for {machine_name} does not exist, cannot update."}), 404
            elif e.response.status_code == 409:
                return jsonify({"error": f"Configuration update conflict for: {machine_name}, ensure you have the latest version."}), 409
            else:
                return jsonify({"error": str(e)}), e.response.status_code
        except Exception as e:
            logger.error(f"Error updating configuration for {machine_name}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/config/remove', methods=['GET'])
    def remove_config():
        """Remove an existing configuration for a specific machine."""
        machine_name = request.args.get('machine_name')
        if not machine_name:
            return jsonify({"error": "Machine name is required"}), 400

        telegraf_service = TelegrafService(
            app.config['TELEGRAF_CONFIG_FOLDER'],
            machine_name=machine_name,
            couchdb_service=None
        )

        machine_config_service = MachineConfigurationService(
            app.config['TELEGRAF_CONFIG_FOLDER'],
            machine_name=machine_name,
            couchdb_service=None
        )

        try:
            active_services = telegraf_service.get_active_telegraf_services()
            active_machines = [service['machine_name'] for service in active_services]

            if machine_name in active_machines:
                return jsonify({"error": f"Cannot remove configuration for {machine_name}. Machine is currently running."}), 409

            existing_doc = couchdb_service.get_doc(machine_name)
            rev = existing_doc['_rev']
            couchdb_service.delete_doc(machine_name, rev)
            machine_config_service.remove_log_file()

            return jsonify({"message": f"Configuration for {machine_name} has been successfully removed."}), 200

        except HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": f"Configuration for {machine_name} does not exist, cannot remove."}), 404
            else:
                return jsonify({"error": str(e)}), e.response.status_code
        except Exception as e:
            logger.error(f"Error removing configuration for {machine_name}: {str(e)}")
            return jsonify({"error": str(e)}), 500
       
    @app.route('/machine/start', methods=['GET'])
    def start_machine_configuration():
        """Start the Telegraf service for a specific machine."""
        machine_name = request.args.get('machine_name')
        if not machine_name:
            return jsonify({"error": "Machine name is required"}), 400
        return _handle_telegraf_service("start", machine_name)

    @app.route('/machine/stop', methods=['GET'])
    def stop_machine_configuration():
        """Stop the Telegraf service for a specific machine."""
        machine_name = request.args.get('machine_name')
        if not machine_name:
            return jsonify({"error": "Machine name is required"}), 400
        return _handle_telegraf_service("stop", machine_name)

    @app.route('/machine/online', methods=['GET'])
    def active_machines():
        """List all currently active Telegraf processes."""
        telegraf_service = TelegrafService(
            app.config['TELEGRAF_CONFIG_FOLDER'],
            machine_name=None,
            couchdb_service=None
        )
        try:
            machine_list = telegraf_service.get_active_telegraf_services()

            if not machine_list:
                return jsonify({"message": "No machines online."}), 404

            return jsonify({"message": "Active machines", "machines": machine_list}), 200
        except Exception as e:
            logger.error(f"Error fetching active machines: {str(e)}")
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
        
    @app.route('/machine/state', methods=['GET'])
    def machine_curent_state():
        """Get current machine state."""
        machine_name = request.args.get('machine_name')
        if not machine_name:
            return jsonify({"error": "Machine name is required"}), 400
        
        telegraf_service = TelegrafService(
            app.config['TELEGRAF_CONFIG_FOLDER'],
            machine_name=machine_name,
            couchdb_service=None
        )
        try:
            machine_state = telegraf_service.get_current_telegraf_state()

            if not machine_state:
                return jsonify({"message": "Active machine not available."}), 404

            return jsonify({"message": "Machine state", "State": machine_state}), 200
        except Exception as e:
            logger.error(f"Error fetching machine states: {str(e)}")
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    @app.route('/machine/configured', methods=['GET'])
    def configured_machines():
        """List all machines which are configured."""
        telegraf_service = TelegrafService(
            app.config['TELEGRAF_CONFIG_FOLDER'],
            machine_name=None,
            couchdb_service=None
        )
        try:
            machine_file_names = telegraf_service.get_configured_machines()
            machine_configured_list = [file[:-5] for file in machine_file_names if file.endswith('.conf')]

            return jsonify({
                "message": "Configured machines",
                "machines": machine_configured_list
                }), 200
        
        except HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": f"No configured machines available."}), 404
            else:
                return jsonify({"error": str(e)}), e.response.status_code
        except Exception as e:
            logger.error(f"Error fetching configured machines: {str(e)}")
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
    @app.route('/machine/standby', methods=['GET'])
    def standby_machines():
        """List all machines which are in standby."""
        telegraf_service = TelegrafService(
            app.config['TELEGRAF_CONFIG_FOLDER'],
            machine_name=None,
            couchdb_service=None
        )
        try:
            machine_file_names = telegraf_service.get_logged_machines()
            machine_configured_list = [file[:-4] for file in machine_file_names if file.endswith('.log')]

            return jsonify({
                "message": "Standby machines",
                "machines": machine_configured_list
                }), 200
        
        except HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": f"No standby machines available."}), 404
            else:
                return jsonify({"error": str(e)}), e.response.status_code
        except Exception as e:
            logger.error(f"Error fetching standby machines: {str(e)}")
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    @app.route('/machine/remove', methods=['GET'])
    def remove_machine():
        """Remove an existing machine."""
        machine_name = request.args.get('machine_name')
        if not machine_name:
            return jsonify({"error": "Machine name is required"}), 400

        telegraf_service = TelegrafService(
            app.config['TELEGRAF_CONFIG_FOLDER'],
            machine_name=machine_name,
            couchdb_service=None
        )

        machine_config_service = MachineConfigurationService(
            app.config['TELEGRAF_CONFIG_FOLDER'],
            machine_name=machine_name,
            couchdb_service=None
        )

        try:
            active_services = telegraf_service.get_active_telegraf_services()
            active_machines = [service['machine_name'] for service in active_services]

            if machine_name in active_machines:
                return jsonify({"error": f"Cannot remove machine: {machine_name}. Machine is currently running."}), 409

            machine_config_service.remove_log_file()
            return jsonify({"message": f"Machine: {machine_name} has been successfully removed."}), 200

        except HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": f"Machine: {machine_name} does not exist, cannot remove."}), 404
            else:
                return jsonify({"error": str(e)}), e.response.status_code
        except Exception as e:
            logger.error(f"Error removing configuration for {machine_name}: {str(e)}")
            return jsonify({"error": str(e)}), 500
                      
    def _validate_json_input(required_keys):
        """Helper function to validate JSON input"""
        json_data = request.get_json()
        if not json_data:
            return {"error": "Configuration data is required"}, 400
        for key in required_keys:
            if key not in json_data:
                return {"error": f"Missing required key: {key}"}, 400
        return json_data, None

    def _handle_telegraf_service(action, machine_name):
        """Helper to handle start or stop Telegraf service actions"""
        telegraf_service = TelegrafService(
            app.config['TELEGRAF_CONFIG_FOLDER'],
            machine_name,
            couchdb_service
        )
        try:
            try:
                existing_doc = couchdb_service.get_doc(machine_name)
            except HTTPError as e:
                if e.response.status_code == 404:
                    return jsonify({"error": f"Configuration for {machine_name} does not exist, cannot {action}."}), 404
                else:
                    return jsonify({"error": f"Configuration invalid for {machine_name} {str(e)}"}), e.response.status_code

            active_services = telegraf_service.get_active_telegraf_services()
            active_service = next((s for s in active_services if s['machine_name'] == machine_name), None)

            if action == "start":
                if active_service:
                    logger.info(f"restarting active Telegraf service for {machine_name}.")
                    telegraf_service.stop_telegraf_service()

                telegraf_service.start_telegraf_service()
                return jsonify({"message": "Telegraf service started successfully"}), 200
            elif action == "stop":
                if not active_service:
                    return jsonify({"message": f"No active Telegraf service found for {machine_name}."}), 200
                telegraf_service.stop_telegraf_service()
                return jsonify({"message": "Telegraf service stopped successfully"}), 200

        except Exception as e:
            logger.error(f"Error during Telegraf service {action} for {machine_name}: {str(e)}")
            return jsonify({"error": str(e)}), 500