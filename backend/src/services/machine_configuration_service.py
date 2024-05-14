import os, logging, subprocess

from flask import jsonify
from pathlib import Path
from ..plc_datalink_rfc1006_model import PlcDatalinkRFC1006Model


# Logger instance defined in `init.py`
logger = logging.getLogger('application_logger')


class MachineConfigurationService:
    def __init__(self, telegraf_config_folder, machine_name, couchdb_service):
        self.telegraf_config_folder = telegraf_config_folder
        self.machine_name = machine_name
        self.couchdb_service = couchdb_service

    def write_configuration_to_file(self):
        """Retrieve configuration from DB and write to file."""
        config_file_path = os.path.join(self.telegraf_config_folder, f"{self.machine_name}.conf")
        if os.path.exists(config_file_path):
            logger.warning(f"Configuration file already exists: {config_file_path}, reconfiguring...")
            self.remove_configuration_file()
        try:
            with open(config_file_path, 'w') as file:
                self._write_configuration_content(file)
        except OSError as e:
            logger.error(f"Failed to open and write configuration file: {config_file_path}, Error: {e}")

    def remove_log_file(self):
        """Remove log file."""
        log_file_path = Path(self.telegraf_config_folder) / f"{self.machine_name}.log"
        try:
            log_file_path.unlink()
            logger.warning(f"File removed: {log_file_path}")
        except FileNotFoundError:
            logger.info(f"File not found: {log_file_path}")
        except OSError as e:
            logger.error(f"Error removing files {log_file_path}: {e}")

    def remove_configuration_file(self):
        """Remove configuration file."""
        config_file_path = Path(self.telegraf_config_folder) / f"{self.machine_name}.conf"
        supervisor_file_path = Path("/etc/supervisor/conf.d") / f"{self.machine_name}.conf"

        try:
            config_file_path.unlink()
            supervisor_file_path.unlink()
            subprocess.run(['supervisorctl', 'reread'], check=True)
            subprocess.run(['supervisorctl', 'update'], check=True)
            logger.warning(f"File removed: {config_file_path} and {supervisor_file_path}")
        except FileNotFoundError:
            logger.info(f"File not found: {config_file_path}")
        except OSError as e:
            logger.error(f"Error removing files {config_file_path}: {e}")

    def _get_machine_configuration(self):
        """Retrieve the configuration for a specific machine from CouchDB."""
        try:
            return self.couchdb_service.get_doc(self.machine_name)
        except Exception as e:
            logger.error(f"An error occurred while retrieving configuration for {self.machine_name}: {e}")
            raise
    
    def _write_configuration_content(self, file):
        """Write all sections of the configuration file."""
        try:
            try:
                machineConfiguration = PlcDatalinkRFC1006Model.from_dict(self._get_machine_configuration()).to_json_dict()
            except ValueError as e:
                logger.error(f"Error creating configuration model: {str(e)}")
                return jsonify({"error": str(e)}), 400
            
            logger.info(f"Writing configuration content to file. {machineConfiguration}")

            sections = [
                self._format_agent_configuration(machineConfiguration),
                self._format_s7comm_configuration(machineConfiguration),
                self._format_s7comm_metric(machineConfiguration),
                self._format_dedup_processor(machineConfiguration),
                self._format_mqtt_configuration(machineConfiguration)                
            ]
            file.write("\n".join(sections))
            file.flush()
        except Exception as e:
            logger.error(f"Failed to write configuration content for {machineConfiguration}: {e}")
            raise

    def _format_agent_configuration(self, config):
        """Format the agent section."""
        agent = config['agent']
        machineData = config['machineData']
        lines = [
            "# agent Configuration",
            "[agent]",
            f"  interval = {self._format_string(str(machineData['requestInterval']) + 's')}",
            f"  round_interval = {self._format_bool(agent['roundInterval'])}",
            f"  hostname = {self._format_string(agent['hostname'])}",
            f"  flush_interval = {self._format_string(agent['flushInterval'])}",
            f"  metric_batch_size = 100",
            f"  metric_buffer_limit = 1000",
            f"  log_with_timezone = {self._format_string(agent['logTimezone'])}",
            f"  quiet = {self._format_bool(agent['quiet'])}",
            f"  debug = true",
            f"  logtarget = {self._format_string('file')}",
            f"  logfile = \"{self.telegraf_config_folder}/{machineData['machineName']}.log\"",
            f"  logfile_rotation_max_size = {self._format_string('25MB')}",
            f"  logfile_rotation_max_archives = 1",
            ""
            ]
        return "\n".join(lines)

    def _format_s7comm_configuration(self, config):
        """Format the S7comm input plugin section."""
        machineData = config['machineData']
        server = self._format_server(machineData['plcIp'], machineData.get('plcPort'))
        lines = [
            "# inputs.s7comm Configuration",
            "[[inputs.s7comm]]",
            f"  server = {self._format_string(server)}",
            f"  rack = {machineData['plcRack']}",
            f"  slot = {machineData['plcSlot']}",
            f"  timeout = {self._format_string(machineData['requestS7commTimeout'])}",
            f"  pdu_size = {machineData['pduSize']}",
            f"  debug_connection = false",
            f""
        ]
        return "\n".join(lines)
    
    def _format_s7comm_metric(self, config):
        """Format individual S7comm metrics."""
        lines = []
        for metric in config['plcTagData']:
            lines.append("  [[inputs.s7comm.metric]]")
            lines.append(f"    fields = [{{ name=\"{config['machineData']['machineName']}.{metric['tagName']}\", address=\"{metric['tagAddress']}\" }}]")
            lines.append("    [inputs.s7comm.metric.tags]")
            lines.append(f"      machine = \"{config['machineData']['machineName']}_{config['machineData']['machineName']}.{metric['tagName']}\"")
            lines.append(f"")
        return "\n".join(lines)

    def _format_dedup_processor(self, config):
        """Format the dedup processor section."""
        lines = [
            "# Filter metrics with repeating field values",
            "[[processors.dedup]]",
            f"  dedup_interval = \"86400s\"",
            f""
        ]
        return "\n".join(lines)
    
    def _format_mqtt_configuration(self, config):
        """Format the MQTT output plugin section."""
        mqtt = config['mqttData']
        mqtt_server = f"tcp://{mqtt['mqttIp']}:{mqtt['mqttPort']}"
        lines = [
            "# MQTT Configuration",
            "[[outputs.mqtt]]",
            f"  servers = [{self._format_string(mqtt_server)}]",
            f"  topic = {self._format_string(mqtt['mqttTopic'])}",
            f"  data_format = {self._format_string(mqtt['mqttDataFormat'])}",
            f"  layout = {self._format_string(mqtt['mqttLayout'])}",
            f"  json_timestamp_units = {self._format_string(mqtt['mqttJsonTimestampUnits'])}",
            f""
        ]
        return "\n".join(lines)

    # Format functions
    def _format_string(self, value):
        return f'"{value}"'
    
    def _format_bool(self, value):
        return str(value).lower()
        
    def _format_server(self, ip, port=None):
        return f"{ip}:{port}" if port else ip



