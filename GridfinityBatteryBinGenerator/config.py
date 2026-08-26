# Application Global Variables shared across modules.

import os

# Set True to write more information to the Text Command window.
DEBUG = False

ADDIN_NAME = 'GridfinityBatteryBinGenerator'

# Internal namespace for Fusion command IDs only - never shown to anyone.
# The published name is "Bryan Gravely" (installer/make_wxs.py and
# installer/PackageContents.xml), matching the code-signing certificate.
# Changing this only renames internal IDs, so it is left alone.
COMPANY_NAME = 'Gravlaxy'
