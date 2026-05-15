from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from threading import Thread
import subprocess, os, logging, psutil, signal, re, json
from datetime import datetime
import time


# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost","*"]}})
#CORS(app)

# Use file path as a default
#CONFIG_FILE_PATH_FULL = '/etc/telegraf/telegraf.conf'
TELEGRAF_CONFIG_FOLDER = '/etc/telegraf/'



@app.route('/config/create', methods=['POST'])
def update_and_submit_config():
    """Update all configurations and submit if all sections are set."""
    try:
        data = request.get_json()
        logging.info(f"update_and_submit_config: {data}")
        if data is None:
            raise ValueError("No JSON data provided")
    except ValueError as e:
        logging.error(f"Failed to get JSON data: {e}")
        return jsonify({"error": "Invalid or no JSON data provided."}), 400
    try:
        write_configurations_to_file(data)
        return jsonify({"message": "All configurations updated and submitted successfully"}), 200
    except Exception as e:
        logging.error(f"Error updating and submitting configurations: {e}")
        return jsonify({"error": str(e)}), 500


"""Write a single section's configurations to the file."""
def write_configurations_to_file(data):
    logging.info(f"configuration: {data}")
    # Ensure the directory exists
    os.makedirs(TELEGRAF_CONFIG_FOLDER, exist_ok=True)
    
    # Build the full file path, assuming a '.conf' extension for configuration files
    config_file_path  = os.path.join(TELEGRAF_CONFIG_FOLDER, f"{data['machineData']['machineName']}.conf")
    logging.info(f"write configurations to file: {config_file_path }")
    
    # Open the file for writing
    with open(config_file_path , 'w') as file:
        
        file.write("\n# agent Configuration\n[agent]\n")
        interval = format_string(data['machineData']['requestInterval'])[:-1] + 's"'  # Move the last quote after 's'
        # flush_interval = format_string(data['agent']['flushInterval'])[:-1] + 's"' 
        file.write(f"  interval = {interval}\n")    
        file.write(f"  round_interval = {format_bool(data['agent']['roundInterval'])}\n")
        file.write(f"  hostname = {format_string(data['agent']['hostname'])}\n")
        file.write(f"  flush_interval = {format_string(data['agent']['flushInterval'])}\n")
        file.write(f"  metric_batch_size = 100\n")
        file.write(f"  metric_buffer_limit = 1000\n")
        file.write(f"  log_with_timezone = {format_string(data['agent']['logTimezone'])}\n")
        file.write(f"  quiet = {format_bool(data['agent']['quiet'])}\n")
        file.write(f"  debug = true\n")
        file.write(f"  logtarget = {format_string('file')}\n")
        file.write(f"  logfile = \"{TELEGRAF_CONFIG_FOLDER}{data['machineData']['machineName']}.log\"\n")
        file.write(f"  logfile_rotation_max_size = {format_string('25MB')}\n")
        file.write(f"  logfile_rotation_max_archives = 1\n")
        file.write(f"\n")

        #write_base_sections_to_file
        file.write("\n# inputs.s7comm Configuration\n[[inputs.s7comm]]\n")
        file.write(f"  server = {format_string(data['machineData']['plcIp'])}\n")
        # file.write(f"  port = {format_value(data['machineData']['plcPort'])}\n")
        file.write(f"  rack = {(data['machineData']['plcRack'])}\n")
        file.write(f"  slot = {(data['machineData']['plcSlot'])}\n")
        file.write(f"  timeout = {format_string(data['machineData']['requestS7commTimeout'])}\n")
        file.write(f"  pdu_size = {(data['machineData']['pduSize'])}\n")
        file.write(f"  debug_connection = false\n")

        #Write [[inputs.s7comm.metric]]
        for metric in (data['plcTagData']):
            file.write("\n  [[inputs.s7comm.metric]]\n")
            fields_str = f'{{ name="{metric["tagName"]}", address="{metric["tagAddress"]}" }}'
            file.write(f"    fields = [{fields_str}]\n")
            file.write("    [inputs.s7comm.metric.tags]\n")
            file.write(f"      machine_tag = \"{data['machineData']['machineName']}_{metric['tagName']}\"\n")
        file.write(f"\n")

        #Write the [[processors.dedup]]
        file.write("\n# Filter metrics with repeating field values\n[[processors.dedup]]\n")
        file.write("  dedup_interval = \"86400s\"\n")
        file.write(f"\n")

        #Write [[outputs.mqtt]]
        file.write("\n# MQTT Configuration\n[[outputs.mqtt]]\n")
        mqtt_server = f"tcp://{data['mqttData']['mqttIp']}:{data['mqttData']['mqttPort']}"
        file.write(f"  servers = [{format_string(mqtt_server)}]\n")
        file.write(f"  topic = {format_string(data['mqttData']['mqttTopic'])}\n")
        file.write(f"  data_format = {format_string(data['mqttData']['mqttDataFormat'])}\n")
        file.write(f"  layout = {format_string(data['mqttData']['mqttLayout'])}\n")
        file.write(f"  json_timestamp_units = {format_string(data['mqttData']['mqttJsonTimestampUnits'])}\n")
        file.write(f"\n")

        file.flush()
    #start_telegraf_service_temp(config_file_path)
    #logging.info(f"connection state: {get_connection_state(data['machineData']['machineName'], data['machineData']['plcIp'])}")

