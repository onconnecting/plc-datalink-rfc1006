from dataclasses import dataclass, field
from typing import List

@dataclass
class Agent:
    flush_interval: str
    hostname: str
    log_timezone: str
    quiet: bool
    round_interval: bool

@dataclass
class MachineData:
    machine_name: str
    machine_state: str
    pdu_size: int
    plc_ip: str
    plc_port: int
    plc_rack: int
    plc_slot: int
    request_interval: int
    request_s7comm_timeout: str

@dataclass
class MQTTData:
    mqtt_data_format: str
    mqtt_ip: str
    mqtt_json_timestamp_units: str
    mqtt_layout: str
    mqtt_port: int
    mqtt_topic: str

@dataclass
class PLCTagData:
    tag_address: str
    tag_name: str
@dataclass
class PlcDatalinkRFC1006Model:
    agent: Agent
    machine_data: MachineData
    mqtt_data: MQTTData
    plc_tag_data: List[PLCTagData] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict) -> "PlcDatalinkRFC1006Model":
        """Create a PlcDatalinkRFC1006Model instance from a dictionary."""
        try:
            # Define static values with defaults
            static_agent = {
                "flushInterval": "1s",
                "hostname": "PLC Datalink RFC1006",
                "logTimezone": "local",
                "quiet": False,
                "roundInterval": True
            }
            static_machine_data = {
                "machineState": "OFF",
                "requestS7commTimeout": "10s"
            }
            static_mqtt_data = {
                "mqttDataFormat": "json",
                "mqttJsonTimestampUnits": "1ms",
                "mqttLayout": "non-batch"
            }

            # Merge static and dynamic (incoming) values
            agent_data = {**static_agent, **data.get("agent", {})}
            machine_data = {**static_machine_data, **data.get("machineData", {})}
            mqtt_data = {**static_mqtt_data, **data.get("mqttData", {})}

            # Construct the models with merged data
            agent = Agent(
                flush_interval=agent_data["flushInterval"],
                hostname=agent_data["hostname"],
                log_timezone=agent_data["logTimezone"],
                quiet=agent_data["quiet"],
                round_interval=agent_data["roundInterval"]
            )

            machine_data_obj = MachineData(
                machine_name=machine_data["machineName"],
                machine_state=machine_data["machineState"],
                pdu_size=machine_data["pduSize"],
                plc_ip=machine_data["plcIp"],
                plc_port=machine_data["plcPort"],
                plc_rack=machine_data["plcRack"],
                plc_slot=machine_data["plcSlot"],
                request_interval=machine_data["requestInterval"],
                request_s7comm_timeout=machine_data["requestS7commTimeout"]
            )

            mqtt_data_obj = MQTTData(
                mqtt_data_format=mqtt_data["mqttDataFormat"],
                mqtt_ip=mqtt_data["mqttIp"],
                mqtt_json_timestamp_units=mqtt_data["mqttJsonTimestampUnits"],
                mqtt_layout=mqtt_data["mqttLayout"],
                mqtt_port=mqtt_data["mqttPort"],
                mqtt_topic=mqtt_data["mqttTopic"]
            )

            plc_tag_data = [
                PLCTagData(tag_address=tag["tagAddress"], tag_name=tag["tagName"])
                for tag in data.get("plcTagData", [])
            ]

            return PlcDatalinkRFC1006Model(
                agent=agent,
                machine_data=machine_data_obj,
                mqtt_data=mqtt_data_obj,
                plc_tag_data=plc_tag_data
            )
        except KeyError as e:
            raise ValueError(f"Missing required key: {str(e)}")

    def to_json_dict(self) -> dict:
        """Convert PlcDatalinkRFC1006Model to a JSON dictionary for CouchDB storage."""
        return {
            "agent": {
                "flushInterval": self.agent.flush_interval,
                "hostname": self.agent.hostname,
                "logTimezone": self.agent.log_timezone,
                "quiet": self.agent.quiet,
                "roundInterval": self.agent.round_interval
            },
            "machineData": {
                "machineName": self.machine_data.machine_name,
                "machineState": self.machine_data.machine_state,
                "pduSize": self.machine_data.pdu_size,
                "plcIp": self.machine_data.plc_ip,
                "plcPort": self.machine_data.plc_port,
                "plcRack": self.machine_data.plc_rack,
                "plcSlot": self.machine_data.plc_slot,
                "requestInterval": self.machine_data.request_interval,
                "requestS7commTimeout": self.machine_data.request_s7comm_timeout
            },
            "mqttData": {
                "mqttDataFormat": self.mqtt_data.mqtt_data_format,
                "mqttIp": self.mqtt_data.mqtt_ip,
                "mqttJsonTimestampUnits": self.mqtt_data.mqtt_json_timestamp_units,
                "mqttLayout": self.mqtt_data.mqtt_layout,
                "mqttPort": self.mqtt_data.mqtt_port,
                "mqttTopic": self.mqtt_data.mqtt_topic
            },
            "plcTagData": [
                {"tagAddress": tag.tag_address, "tagName": tag.tag_name}
                for tag in self.plc_tag_data
            ]
        }
