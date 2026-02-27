"""
config.py — Application-wide constants.
"""

import re

# Matches: /aurora-profile-by-toon/{player_id}/{gateway_number}
SCR_PATTERN = re.compile(r'/aurora-profile-by-toon/([^/?]+)/\d+')

__version__ = "1.0.0"