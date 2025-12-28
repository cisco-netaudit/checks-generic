"""
This check verifies that all BGP neighbors are in the 'Established' state.

Algorithm:
- Requests the "show ip bgp neighbors" command and parses the output for neighbor state information.
- If no output is received, sets status to ERROR.
- Identifies and evaluates each neighbor's state from the output.
- If any neighbor is not in the 'Established' state, sets status to FAIL along with details.
- If all neighbors are in the 'Established' state, sets status to PASS.
"""
import re

class BGPNeighborCheck:
    NAME = "BGP Neighbor State"
    VERSION = "1.0.6"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["BGP"]
    DESCRIPTION = "Verify if all the BGP neighbor states are in established state by using the show ip bgp neighbors command."
    COMPLEXITY = 1

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show ip bgp neighbors",   # On NX-OS you can also use: show bgp ipv4 unicast neighbors
            "handler": "handle_initial",
        }
        self.RESULTS = {
            "status": 0,
            "observation": "",
            "comments": [],
        }

    def handle_initial(self, device, command, output):
        """
        Handler to process the output of the 'show ip bgp neighbors' command.
        Verifies if all BGP neighbors are in the 'Established' state.
        """
        try:
            if not output or not output.strip():
                self.RESULTS["status"] = 5  # ERROR
                self.RESULTS["observation"] = "Empty output received from device."
                self.REQUESTS.clear()
                return

            # Split into neighbor blocks. Works for NX-OS/IOS/IOS-XR style headers.
            block_re = re.compile(
                r"(?:^|\n)BGP neighbor is\s+(?P<neighbor>\S+).*?(?=\nBGP neighbor is\s+\S+|\Z)",
                re.DOTALL | re.IGNORECASE
            )
            # Inside each block, capture state in multiple common formats
            state_re = re.compile(
                r"(?:BGP\s+state\s*=\s*|State\s*(?:is|:)\s*)(?P<state>[A-Za-z]+)",
                re.IGNORECASE
            )

            blocks = list(block_re.finditer(output))
            if not blocks:
                # Fallback: try a more generic match just in case the header differs
                generic = re.findall(
                    r"(?P<neighbor>(?:\d{1,3}\.){3}\d{1,3}|[0-9A-Fa-f:]+).*?(?:BGP\s+state\s*=\s*|State\s*(?:is|:)\s*)(?P<state>[A-Za-z]+)",
                    output,
                    re.DOTALL
                )
                if not generic:
                    self.RESULTS["status"] = 6  # INCONCLUSIVE
                    self.RESULTS["observation"] = "Unable to parse BGP neighbor states."
                    self.RESULTS["comments"].append("No neighbor blocks found. Check the exact command used on NX-OS (try 'show bgp ipv4 unicast neighbors').")
                    self.REQUESTS.clear()
                    return
                matches = generic
            else:
                matches = []
                for m in blocks:
                    neighbor = m.group("neighbor")
                    block = m.group(0)
                    sm = state_re.search(block)
                    if sm:
                        matches.append((neighbor, sm.group("state")))
                    else:
                        # If we found a neighbor but no state, record as unparsable
                        matches.append((neighbor, "Unknown"))

            # Evaluate states
            failed_neighbors = []
            unknown_neighbors = []
            for neighbor, state in matches:
                if state.lower() == "established":
                    continue
                elif state.lower() == "unknown":
                    unknown_neighbors.append(neighbor)
                else:
                    failed_neighbors.append((neighbor, state))

            if failed_neighbors or unknown_neighbors:
                self.RESULTS["status"] = 2  # FAIL
                problems = []
                if failed_neighbors:
                    problems.append(f"{len(failed_neighbors)} not 'Established'")
                if unknown_neighbors:
                    problems.append(f"{len(unknown_neighbors)} with unknown state")
                self.RESULTS["observation"] = f"Found {', '.join(problems)}."
                for neighbor, state in failed_neighbors:
                    self.RESULTS["comments"].append(f"Neighbor {neighbor} is in state {state}.")
                for neighbor in unknown_neighbors:
                    self.RESULTS["comments"].append(f"Neighbor {neighbor}: state not found in output block.")
            else:
                self.RESULTS["status"] = 1  # PASS
                self.RESULTS["observation"] = "All BGP neighbors are in 'Established' state."

            self.REQUESTS.clear()

        except Exception as e:
            self.RESULTS["status"] = 5  # ERROR
            self.RESULTS["observation"] = "Error occurred during BGP neighbor state validation."
            self.RESULTS["comments"].append(f"Exception: {str(e)}")
            self.REQUESTS.clear()


CHECK_CLASS = BGPNeighborCheck