def format_string(value):
    return f'"{value}"'
    
def format_bool(value):
    if isinstance(value, bool):
        return str(value).lower()

@app.route('/config/read', methods=['GET'])
def read_config():
    """Read and return the configuration file content."""

    config_file_path  = os.path.join(TELEGRAF_CONFIG_FOLDER, f"{request.args.get('machine_name')}.conf")

    try:
        return send_file(config_file_path, mimetype='text/plain'), 200
    except FileNotFoundError:
        logging.error("Configuration file not found.")
        return jsonify({"error": "Configuration file not found."}), 404
    except Exception as e:
        logging.error(f"Error reading configuration file: {e}")
        return jsonify({"error": str(e)}), 500
    
# def start_telegraf_service():
#      # Find and terminate any existing Telegraf processes
#     for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
#         if proc.info['cmdline'] and 'telegraf' in ' '.join(proc.info['cmdline']):
#             proc.terminate()
#             try:
#                 proc.wait(timeout=5)  # Wait up to 5 seconds for the process to terminate
#             except psutil.TimeoutExpired:
#                 logging.warning(f"PLC Datalink RFC1006 process did not terminate in time, killing it.")
#                 proc.kill()

#     # Start Telegraf
#     subprocess.Popen(['telegraf', '--config', CONFIG_FILE_PATH_FULL, '--watch-config',CONFIG_FILE_PATH_FULL,])





def get_telegraf_process_id(config_file_path):
    """Return the PID of the Telegraf process using the specified configuration file, if running."""
    try:
        # Check for a specific Telegraf process by its command line
        result = subprocess.run(['pgrep', '-f', f"telegraf --config {config_file_path}"], capture_output=True, text=True)
        if result.stdout.strip():
            return int(result.stdout.strip())
    except ValueError:
        pass  # No process found or invalid output
    return None


def list_active_telegraf_processes():
    """
    List all active Telegraf processes along with their config file names.
    Returns a list of dictionaries with keys 'pid' and 'plc_configuration'.
    """
    try:
        # Use 'ps' to get a list of all processes, then grep for 'telegraf'
        cmd = "ps aux | grep telegraf | grep -v grep"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        
        processes = []
        # Parse the output
        for line in result.stdout.splitlines():
            parts = line.split()
            pid = parts[1]
            config_path = None
            # Search for the '--config' argument
            if '--config' in parts:
                config_index = parts.index('--config') + 1
                if config_index < len(parts):
                    config_path = parts[config_index]
                    # Extract the base name without '.conf'
                    base_name = os.path.basename(config_path)
                    config_name = base_name.replace('.conf', '')
            
            # Only append if a config name is found
            if config_path:
                processes.append({"machine_name": config_name, "process": pid})
        
        return processes
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return []
    

@app.route('/plc/processes', methods=['GET'])
def get_telegraf_processes():
    """
    Get a list of all active Telegraf processes along with their config file names.
    
    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    processes = list_active_telegraf_processes()

    if processes:
        response = jsonify(processes)
        return response, 200
    else:
        response = jsonify(error="No active PLC Datalink RFC1006 processes found")
        return response, 404
    

@app.route('/plc/ping', methods=['GET'])
def check_connection_state():
    """
    Check the connection state for the given IP address.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    ip_address = request.args.get('ip_address')

    # Check if IP address is provided
    if ip_address is None:
        response = jsonify(error="IP address not provided")
        return response, 400

    # Ping the IP address
    result = subprocess.run(['ping', '-c', '1', ip_address], capture_output=True)

    # Check the return code to determine the connection state
    if result.returncode == 0:
        connection_state = True
        status_code = 200
    else:
        connection_state = False
        status_code = 400

    connection_info = {"ip_address": ip_address, "plc_connection_reachable": connection_state}

    response = jsonify(connection_info)
    return response, status_code


