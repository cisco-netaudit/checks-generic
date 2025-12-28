"""
This check validates whether the NXOS version on the device is 10.5(1).

Algorithm:
- Requests the "show version" command and receives its output from the Netaudit Engine.
- Parses the output to extract the reported NXOS version.
- Sets status to PASS if the version is 10.5(1), FAIL if it differs, 
  INCONCLUSIVE if the version cannot be determined from the output, or ERROR if an exception occurs.
"""

class NXOSVersionCheck:
    NAME = "NXOS Version - 10.5(1)"
    VERSION = "1.0.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["nxos", "version"]
    DESCRIPTION = "Verify whether the device OS is 10.5(1) or not using show version"
    COMPLEXITY = 1

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show version",
            "handler": "handle_version_check"
        }
        self.RESULTS = {
            "status": 0,
            "observation": "",
            "comments": []
        }

    def handle_version_check(self, device, cmd, output):
        """
        Parses the output of "show version" to check if NXOS version is 10.5(1).
        """
        try:
            # Use regex to extract the NXOS version
            import re
            version_regex = r"NXOS: version (\S+) .*"
            match = re.search(version_regex, output)

            if match:
                nxos_version = match.group(1)
                self.RESULTS["observation"] = f"NXOS version found: {nxos_version}"

                if nxos_version == "10.5(1)":
                    self.RESULTS["status"] = 1  # PASS
                    self.RESULTS["comments"].append(
                        f"Device is running the expected NXOS version: {nxos_version}."
                    )
                else:
                    self.RESULTS["status"] = 2  # FAIL
                    self.RESULTS["comments"].append(
                        f"Device is running NXOS version {nxos_version}, "
                        f"which does not match the expected version 10.5(1)"
                    )
            else:
                self.RESULTS["status"] = 6  # INCONCLUSIVE
                self.RESULTS["observation"] = "Unable to determine NXOS version from output."
                self.RESULTS["comments"].append("The version information could not be parsed. Please verify manually.")

        except Exception as e:
            self.RESULTS["status"] = 5  # ERROR
            self.RESULTS["observation"] = "An error occurred while analyzing the version output."
            self.RESULTS["comments"].append(f"Error details: {str(e)}")

        # Clear REQUESTS to indicate the check is done
        self.REQUESTS = {}


CHECK_CLASS = NXOSVersionCheck