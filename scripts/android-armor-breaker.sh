#!/usr/bin/env bash
# Android Armor Breaker - Skill wrapper script
# APK reinforcement analysis and intelligent unpacking solution: static identification of mainstream reinforcement vendors, dynamic extraction of DEX files
# Supports deep search and anti-debug bypass, provides complete DEX integrity verification
# Provides simple command-line interface

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="${SCRIPT_DIR}/enhanced_dexdump_runner.py"
APK_ANALYZER="${SCRIPT_DIR}/apk_protection_analyzer.py"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    log_error "Cannot find Python execution script: $PYTHON_SCRIPT"
    exit 1
fi

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    log_error "Python3 not found, please install Python3 first"
    exit 1
fi

# Show help information
show_help() {
    cat << EOF
Android Armor Breaker - APK Reinforcement Analysis and Intelligent Unpacking Solution

Usage:
  android-armor-breaker [analyze|dump] [options]

Subcommands:
  analyze              Analyze reinforcement type of APK file
  dump                 Unpack Android application (default subcommand)

APK Analysis (analyze):
  android-armor-breaker analyze --apk <apk_file_path> [--verbose]

  -a, --apk <file_path>   APK file path (required)
  -v, --verbose          Verbose output mode

Application Unpacking (dump):
  android-armor-breaker dump [options] <package_name>
  or
  android-armor-breaker [options] <package_name> (short form)

  -p, --package <package_name>    Android application package name (required)
  -o, --output <directory>        Output directory (default: ./dex_output)
  -d, --deep-search               Deep search mode (for strong protections like new Baidu reinforcement)
  -b, --bypass-antidebug          Enable anti-debug bypass (for strong anti-debug protection)
  -v, --verbose                   Verbose output mode

Examples:
  # Analyze APK reinforcement type
  android-armor-breaker analyze --apk ./app.apk --verbose

  # Unpack application (full form)
  android-armor-breaker dump --package com.example.app --deep-search

  # Unpack application (short form - backward compatible)
  android-armor-breaker --package com.example.app --output ./output/
  android-armor-breaker -p com.example.app -o ./dex_output/ -v

Skill Features:
  1. 🔍 APK Reinforcement Analysis (analyze subcommand)
  2. ⚡ Intelligent Unpacking Strategy (Frida-based deep search and anti-debug bypass)
  3. 🛡️ Anti-debug Bypass (--bypass-antidebug)
  4. 📊 DEX Integrity Verification
  5. 📄 Generate Detailed Execution Report

Recommended Workflow:
  1. First analyze APK: android-armor-breaker analyze --apk app.apk
  2. Select unpacking parameters based on analysis results
  3. Execute unpacking: android-armor-breaker --package <package_name> [parameters]
EOF
}

show_analyze_help() {
    cat << EOF
APK Reinforcement Analysis Tool

Usage:
  android-armor-breaker analyze --apk <apk_file_path> [options]

Options:
  -a, --apk <file_path>   APK file path (required)
  -v, --verbose          Verbose output mode
  -h, --help             Show this help message

Examples:
  android-armor-breaker analyze --apk ./app.apk
  android-armor-breaker analyze --apk /path/to/app.apk --verbose

Output:
  - Console displays reinforcement analysis report
  - Generates JSON format detailed report: <apk_filename>_protection_analysis.json
EOF
}

show_dump_help() {
    cat << EOF
Android Application Unpacking Tool

Usage:
  android-armor-breaker dump [options] <package_name or APK file>
  or
  android-armor-breaker [options] <package_name or APK file> (short form)

Options:
  -p, --package <package_name>    Android application package name (mutually exclusive with --apk)
  -a, --apk <APK_file>            APK file path (automatically analyzes reinforcement and extracts package name)
  -o, --output <directory>        Output directory (default: ./dex_output)
  -d, --deep-search               Deep search mode (for strong protections like new Baidu reinforcement)
  -b, --bypass-antidebug          Enable anti-debug bypass (for strong anti-debug protection)
  -v, --verbose                   Verbose output mode
  -h, --help                      Show this help message

Description:
  - If --apk parameter is specified, automatically analyzes APK reinforcement:
      * If no reinforcement: directly extracts static DEX files
      * If reinforced: executes dynamic unpacking (requires application to be installed)
  - If --package parameter is specified, directly executes dynamic unpacking

Examples:  android-armor-breaker dump --apk ./app.apk --output ./app_dex/
  android-armor-breaker --apk /path/to/app.apk -v
  android-armor-breaker dump --package com.example.app
  android-armor-breaker --package com.example.app --output ./dex_output/
  android-armor-breaker -p com.example.app -o ./dump/ -v
  android-armor-breaker --package cn.ninebot.ninebot --bypass-antidebug
EOF
}

# Check if APK analyzer exists
check_apk_analyzer() {
    if [ ! -f "$APK_ANALYZER" ]; then
        log_error "Cannot find APK analysis tool: $APK_ANALYZER"
        log_info "Please ensure apk_protection_analyzer.py is in the scripts directory"
        exit 1
    fi
}