@app.route('/plc/connection', methods=['GET'])
def get_connection_state():
    try:
        machine_name = request.args.get('machine_name')
        if not machine_name:
            return jsonify({"error": "Machine name is required"}), 400
        
        logfilePath = os.path.join(TELEGRAF_CONFIG_FOLDER, f"{machine_name}.log")
        if not os.path.isfile(logfilePath):
            return jsonify({"error": f"{machine_name} not active"}), 404
        
        connect_attempt_pattern = re.compile(r"Connecting to \"[\d\.]+:\d+\"")
        disconnect_pattern = re.compile(r"Disconnecting from \"[\d\.]+:\d+\"|Stopped Successfully")
        error_message_pattern = re.compile(r"Error in plugin|Error running agent")
        active_processing_pattern = re.compile(r"got \[\d+\] for field")

        last_connect_attempt = None
        last_disconnect = None
        last_error = None
        active_connection = False
        active_processing_count = 0
        
        with open(logfilePath, 'r') as file:  # Changed to text mode
            lines = tail(file, 100)
        
        for line in reversed(lines):
            if re.search(connect_attempt_pattern, line):
                last_connect_attempt = line[:20]
            if re.search(disconnect_pattern, line):
                last_disconnect = line[:20]
            if re.search(error_message_pattern, line):
                last_error = line[:20]
                active_connection = False
            if re.search(active_processing_pattern, line):
                active_processing_count += 1
                if active_processing_count >= 4:
                    active_connection = True
        
        active_connection = active_processing_count >= 4 and not last_disconnect
        
        return jsonify({
            "Last Connection Attempt": last_connect_attempt,
            "Last Disconnection": last_disconnect,
            "Last Error": last_error,
            "Machine Active Connection": active_connection
        }), 200
    except Exception as e:
        return jsonify({"error": "Internal server error: " + str(e)}), 500
    
        
def tail(file, lines=100):
    """ Utility function to get the last 'lines' from a file, ensures reading as text. """
    file.seek(0, os.SEEK_END)
    end = file.tell()
    n_lines = 0
    while n_lines <= lines and end > 0:
        file.seek(max(end - 1024, 0), os.SEEK_SET)
        block = file.read(min(1024, end))
        n_lines += block.count('\n')
        end -= 1024
    file.seek(max(end, 0), os.SEEK_SET)
    return file.read().splitlines()[-lines:]


def start_telegraf_service_temp(config_file_path):
    """Start or restart the Telegraf service with the given configuration."""
    # Find any existing Telegraf process using this specific configuration
    process_id = get_telegraf_process_id(config_file_path)
    if process_id:
        try:
            os.kill(process_id, signal.SIGTERM)  # Send termination signal
            logging.info(f"Terminated existing Telegraf process with PID: {process_id}")
        except ProcessLookupError:
            logging.warning(f"Process with PID {process_id} no longer exists.")

    # Start a new Telegraf process
    process = subprocess.Popen(['telegraf', '--config', config_file_path, '--watch-config', config_file_path])
    logging.info(f"Started new Telegraf process with PID: {process.pid}")
    


@app.route('/plc/stop', methods=['GET'])
def stop_telegraf():
    machine_name = request.args.get('machine_name')
    processes = list_active_telegraf_processes()
    conf_file_path = TELEGRAF_CONFIG_FOLDER + machine_name + '.conf'

    for process_info in processes:
        if process_info['machine_name'] == machine_name:
            pid = int(process_info['process'])
            try:
                os.kill(pid, signal.SIGTERM)
                os.remove(conf_file_path)
                return jsonify({'info': f'Process {pid} for {machine_name} stopped successfully'}), 200
            except ProcessLookupError:
                return jsonify({'warning': f'No such process {pid} for {machine_name}'}), 404
            except PermissionError:
                return jsonify({'error': 'Permission denied to stop the process'}), 403

    return jsonify({'warning': f'No process found for machine {machine_name}'}), 404



@app.route('/plc/execute', methods=['GET'])
def start_telegraf():
    # Construct the path to the config machine file
    machine_name = request.args.get('machine_name')
    conf_file_path = TELEGRAF_CONFIG_FOLDER + machine_name + '.conf'

    start_telegraf_service_thread = Thread(target=start_telegraf_service_temp(conf_file_path))
    start_telegraf_service_thread.start()
    return jsonify({'message': f'PLC Datalink RFC1006 starting wit machine: {machine_name}.'}), 202


def get_config_files():
    """List all .conf files in the TELEGRAF_CONFIG_FOLDER."""
    config_files = []
    for file in os.listdir(TELEGRAF_CONFIG_FOLDER):
        logging.info(f'Configuration file: {file}')
        if file.endswith(".conf"):
            config_files.append(file)
    return config_files


def initiate_telegraf_services():
    """Function to start Telegraf for all configurations found."""
    config_files = get_config_files()
    if not config_files:
        logging.warning('No configuration files found.')
        return False

    for config_file in config_files:
        config_file_path = os.path.join(TELEGRAF_CONFIG_FOLDER, config_file)
        start_telegraf_service_thread = Thread(target=start_telegraf_service_temp(config_file_path))
        start_telegraf_service_thread.start()
        time.sleep(2)

    logging.info(f'Started Telegraf for {len(config_files)} configurations.')
    return True


@app.route('/plc/start-all', methods=['GET'])
def start_all_telegraf():
    """Start Telegraf services for all configurations in the directory via HTTP request."""
    result = initiate_telegraf_services()
    if not result:
        return jsonify({'message': 'No configuration files found.'}), 404
    return jsonify({'message': 'Started Telegraf for all configurations.'}), 200



if __name__ == '__main__':
    if not initiate_telegraf_services():
        logging.error("Failed to start PLC Datalink RFC1006 services.")
    else:
        logging.info("Start PLC Datalink RFC1006 services.")
    #app.run(debug=True, port=5000)
