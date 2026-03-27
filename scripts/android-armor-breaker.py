#!/usr/bin/env python3
"""
Android Armor Breaker - Python wrapper script

This is a Python wrapper that calls the main Bash script for compatibility
with clawhub packaging system.

For direct usage, use the Bash script: ./android-armor-breaker
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point for Python wrapper"""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    bash_script = script_dir / "android-armor-breaker"
    
    if not bash_script.exists():
        print(f"Error: Main Bash script not found: {bash_script}")
        sys.exit(1)
    
    if not os.access(bash_script, os.X_OK):
        print(f"Error: Bash script not executable: {bash_script}")
        sys.exit(1)
    
    # Pass all arguments to the Bash script
    cmd = [str(bash_script)] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error executing Bash script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()