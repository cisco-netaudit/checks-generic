"""
This check evaluates the environmental status of network devices.

Algorithm:
- Requests the "show environment" command and parses the output for sensor data.
- Identifies fans and power supplies with non-OK statuses, and temperature sensors above 75°C.
- If any failures are detected, sets status to FAIL; otherwise, sets status to PASS.
- Populates comments and observations based on the detected environmental issues.
"""

class EnvironmentalStatusCheck:
    NAME = "Environmental Status"
    VERSION = "1.0.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["env", "psu", "temperature", "fans", "nxos"]
    DESCRIPTION = "Evaluates the status of sensors, including fans, power supplies, and temperature sensors using 'show environment'"
    COMPLEXITY = 1

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show environment",
            "handler": "handle_environment_status"
        }
        self.RESULTS = {
            "status": 0,
            "observation": "",
            "comments": []
        }

    def handle_environment_status(self, device, cmd, output):
        import re

        fan_pattern = re.compile(r"Fan\s+(\S+)\s+status:\s+(\S+)", re.IGNORECASE)
        psu_pattern = re.compile(r"Power\s+Supply\s+(\S+)\s+status:\s+(\S+)", re.IGNORECASE)
        temp_pattern = re.compile(r"Temperature\s+Sensor\s+(\S+)\s+value:\s+(\d+)\s+C", re.IGNORECASE)

        fan_statuses = fan_pattern.findall(output)
        psu_statuses = psu_pattern.findall(output)
        temp_readings = temp_pattern.findall(output)

        failed_fans = [fan for fan, status in fan_statuses if status.lower() != "ok"]
        failed_psus = [psu for psu, status in psu_statuses if status.lower() != "ok"]
        high_temps = [sensor for sensor, temp in temp_readings if int(temp) > 75]  # Assuming 75C is the threshold

        if failed_fans or failed_psus or high_temps:
            self.RESULTS["status"] = 2  # FAIL
        else:
            self.RESULTS["status"] = 1  # PASS

        if failed_fans:
            self.RESULTS["comments"].append(f"Failed Fans: {', '.join(failed_fans)}")
        if failed_psus:
            self.RESULTS["comments"].append(f"Failed Power Supplies: {', '.join(failed_psus)}")
        if high_temps:
            self.RESULTS["comments"].append(f"High Temperature Sensors: {', '.join(high_temps)}")

        if self.RESULTS["status"] == 1:
            self.RESULTS["observation"] = "All environmental components are operating normally."
        else:
            self.RESULTS["observation"] = "Some environmental components have issues."

        # Clear the REQUESTS as we are done with our check
        self.REQUESTS = {}


CHECK_CLASS = EnvironmentalStatusCheck