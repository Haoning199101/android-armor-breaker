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

# 国际化导入
from i18n_logger import get_logger

def setup_logger(language: str = 'en-US', verbose: bool = False):
    """设置国际化日志器"""
    return get_logger(language=language, verbose=verbose, module="android-armor-breaker")

def main():
    """Main entry point for Python wrapper"""
    # 解析语言参数
    language = 'en-US'
    verbose = False
    
    # 检查是否有语言参数
    for i, arg in enumerate(sys.argv[1:]):
        if arg in ['--language', '-l'] and i + 1 < len(sys.argv[1:]):
            language = sys.argv[i + 2]
        elif arg == '--verbose' or arg == '-v':
            verbose = True
    
    # 设置日志器
    logger = setup_logger(language=language, verbose=verbose)
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    bash_script = script_dir / "android-armor-breaker"
    
    if not bash_script.exists():
        logger.log("bash_script_not_found", "ERROR", path=str(bash_script))
        sys.exit(1)
    
    if not os.access(bash_script, os.X_OK):
        logger.log("bash_script_not_executable", "ERROR", path=str(bash_script))
        sys.exit(1)
    
    # Pass all arguments to the Bash script
    cmd = [str(bash_script)] + sys.argv[1:]
    
    try:
        logger.log("starting_bash_script", command=" ".join(cmd))
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            logger.log("bash_script_completed_successfully", "SUCCESS")
        else:
            logger.log("bash_script_failed", "ERROR", exit_code=result.returncode)
        
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        logger.log("operation_interrupted_by_user", "WARNING")
        sys.exit(130)
    except Exception as e:
        logger.log("bash_script_execution_error", "ERROR", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()