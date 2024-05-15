import os, time, logging, subprocess, signal, re, threading
from pathlib import Path
from .machine_configuration_service import MachineConfigurationService

logger = logging.getLogger('application_logger')


class TelegrafService:
    def __init__(self, telegraf_config_folder, machine_name, couchdb_service):
        self.telegraf_config_folder = Path(telegraf_config_folder)
        self.machine_name = machine_name
        self.couchdb_service = couchdb_service

        self.patterns = {
            "init_plugins": re.compile(r"\[agent\] Initializing plugins"),
            "connected_outputs": re.compile(r"\[agent\] Successfully connected to outputs\.mqtt"),
            "start_service": re.compile(r"\[agent\] Starting service inputs"),
            "successful_connection": re.compile(r"\[inputs\.s7comm\] Connecting to \"[\d\.]+:\d+\"..."),
            "data_received": re.compile(r"\[inputs\.s7comm\]   got \[\d+\] for field"),
            "error_timeout": re.compile(r"Error in plugin: connecting to .* failed: dial tcp .* i/o timeout"),
            "error_reading_failed": re.compile(r"reading batch \d+ failed: Connection to address .* is null; reconnecting..."),
            "error_agent_running": re.compile(r"Error running agent: starting input inputs.s7comm: connecting to .* failed: dial tcp .* i/o timeout"),
            "agent_stopping": re.compile(r"I! \[agent\] Stopping running outputs"),
            "agent_stopped": re.compile(r"D! \[agent\] Stopped Successfully")
        }

    def start_telegraf_service(self):
        """Start a new Telegraf service for the given machine."""
        
        machine_conf_path = self._get_machine_conf_path()
        logger.info(f"Starting Telegraf service: {machine_conf_path}")

        machine_config_service = MachineConfigurationService(
            str(self.telegraf_config_folder),
            self.machine_name,
            self.couchdb_service
        )
        machine_config_service.write_configuration_to_file()

        process_id = self._get_one_telegraf_process_id(machine_conf_path)
        if process_id:
            self._terminate_existing_process(process_id)
        try:
            process = subprocess.Popen(['/app/backend-entrypoint.sh'])
            #process = subprocess.Popen(['telegraf', '--config', str(machine_conf_path), '--watch-config', str(machine_conf_path)])
            logger.info(f"Started new Telegraf process with PID: {process.pid}")
        except Exception as e:
                logger.error(f"Failed to start Telegraf for {machine_conf_path}: {e}")

    def stop_telegraf_service(self):
        """Stop the Telegraf service for the given machine and remove the configuration file."""
        machine_conf_path = self._get_machine_conf_path()
        logger.info(f"Stopping Telegraf service: {machine_conf_path}")

        process_id = self._get_one_telegraf_process_id(machine_conf_path)
        if process_id:
            self._terminate_existing_process(process_id)

        machine_config_service = MachineConfigurationService(
            str(self.telegraf_config_folder),
            self.machine_name,
            self.couchdb_service
        )
        machine_config_service.remove_configuration_file()

    def get_active_telegraf_services(self):
        """
        List all active Telegraf processes with their config file name.
        Returns a list of dictionaries with keys 'machine_name' and 'process'.
        """
        try:
            cmd = "ps aux | grep telegraf | grep -v grep"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)

            processes = [
                {
                    "machine_name": os.path.basename(parts[parts.index('--config') + 1]).replace('.conf', ''),
                    "process": parts[1]
                }
                for line in result.stdout.splitlines()
                if '--config' in (parts := line.split())
            ]

            return processes
        except Exception as e:
            logger.error(f"Error fetching active Telegraf services: {e}")
            return []

    def initiate_telegraf_services(self):
        """Start Telegraf for all existing configurations on app start."""
        config_files = self.get_configured_machines()
        if not config_files:
            logger.warning('No configuration files found.')
            return False

        for config_file in config_files:
            config_file_path = os.path.join(self.telegraf_config_folder, config_file)
            process_id = self._get_one_telegraf_process_id(config_file_path)
            if process_id:
                self._terminate_existing_process(process_id)
            process = subprocess.Popen(['telegraf', '--config', str(config_file_path), '--watch-config', str(config_file_path)])
            logger.info(f"Started new Telegraf process with PID: {process.pid} for {self.machine_name}")
            
            time.sleep(2)
        return True
        

    def get_current_telegraf_state(self):
        log_file_path = self.telegraf_config_folder / f"{self.machine_name}.log"

        if not log_file_path.is_file():
            return {"last_update": None, "last_disconnect": None, "active_connection": False}

        try:
            with open(log_file_path, 'r') as file:
                lines = file.readlines()[-50:] 

            state = {"last_connect_time": None, "last_disconnect_time": None, "active_connection": False}

            for line in reversed(lines):
                timestamp = line[:19]
                self._update_state_from_log(line, timestamp, state)

            if state["last_disconnect_time"] and (not state["last_connect_time"] or state["last_connect_time"] < state["last_disconnect_time"]):
                state["active_connection"] = False
            elif state["last_connect_time"]:
                state["active_connection"] = True

            return {
                "active_connection": state["active_connection"],
                "last_update": state["last_connect_time"] if state["active_connection"] else state["last_disconnect_time"],
                "last_disconnect": state["last_disconnect_time"]
            }

        except Exception as e:
            logger.error(f"Failed to get current machine state {self.machine_name}: {e}")
            return {"active_connection": False, "last_update": None, "last_disconnect": None}

    def _update_state_from_log(self, line, timestamp, state):
        """Update connection state based on log line content."""
        for key, pattern in self.patterns.items():
            if pattern.search(line):
                if key in ["init_plugins", "connected_outputs", "start_service"]:
                    continue
                #elif key in ["successful_connection", "data_received"]:
                elif key in ["data_received"]:
                    state["last_connect_time"] = timestamp
                    state["active_connection"] = True
                elif key in ["error_timeout", "error_reading_failed", "error_agent_running", "agent_stopping", "agent_stopped"]:
                    state["last_disconnect_time"] = timestamp
                    state["active_connection"] = False

                        
    def get_configured_machines(self):
        """Retrieve all configuration files from machines, which are configured."""
        try:
            config_files = [file for file in os.listdir(self.telegraf_config_folder) if file.endswith('.conf')]
            if not config_files:
                logger.warning('No configuration files found.')
            return config_files
        except Exception as e:
            logger.error(f"Error while fetching configuration files: {e}")
            return []

    def get_logged_machines(self):
        """Retrieve all logfile names from machines, which are available."""
        try:
            config_files = [file for file in os.listdir(self.telegraf_config_folder) if file.endswith('.log')]
            if not config_files:
                logger.warning('No logfiles found.')
            return config_files
        except Exception as e:
            logger.error(f"Error while fetching logfiles: {e}")
            return []
          
    def _get_last_log_lines(self,file, lines=100):
        """ Function to get the last 100 'lines' from a file, ensures reading as text. """
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
    
    def _get_one_telegraf_process_id(self, machine_conf_path):
        """Retrieve the process ID of a specific Telegraf process by its configuration file."""
        try:
            result = subprocess.run(['pgrep', '-f', f"telegraf --config {machine_conf_path}"], capture_output=True, text=True)
            if result.stdout.strip():
                return int(result.stdout.strip())
        except ValueError:
            logger.error("Error parsing process ID")
        return None
       
    def _get_machine_conf_path(self):
        """Return the configuration file path for the machine."""
        return self.telegraf_config_folder / f"{self.machine_name}.conf"

    def _terminate_existing_process(self, process_id):
        """Terminate an existing Telegraf process."""
        try:
            os.kill(process_id, signal.SIGTERM)
            logger.info(f"Terminated existing Telegraf process with PID: {process_id}")
        except ProcessLookupError:
            logger.warning(f"Process with PID {process_id} no longer exists.")