# APK analysis function
analyze_apk() {
    local APK_PATH=""
    local VERBOSE=false
    
    # Parse analyze subcommand parameters
    shift  # Remove "analyze"
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--apk)
                APK_PATH="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_analyze_help
                exit 0
                ;;
            *)
                log_error "Unknown parameter: $1"
                show_analyze_help
                exit 1
                ;;
        esac
    done
    
    # Validate parameters
    if [ -z "$APK_PATH" ]; then
        log_error "Please specify APK file path"
        show_analyze_help
        exit 1
    fi
    
    if [ ! -f "$APK_PATH" ]; then
        log_error "APK file does not exist: $APK_PATH"
        exit 1
    fi
    
    # Execute analysis
    check_apk_analyzer
    
    log_info "Starting APK analysis: $(basename "$APK_PATH")"
    
    if [ "$VERBOSE" = true ]; then
        python3 "$APK_ANALYZER" --apk "$APK_PATH" --verbose
    else
        python3 "$APK_ANALYZER" --apk "$APK_PATH"
    fi
}

# Unpacking function (original functionality)
dump_apk() {
    local PACKAGE_NAME=""
    local OUTPUT_DIR="./dex_output"
    local DEEP_SEARCH=false
    local BYPASS_ANTIDEBUG=false
    local VERBOSE=false
    
    # If it's the dump subcommand, remove the first parameter
    if [ "$1" = "dump" ]; then
        shift
    fi
    
    # Parse parameters (compatible with original syntax)
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--package)
                PACKAGE_NAME="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -d|--deep-search)
                DEEP_SEARCH=true
                shift
                ;;
            -b|--bypass-antidebug)
                BYPASS_ANTIDEBUG=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -t|--detect-protection)
                log_warning "⚠️  --detect-protection parameter is deprecated"
                log_info "💡 Please use the new command to analyze APK: android-armor-breaker analyze --apk <apk_file_path>"
                shift
                ;;
            -h|--help)
                show_dump_help
                exit 0
                ;;
            *)
                # If -p/--package is not specified, treat the first non-option parameter as package name
                if [ -z "$PACKAGE_NAME" ]; then
                    PACKAGE_NAME="$1"
                    shift
                else
                    log_warning "Unknown parameter: $1"
                    shift
                fi
                ;;
        esac
    done
    
    # Validate required parameters
    if [ -z "$PACKAGE_NAME" ]; then
        log_error "Please specify application package name"
        echo ""
        show_dump_help
        exit 1
    fi
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    # Display execution information
    log_info "Target application: $PACKAGE_NAME"
    log_info "Output directory: $OUTPUT_DIR"
    
    if [ "$DEEP_SEARCH" = true ]; then
        log_info "Deep search mode: Enabled"
    fi
    if [ "$BYPASS_ANTIDEBUG" = true ]; then
        log_info "Anti-debug bypass: Enabled"
    fi
    if [ "$VERBOSE" = true ]; then
        log_info "Verbose mode: Enabled"
    fi
    
    # Build Python command arguments
    local PYTHON_ARGS="--package $PACKAGE_NAME --output $OUTPUT_DIR"
    
    if [ "$DEEP_SEARCH" = true ]; then
        PYTHON_ARGS="$PYTHON_ARGS --deep-search"
    fi
    if [ "$BYPASS_ANTIDEBUG" = true ]; then
        PYTHON_ARGS="$PYTHON_ARGS --bypass-antidebug"
    fi
    if [ "$VERBOSE" = true ]; then
        PYTHON_ARGS="$PYTHON_ARGS --verbose"
    fi
    
    # Execute Python script
    log_info "Starting unpacking..."
    python3 "$PYTHON_SCRIPT" $PYTHON_ARGS
    
    # Check execution result
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "Unpacking task completed!"
        log_info "DEX files saved to: $OUTPUT_DIR"
    else
        log_error "Unpacking task failed (exit code: $EXIT_CODE)"
        exit $EXIT_CODE
    fi
}

# Main function
main() {
    # If no arguments, show help
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # Check if the first parameter is a subcommand
    case "$1" in
        analyze)
            analyze_apk "$@"
            ;;
        dump)
            dump_apk "$@"
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            # If no subcommand, default to unpacking function (backward compatible)
            # Check if parameter is a package name (does not start with -)
            if [[ "$1" == -* ]]; then
                # It's an option, execute unpacking
                dump_apk "$@"
            else
                # Might be a package name, check if it contains . character (package name feature)
                if [[ "$1" == *.* ]]; then
                    log_info "Detected package name format, executing unpacking function"
                    dump_apk "$@"
                else
                    # Unknown command
                    log_error "Unknown command: $1"
                    echo ""
                    show_help
                    exit 1
                fi
            fi
            ;;
    esac
}

# Execute main function
main "$@"