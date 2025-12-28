"""
This check enforces compliance of CDP-connected interface descriptions based on a specific naming convention.

Algorithm:
- Requests "show cdp neighbors detail" and parses the output to extract CDP neighbor relationships.
- If no CDP neighbors are found, sets status to INCONCLUSIVE.
- Requests "show interfaces description" and compares actual descriptions with the expected format.
- If all descriptions match the expected format, sets status to PASS.
- If discrepancies exist, sets status to FAIL and records non-compliant interfaces.
"""

import re

class CDPInterfaceDescriptionComplianceCheck:
    NAME = "CDP Interface Description Compliance"
    VERSION = "1.0.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["CDP", "Interface", "Compliance", "Description"]
    DESCRIPTION = (
        "Ensures that all CDP-connected interfaces have descriptions matching the "
        "format <local_interface>_<remote_hostname>_<remote_interface>."
    )
    COMPLEXITY = 2

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show cdp neighbors detail",
            "handler": "handle_cdp_neighbors",
        }
        self.RESULTS = {
            "status": 0,
            "observation": "",
            "comments": [],
        }
        self.cdp_data = {}

    def handle_cdp_neighbors(self, device, cmd, output):
        """
        Parses CDP neighbor details to map local interfaces to remote devices and ports.
        """
        neighbor_pattern = re.compile(
            r"Device ID:\s*(?P<remote_host>[^\n(]+).*?"
            r"Interface:\s*(?P<local_intf>[\w/.\-]+),\s*Port ID \(outgoing port\):\s*(?P<remote_intf>[\w/.\-]+)",
            re.DOTALL | re.IGNORECASE
        )

        for match in neighbor_pattern.finditer(output):
            local_intf = match.group("local_intf").strip()
            remote_host = match.group("remote_host").split(".")[0].strip()
            remote_intf = match.group("remote_intf").strip()
            self.cdp_data[local_intf] = {
                "remote_host": remote_host,
                "remote_intf": remote_intf
            }

        if not self.cdp_data:
            self.RESULTS["status"] = 6  # INCONCLUSIVE
            self.RESULTS["observation"] = "No CDP neighbors found or parsing failed."
            self.RESULTS["comments"].append(
                "Could not extract CDP neighbor data. Ensure 'show cdp neighbors detail' output is available."
            )
            self.REQUESTS = {}
            return

        # Next command: get interface descriptions
        self.REQUESTS = {
            "device": self.device,
            "command": "show interfaces description",
            "handler": "handle_interface_descriptions",
        }

    def handle_interface_descriptions(self, device, cmd, output):
        """
        Compares actual interface descriptions with expected CDP-based format.
        """
        desc_pattern = re.compile(r"^(?P<intf>\S+)\s+(?P<status>up|down|admin down)\s+\S+\s+(?P<desc>.+)?", re.MULTILINE)
        descriptions = {}

        for match in desc_pattern.finditer(output):
            intf = match.group("intf")
            desc = match.group("desc").strip() if match.group("desc") else ""
            descriptions[intf] = desc

        non_compliant = []
        compliant_count = 0

        for local_intf, info in self.cdp_data.items():
            expected_desc = f"{local_intf}_{info['remote_host']}_{info['remote_intf']}"
            actual_desc = descriptions.get(local_intf, "")
            if actual_desc == expected_desc:
                compliant_count += 1
            else:
                non_compliant.append((local_intf, actual_desc, expected_desc))

        total_checked = len(self.cdp_data)
        if not total_checked:
            self.RESULTS["status"] = 6  # INCONCLUSIVE
            self.RESULTS["observation"] = "No CDP-connected interfaces were found."
            self.RESULTS["comments"].append("Check skipped — no CDP neighbor interfaces detected.")
        elif not non_compliant:
            self.RESULTS["status"] = 1  # PASS
            self.RESULTS["observation"] = (
                f"All {total_checked} CDP-connected interfaces have compliant descriptions."
            )
            self.RESULTS["comments"].append("All CDP-connected interfaces follow the standard naming convention.")
        else:
            self.RESULTS["status"] = 2  # FAIL
            self.RESULTS["observation"] = (
                f"{len(non_compliant)} out of {total_checked} CDP-connected interfaces have non-compliant descriptions."
            )
            for local_intf, actual, expected in non_compliant:
                self.RESULTS["comments"].append(
                    f"Interface {local_intf} has description '{actual}' — expected '{expected}'. "
                    f"Remediation: update description using 'description {expected}'."
                )

        self.REQUESTS = {}

CHECK_CLASS = CDPInterfaceDescriptionComplianceCheck