"""
This check validates that all route-maps referenced in BGP configuration, including templates, are properly defined.

Algorithm:
- Requests the "show run" command and retrieves the device configuration.
- Parses the output to extract defined route-maps and those referenced in BGP neighbors or templates.
- Checks if all referenced route-maps are defined.
- If no BGP configuration is found, sets status to FAIL with relevant comments.
- Sets status to PASS if all referenced route-maps are defined, otherwise sets status to FAIL.
"""

import re

class RouteMapPresenceCheck:
    NAME = "Route Map Presence"
    VERSION = "1.2.1"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["BGP", "route-maps", "templates"]
    DESCRIPTION = "Verify that all route-maps used in BGP neighbors or templates are defined."
    COMPLEXITY = 4

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show run",
            "handler": "handle_route_map_check"
        }
        self.RESULTS = {"status": 0,
                        "observation": "",
                        "comments": []}

    def handle_route_map_check(self, device, cmd, output):
        defined_route_maps = set()
        used_route_maps = set()
        template_route_maps = {}
        neighbor_to_template = {}

        # --- Capture all defined route-maps
        defined_pattern = re.compile(r"^route-map\s+(\S+)\s+(permit|deny)\b", re.MULTILINE)
        for match in defined_pattern.finditer(output):
            defined_route_maps.add(match.group(1))

        # --- Extract BGP configuration block (robust version)
        bgp_section_pattern = re.compile(
            r"(?m)^\s*router bgp\s+\d+[\s\S]*?(?=^\S|\Z)"
        )
        bgp_match = bgp_section_pattern.search(output)
        if not bgp_match:
            self.RESULTS["status"] = 2
            self.RESULTS["observation"] = "No BGP configuration found."
            self.RESULTS["comments"].append("Ensure 'router bgp' is present in configuration.")
            self.REQUESTS.clear()
            return

        bgp_config = bgp_match.group(0)

        # --- Parse templates and their route-maps
        template_pattern = re.compile(
            r"(?m)^ {2,}template peer (\S+)([\s\S]*?)(?=^ {2,}(?:template|neighbor|exit|!|\Z))"
        )
        for tmatch in template_pattern.finditer(bgp_config):
            template_name = tmatch.group(1)
            template_body = tmatch.group(2)
            maps = re.findall(r"route-map\s+(\S+)\s+(in|out)", template_body)
            if maps:
                template_route_maps[template_name] = {m[0] for m in maps}

        # --- Parse neighbors and find inherited templates
        neighbor_pattern = re.compile(
            r"(?m)^ {2,}neighbor\s+(\S+)([\s\S]*?)(?=^ {2,}(?:neighbor|template|exit|!|\Z))"
        )
        for nmatch in neighbor_pattern.finditer(bgp_config):
            neighbor = nmatch.group(1)
            body = nmatch.group(2)
            inherit_match = re.search(r"inherit\s+peer\s+(\S+)", body)
            if inherit_match:
                neighbor_to_template[neighbor] = inherit_match.group(1)
            maps = re.findall(r"route-map\s+(\S+)\s+(in|out)", body)
            for m in maps:
                used_route_maps.add(m[0])

        # --- Combine route-maps from templates into used list
        for neighbor, template in neighbor_to_template.items():
            if template in template_route_maps:
                used_route_maps.update(template_route_maps[template])

        # --- Compare
        missing_maps = used_route_maps - defined_route_maps

        if not used_route_maps:
            self.RESULTS["status"] = 1
            self.RESULTS["observation"] = "No route-maps are referenced under BGP neighbors or templates."
            self.RESULTS["comments"].append("No route-maps found in BGP configuration.")
        elif not missing_maps:
            self.RESULTS["status"] = 1
            self.RESULTS["observation"] = "All route-maps referenced in BGP configuration (including templates) are defined."
            self.RESULTS["comments"].append(f"Defined route-maps: {', '.join(sorted(defined_route_maps))}")
            self.RESULTS["comments"].append(f"Used route-maps: {', '.join(sorted(used_route_maps))}")
        else:
            self.RESULTS["status"] = 2
            self.RESULTS["observation"] = "Some route-maps referenced in BGP configuration or templates are missing."
            self.RESULTS["comments"].append(f"Missing route-maps: {', '.join(sorted(missing_maps))}")
            if defined_route_maps:
                self.RESULTS["comments"].append(f"Defined route-maps: {', '.join(sorted(defined_route_maps))}")
            if used_route_maps:
                self.RESULTS["comments"].append(f"Used route-maps: {', '.join(sorted(used_route_maps))}")

        # --- Done
        self.REQUESTS.clear()


CHECK_CLASS = RouteMapPresenceCheck