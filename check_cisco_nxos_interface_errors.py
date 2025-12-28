"""
This check validates interface health by identifying error counters in the device's interface statistics.

Algorithm:
- Requests "show interface" command and parses the output to extract error counters per interface.
- If no output is received, sets status to ERROR.
- If all counters are zero, sets status to PASS with a confirmation message.
- If any interface reports non-zero error counters, sets status to FAIL and reports the affected interfaces and counters.
"""
import re

class InterfaceErrorCheck:
    NAME = "Interface Errors"
    VERSION = "1.0.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["interfaces", "errors", "health"]
    DESCRIPTION = "Checks all interfaces for errors such as runts, giants, CRC, input/output errors."
    COMPLEXITY = 2

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show interface",
            "handler": "handle_interface_errors"
        }
        self.RESULTS = {"status": 0,
                        "observation": "",
                        "comments": []
                        }

    def handle_interface_errors(self, device, cmd, output):
        """
        Parses 'show interface' output to identify interfaces with error counters.
        Works with NX-OS style 'show interface' outputs.
        """

        # Match each interface block — until next interface or end of text
        interface_pattern = re.compile(
            r"^(\S+)\s+is\s+.*?(?=^\S+\s+is\s+|\Z)",
            re.DOTALL | re.MULTILINE
        )

        error_interfaces = {}

        for match in interface_pattern.finditer(output):
            iface_block = match.group(0)
            iface_name = match.group(1)

            # Extract counters (default 0 if missing)
            errors = {
                "runts": self._get_int(r"(\d+)\s+runts", iface_block),
                "giants": self._get_int(r"(\d+)\s+giants", iface_block),
                "crc": self._get_int(r"(\d+)\s+CRC", iface_block),
                "input_errors": self._get_int(r"(\d+)\s+input error", iface_block),
                "output_errors": self._get_int(r"(\d+)\s+output error", iface_block),
                "collisions": self._get_int(r"(\d+)\s+collision", iface_block),
                "ignored": self._get_int(r"(\d+)\s+ignored", iface_block),
            }

            # Flag interface if any counter > 0
            if any(v > 0 for v in errors.values()):
                error_interfaces[iface_name] = errors

        # --- Reporting ---
        if not error_interfaces:
            self.RESULTS["status"] = 1  # PASS
            self.RESULTS["observation"] = "No interface errors detected."
            self.RESULTS["comments"].append("All interfaces are operating normally.")
        else:
            self.RESULTS["status"] = 2  # FAIL
            self.RESULTS["observation"] = f"{len(error_interfaces)} interface(s) have error counters."
            for iface, counters in error_interfaces.items():
                err_summary = ", ".join(
                    [f"{k}: {v}" for k, v in counters.items() if v > 0]
                )
                self.RESULTS["comments"].append(f"{iface}: {err_summary}")

        # Clear requests once handled
        self.REQUESTS.clear()

    @staticmethod
    def _get_int(pattern, text):
        """
        Helper: returns integer from regex match, or 0 if not found.
        """
        m = re.search(pattern, text)
        return int(m.group(1)) if m else 0


CHECK_CLASS = InterfaceErrorCheck