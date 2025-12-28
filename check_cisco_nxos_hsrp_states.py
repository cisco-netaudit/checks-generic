"""
This check validates the HSRP (Hot Standby Router Protocol) state and configuration 
on NX-OS devices to ensure proper redundancy and failover roles.

Algorithm:
- Requests the "show hsrp brief" command and parses the output for HSRP group details.
- If no group details are found, sets status to FAIL with appropriate comments.
- Validates HSRP state, active, and standby IP addresses for each group.
- If all groups are valid, sets status to PASS; otherwise, sets status to FAIL and logs issues.
"""

import re

class HsrpStateCheck:
    """Check that HSRP (Hot Standby Router Protocol) configurations are correct and active without issues."""

    NAME = "HSRP State"
    VERSION = "1.5.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["HSRP", "nxos", "networking"]
    DESCRIPTION = "Validates HSRP state and ensures active and standby roles are correctly configured on NX-OS devices."
    COMPLEXITY = 2

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {"device": self.device, "command": "show hsrp brief", "handler": "handle_hsrp_brief"}
        self.RESULTS = {"status": 0,
                        "observation": "",
                        "comments": []
                        }

    def handle_hsrp_brief(self, device, cmd, output):
        """
        Parse HSRP brief information using regex to extract only valid data lines.
        Handles 'local' as valid Active/Standby IP.
        """
        # Regex to match HSRP data lines:
        # Optional leading spaces, Interface, Group, Prio, optional P column, State, Active, Standby, Virtual
        pattern = re.compile(
            r"^\s*"                             # optional leading spaces
            r"(?P<intf>\S+)\s+"                 # Interface
            r"(?P<group>\d+)\s+"                # Group
            r"(?P<prio>\d+)\s+"                 # Priority
            r"(?:\S\s+)?"                        # Optional P column (single char)
            r"(?P<state>\S+)\s+"                # State
            r"(?P<active>\S+)\s+"               # Active address
            r"(?P<standby>\S+)\s+"              # Standby address
            r"(?P<virtual>.+)$",                # Virtual/group addr (anything)
            re.MULTILINE
        )

        matches = pattern.findall(output)

        if not matches:
            self.RESULTS["status"] = 2
            self.RESULTS["observation"] = "No HSRP groups found."
            self.RESULTS["comments"].append("HSRP output did not contain any group details.")
            self.REQUESTS.clear()
            return

        failed_groups = []
        ip_regex = r"^\d+\.\d+\.\d+\.\d+$"

        for intf, group, prio, state, active, standby, virtual in matches:
            # State check
            if state not in ("Active", "Standby", "local"):
                failed_groups.append(f"Interface {intf}, Group {group} has unexpected state '{state}'.")

            # IP validation (skip 'local')
            if active != "local" and not re.match(ip_regex, active):
                failed_groups.append(f"Interface {intf}, Group {group}: Invalid Active IP '{active}'")
            if standby != "local" and not re.match(ip_regex, standby):
                failed_groups.append(f"Interface {intf}, Group {group}: Invalid Standby IP '{standby}'")

        if failed_groups:
            self.RESULTS["status"] = 2
            self.RESULTS["observation"] = "Issues detected with HSRP group states or addresses."
            self.RESULTS["comments"].extend(failed_groups)
        else:
            self.RESULTS["status"] = 1
            self.RESULTS["observation"] = "All HSRP groups are correctly configured and in proper state."
            self.RESULTS["comments"].append("HSRP groups are operating correctly with valid Active/Standby roles.")

        self.REQUESTS.clear()


CHECK_CLASS = HsrpStateCheck