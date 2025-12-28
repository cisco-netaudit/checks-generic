"""
This check validates LACP port-channel configuration and member interface states on NX-OS devices.

Algorithm:
- Requests "show port-channel summary" command and parses the output for port-channel data.
- Skips irrelevant header and separator lines.
- Identifies port-channels with issues such as down status, non-LACP protocol, or no active members.
- If any issues are detected, sets status to FAIL; otherwise, sets status to PASS.
"""

import re

class PortChannelCheck:
    NAME = "Port Channel Status"
    VERSION = "1.2.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["LACP", "nxos", "interface"]
    DESCRIPTION = "Verify LACP port-channel configuration and member interface states on NX-OS devices."
    COMPLEXITY = 2

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {"device": self.device, "command": "show port-channel summary", "handler": "handle_initial"}
        self.RESULTS = {"status": 0, "observation": "", "comments": []}

    def handle_initial(self, device, cmd, output):
        """
        Parse port-channel summary and detect issues.
        Handles Po names with embedded status flags and any number of member interfaces.
        """
        port_channels_with_issues = []

        # Skip headers and separator lines
        lines = [line for line in output.splitlines() if line.strip() and not line.startswith("-") and not line.startswith("Flags") and not line.startswith("Group")]

        # Regex to match lines like:
        # 100   Po100(SU)   Eth      LACP      Eth1/49(P)   Eth1/50(P)
        pattern = re.compile(
            r"^\d+\s+"                          # Group number
            r"(Po\d+\([A-Z]+\))\s+"             # Port-channel with flags, e.g., Po100(SU)
            r"([A-Za-z]+)\s+"                    # Type, e.g., Eth
            r"([A-Za-z]+)\s+"                    # Protocol, e.g., LACP
            r"((?:[A-Za-z0-9/]+(?:\([A-Z]\))?\s*)+)$"  # Member interfaces (any number)
        )

        for line in lines:
            match = pattern.match(line)
            if not match:
                continue

            po_name, po_type, protocol, members = match.groups()
            member_list = members.split()

            # Check if port-channel is down based on embedded flags in Po name
            # Example flags: SU = Up, SD = Down
            if "D" in po_name.upper():
                port_channels_with_issues.append(
                    f"{po_name} has a down status (check flags in Po name)."
                )

            # Check LACP protocol
            if protocol.upper() != "LACP":
                port_channels_with_issues.append(
                    f"{po_name} is not using LACP protocol (found {protocol})."
                )

            # Check for no active member interfaces
            if not member_list:
                port_channels_with_issues.append(
                    f"{po_name} has no member interfaces."
                )

        # Update RESULTS
        if port_channels_with_issues:
            self.RESULTS["status"] = 2  # FAIL
            self.RESULTS["observation"] = f"Found {len(port_channels_with_issues)} port-channel(s) with issues."
            self.RESULTS["comments"].extend(port_channels_with_issues)
        else:
            self.RESULTS["status"] = 1  # PASS
            self.RESULTS["observation"] = "All port-channels are healthy."
            self.RESULTS["comments"].append("No issues detected with port-channel configuration or status.")

        self.REQUESTS = {}  # No further action needed for now

CHECK_CLASS = PortChannelCheck