"""
This check validates the operational status of transceiver modules by analyzing key parameters.

Algorithm:
- Requests "show interface transceiver details" command and processes the output.
- If no valid output is received, sets status to FAIL.
- Parses transceiver details (temperature, voltage, current, Tx/Rx power).
- Compares values against predefined threshold ranges for each parameter.
- If all values are within range, sets status to PASS; otherwise, sets status to FAIL and records issues.
"""
import re

class FiberOpticsL1:
    NAME = "Fiber Optics L1"
    VERSION = "1.0.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["sfp", "optics", "transceivers"]
    DESCRIPTION = "Checks the status of transceiver modules, examining details like temperature, voltage, current, and transmit/receive power using 'show interface transceiver details'."
    COMPLEXITY = 1

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show interface transceiver details",
            "handler": "handle_transceiver_details"
        }
        self.RESULTS = {
            "status": 0,
            "observation": "",
            "comments": []
        }

    def handle_transceiver_details(self, device, cmd, output):
        """
        Parses the output of 'show interface transceiver details' to validate transceiver status.
        Checks whether temperature, voltage, current, and power levels are within acceptable ranges.
        """
        try:
            # Example output parsing using regex
            regex_transceiver = re.compile(
                r"^(?P<interface>\S+)\s+"
                r"Temp:(?P<temperature>[+-]?\d+\.?\d*)C\s+"
                r"Voltage:(?P<voltage>[+-]?\d+\.?\d*)V\s+"
                r"Current:(?P<current>[+-]?\d+\.?\d*)mA\s+"
                r"TxPower:(?P<tx_power>[+-]?\d+\.?\d*)dBm\s+"
                r"RxPower:(?P<rx_power>[+-]?\d+\.?\d*)dBm",
                re.MULTILINE
            )

            matches = regex_transceiver.finditer(output)

            if not matches:
                self.RESULTS["status"] = 2
                self.RESULTS["observation"] = "No transceiver information detected in the output."
                self.RESULTS["comments"].append("Ensure the device supports 'show interface transceiver details' and returns valid data.")
                self.REQUESTS = {}
                return

            issues_found = []

            # Example thresholds (update these based on your requirements or device documentation)
            THRESHOLDS = {
                "temperature": (-10, 70),       # Degrees Celsius
                "voltage": (3.1, 3.5),         # Volts
                "current": (0, 100),           # Milliamps (mA)
                "tx_power": (-10, 5),          # dBm
                "rx_power": (-10, 5),          # dBm
            }

            for match in matches:
                interface = match.group("interface")
                temperature = float(match.group("temperature"))
                voltage = float(match.group("voltage"))
                current = float(match.group("current"))
                tx_power = float(match.group("tx_power"))
                rx_power = float(match.group("rx_power"))

                # Check thresholds
                for param, (min_val, max_val) in THRESHOLDS.items():
                    value = locals()[param]
                    if value < min_val or value > max_val:
                        issues_found.append(
                            f"Interface {interface}: {param} out of range ({value}) - expected between {min_val} and {max_val}."
                        )

            if issues_found:
                self.RESULTS["status"] = 2
                self.RESULTS["observation"] = "Issues detected with one or more transceiver modules."
                self.RESULTS["comments"].extend(issues_found)
            else:
                self.RESULTS["status"] = 1
                self.RESULTS["observation"] = "All transceiver modules are within acceptable parameters."
                self.RESULTS["comments"].append("No anomalies found in transceiver status.")

        except Exception as e:
            self.RESULTS["status"] = 5
            self.RESULTS["observation"] = "Error occurred during parsing."
            self.RESULTS["comments"].append(f"Exception: {str(e)}")

        # Clear REQUESTS since this is a single-level check
        self.REQUESTS = {}


CHECK_CLASS = FiberOpticsL1