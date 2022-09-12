import json
import os


__version__ = "UNKNOWN"
with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".version.json")
) as version_file:
    __version__ = json.load(version_file)["version"]
