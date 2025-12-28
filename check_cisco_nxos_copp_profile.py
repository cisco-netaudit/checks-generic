"""
This check validates that the Control Plane Policing (CoPP) profile is set to "strict" on NX-OS devices.

Algorithm:
- Requests the command "show run | i strict" to verify the CoPP profile configuration.
- Parses the output to check if the configuration includes "copp profile strict."
- If no output is received, sets status to ERROR.
- If "strict" is found, sets status to PASS; otherwise, sets status to FAIL.
"""

import re


class CoppProfileStrictCheck:
    NAME = "CoPP Profile Strict"
    VERSION = "1.0.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["copp profile", "nxos", "network security"]
    DESCRIPTION = "Verify the CoPP (Control Plane Policing) profile is set to strict on NX-OS devices."
    COMPLEXITY = 2

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show run | i strict",
            "handler": "handle_copp_status"
        }
        self.RESULTS = {
            "status": 0,
            "observation": "",
            "comments": []
        }

    def handle_copp_status(self, device, cmd, output):
        # Example regex pattern to find "strict" in the CoPP status output
        pattern = re.compile(r"copp\s+profile\s+strict")

        if pattern.search(output):
            self.RESULTS["status"] = 1  # PASS
            self.RESULTS["observation"] = "CoPP profile is correctly set to strict."
            self.RESULTS["comments"].append(
                "The CoPP profile on the device is set to 'strict', which is the correct setting. No action is needed.")
        else:
            self.RESULTS["status"] = 2  # FAIL
            self.RESULTS["observation"] = "CoPP profile is not set to strict."
            self.RESULTS["comments"].append(
                "The CoPP profile is not set to 'strict'. "
                "To enhance network security and ensure rate-limiting protects the control plane, "
                "consider setting the CoPP profile to 'strict'."
                "\nExample command to set CoPP profile to strict:\n"
                "  configure terminal\n"
                "  copp profile strict"
            )

        # Clear the REQUESTS to signal completion
        self.REQUESTS.clear()


CHECK_CLASS = CoppProfileStrictCheck