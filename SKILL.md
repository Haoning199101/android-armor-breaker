---
name: android-armor-breaker
description: Android Armor Breaker - Frida-based unpacking technology for commercial to enterprise Android app protections, providing complete APK reinforcement analysis and intelligent DEX extraction solutions.
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["frida-dexdump", "python3", "adb"] },
        "install":
          [
            {
              "id": "frida-tools",
              "kind": "pip",
              "package": "frida-tools",
              "bins": ["frida", "frida-dexdump"],
              "label": "Install Frida Tools",
            },
            {
              "id": "python3",
              "kind": "apt",
              "package": "python3",
              "bins": ["python3"],
              "label": "Install Python3",
            },
            {
              "id": "adb",
              "kind": "apt",
              "package": "adb",
              "bins": ["adb"],
              "label": "Install Android Debug Bridge",
            },
          ],
      },
  }
---

## 1. Name
**android-armor-breaker**

## 2. Description
**Android Armor Breaker** - A Frida-based unpacking technology for the OpenClaw platform, targeting commercial to enterprise-level Android application protection schemes, providing complete **APK reinforcement analysis** and **intelligent DEX extraction** solutions.

**Frida Unpacking Technology**: Commercial-grade reinforcement breakthrough solutions based on the Frida framework, supporting advanced features like deep search, anti-debug bypass, etc.

**Core Features**:
1. ✅ **APK Reinforcement Analysis** - Static analysis of APK files, identifying protection vendors and protection levels
2. ✅ **Environment Check** - Automatic checking of Frida environment, device connection, app installation status, root privileges
3. ✅ **Intelligent Unpacking** - Automatically selects the best unpacking strategy based on protection level
4. ✅ **Real-time Monitoring Interface** - Tracks Dex file extraction process and displays progress in real-time
5. ✅ **DEX Integrity Verification** - Verifies the integrity and validity of generated DEX files

**Enhanced Features (for commercial protections)**:
6. ✅ **Application Warm-up Mechanism** - Wait + simulated operations to trigger more DEX loading
7. ✅ **Multiple Unpacking Attempts** - Unpacking at multiple time points, merging results to improve coverage
8. ✅ **Dynamic Loading Detection** - Specifically detects dynamically loaded files like `baiduprotect*.dex`
9. ✅ **Deep Integrity Verification** - Multi-dimensional verification including file headers, size, Baidu protection features, etc.

## 3. Installation

### 3.1 Automatic Installation via OpenClaw
This skill is configured with automatic dependency installation. When installed through the OpenClaw skill system, it will automatically detect and install the following dependencies:

1. **Frida Tools Suite** (`frida-tools`) - Includes `frida` and `frida-dexdump` commands
2. **Python3** - Script runtime environment
3. **Android Debug Bridge** (`adb`) - Device connection tool

### 3.2 Manual Dependency Installation
If not installed via OpenClaw, please manually install the following dependencies:

```bash
# Install Frida tools
pip install frida-tools

# Install Python3 (if not installed)
sudo apt-get install python3 python3-pip

# Install ADB
sudo apt-get install adb

# Run frida-server on Android device
# 1. Download frida-server for the correct architecture
# 2. Push to device: adb push frida-server /data/local/tmp/
# 3. Set permissions and run: adb shell "chmod 755 /data/local/tmp/frida-server && /data/local/tmp/frida-server"
```

### 3.3 Skill File Structure
After installation, the skill file structure is as follows:
```
android-armor-breaker/
├── SKILL.md              # Skill documentation
├── _meta.json            # Skill metadata
├── LICENSE               # MIT License
├── scripts/              # Execution script directory
│   ├── android-armor-breaker          # Main wrapper script
│   ├── apk_protection_analyzer.py     # APK protection analyzer
│   ├── enhanced_dexdump_runner.py     # Enhanced unpacking executor
│   └── antidebug_bypass.py            # Anti-debug bypass module
└── .clawhub/             # ClawHub publishing configuration
    └── origin.json       # Publishing source information
```

## 4. Key Commands

Android Armor Breaker provides a **subcommand system**, supporting two core functions: `analyze` (APK protection analysis) and `dump` (application unpacking).

### 4.1 APK Protection Analysis (analyze subcommand)
**Analyze First, Then Unpack** - Recommended workflow: First analyze APK protection type, then select the best unpacking strategy based on analysis results.

```bash
# Basic usage
android-armor-breaker analyze --apk <apk_file_path>

# Verbose output mode
android-armor-breaker analyze --apk <apk_file_path> --verbose

# Example: Analyze example app APK
android-armor-breaker analyze --apk /path/to/example_app.apk --verbose
```

**Output Results**:
- Console displays protection analysis report (protection type, protection level, confidence)
- Generates JSON format detailed report: `<apk_filename>_protection_analysis.json`
- Provides unpacking strategy recommendations (recommended parameters, estimated success rate, estimated time)

### 4.2 Application Unpacking (dump subcommand)
**Frida Unpacking Technology** - Commercial-grade reinforcement breakthrough solutions based on the Frida framework.

```bash
# Complete syntax
android-armor-breaker dump --package <package_name> [options]

# Enable deep search mode (for commercial protections)
android-armor-breaker dump --package <package_name> --deep-search --verbose

# Enable anti-debug bypass (for strong anti-debugging)
android-armor-breaker dump --package <package_name> --bypass-antidebug --verbose
```

### 4.3 Shorthand Syntax (Backward Compatible)
```bash
# Shorthand form (automatically recognized as dump command)
android-armor-breaker --package <package_name> --output ./dex_output/

# Deep search mode
android-armor-breaker --package <package_name> --deep-search --verbose

# Anti-debug bypass
android-armor-breaker --package <package_name> --bypass-antidebug

# Deprecated parameters (shows warning, recommend using analyze subcommand)
android-armor-breaker --package <package_name> --detect-protection
```

### 4.4 Recommended Workflow
```
📋 Smart Workflow (Recommended):
1. 📥 Obtain APK file
2. 🔍 android-armor-breaker analyze --apk app.apk
3. 📊 View protection analysis report and unpacking recommendations
4. ⚡ Execute unpacking based on recommendations: android-armor-breaker --package <package_name> [corresponding parameters]
```

### 4.5 Direct Python Script Usage
```bash
# APK protection analysis tool
python3 scripts/apk_protection_analyzer.py --apk <apk_file_path> --verbose

# Enhanced unpacking executor
python3 scripts/enhanced_dexdump_runner.py --package <package_name> --deep-search --verbose

# Anti-debug bypass module
python3 scripts/antidebug_bypass.py --package <package_name> --verbose
```

## 5. Supported Protection Schemes

- ✅ 360 Protection (Verified: Example App 1, 85 DEX files)
- ✅ Bangbang Enterprise Edition (Verified: Example App 2, 115 DEX files)
- ✅ Bangbang Enterprise Edition Lightweight (Verified: Example App 3, 59 DEX files)
- ⚠️ New Baidu Protection (Theoretically supported, pending verification)
- ❌ Mixed Protections (360+Tencent, etc., current technical limitations)

## 6. Testing Results

Based on actual testing from March 18-19, 2026:

| Application | Protection Type | DEX Count | Result |
|------------|----------------|-----------|--------|
| Example App 1 | 360 Protection | 85 | ✅ Success |
| Example App 2 | Bangbang Enterprise | 115 | ✅ Success |
| Example App 3 | Bangbang Enterprise | 59 | ✅ Success |
| Example App 4 | 360+Tencent Mixed | 0 | ❌ Failure |

**Success Rate**: 75% (3/4 applications successful)
**Total DEX Files**: 259
**Total File Size**: Approximately 1.6GB

## 7. Technical Implementation Details

### 7.1 Optimization Strategies for New Baidu Protection
- **Deep Search Mode (-d parameter)**: For strong protections like new Baidu protection, use `-d` parameter for more thorough memory scanning, breaking through DEX count limits in normal mode
- **Multiple Unpacking Attempts**: Execute unpacking at different time points after application startup to capture dynamically loaded DEX
- **Application Warm-up Mechanism**: Simulate user operations to trigger more functionality loading
- **Dynamic Loading Detection**: Special attention to dynamically loaded protection files like `baiduprotect*.dex`
- **Deep Integrity Verification**: Multi-dimensional verification of DEX file validity

### 7.2 Core Algorithms
```python
# Multiple unpacking attempt merging algorithm
def merge_dex_files(self, all_dex_lists: List[List[Dict]]) -> List[Dict]:
    """Merge results from multiple unpacking attempts, deduplicate"""
    unique_dex_files = {}
    for dex_list in all_dex_lists:
        for dex_info in dex_list:
            md5 = dex_info['md5']
            if md5 not in unique_dex_files:
                unique_dex_files[md5] = dex_info
    return list(unique_dex_files.values())

# DEX integrity verification algorithm
def verify_dex_header(self, dex_file: Path) -> bool:
    """Verify DEX file header"""
    with open(dex_file, 'rb') as f:
        header = f.read(4)
        return header in [b'dex\n', b'dey\n']

### 7.3 Complete DEX File Verification (Enhanced Version)
New complete verification features include:

1. **CRC32 Verification**: Verify CRC32 checksum at offset 0x8 in DEX file header
2. **SHA-1 Signature Verification**: Verify 20-byte SHA-1 signature at offset 0xC
3. **MD5 Match Verification**: Recalculate file MD5 and compare with frida-dexdump output MD5
4. **DEX Structure Verification**: Verify string table, type table offsets in file header are valid
5. **File Size Verification**: Verify file size field matches actual file size

**Verification Algorithm Example**:
```python
def _verify_dex_complete(self, dex_path: Path, expected_md5: str = None) -> Dict:
    """Complete DEX file verification"""
    # 1. CRC32 verification
    expected_crc32 = struct.unpack('<I', data[8:12])[0]
    actual_crc32 = zlib.crc32(data[12:]) & 0xffffffff
    
    # 2. SHA-1 verification  
    expected_sha1 = data[12:32]
    actual_sha1 = hashlib.sha1(data[32:]).digest()
    
    # 3. MD5 verification
    actual_md5 = hashlib.md5(data).hexdigest()
    
    # 4. DEX structure verification
    string_ids_size = struct.unpack('<I', data[0x38:0x3c])[0]
    string_ids_off = struct.unpack('<I', data[0x3c:0x40])[0]
    
    return {
        'crc32_valid': expected_crc32 == actual_crc32,
        'sha1_valid': expected_sha1 == actual_sha1,
        'md5_match': actual_md5.lower() == expected_md5.lower() if expected_md5 else None
    }
```

## 8. Usage Examples

### 8.1 APK Protection Analysis Example (Recommended: Analyze First, Then Unpack)
```bash
# Analyze APK protection type
android-armor-breaker analyze --apk /path/to/app.apk --verbose

# Analyze example app APK (test case)
android-armor-breaker analyze --apk /path/to/example_app.apk --verbose

# Analysis results:
# 📊 Protection Type: ALI (Ali Protection)
# 🛡️ Protection Level: COMMERCIAL (Commercial Level)
# 💡 Recommendation: Use deep search mode for unpacking
```

### 8.2 Intelligent Unpacking Example (Select Parameters Based on Analysis Results)
```bash
# Execute unpacking based on analysis results (commercial-level protection)
android-armor-breaker --package com.example.app --deep-search --verbose

# For strong anti-debugging protection
android-armor-breaker --package com.example.app --bypass-antidebug --verbose

# Frida unpacking standard mode
android-armor-breaker --package com.example.app --verbose

# Specify output directory
android-armor-breaker --package com.example.app --output ./dex_output/ --verbose
```

### 8.3 Unpacking an Application (Normal Mode)
```bash
python3 scripts/enhanced_dexdump_runner.py \
  --package <package_name> \
  --output ./dump_dex/ \
  --attempts 3 \
  --verbose
```

### 8.4 New Baidu Protection Application Unpacking (Deep Search Mode)
```bash
# For strong protections like new Baidu protection, must use deep search mode
python3 scripts/enhanced_dexdump_runner.py \
  --package <package_name> \
  --output ./deep_output/ \
  --deep-search \
  --attempts 3 \
  --verbose

# Direct frida-dexdump command (equivalent to above Python script)
frida-dexdump -U -f <package_name> -d -o ./direct_output/
```

## 9. Technical Breakthroughs

1. **Memory Permission Modification** - Break through `PROT_NONE` memory protection, solving access violation issues
2. **Frida Feature Hiding** - Rename files, non-standard ports, function name obfuscation to avoid script destruction
3. **Anti-debug Bypass** - Staged injection to break through enterprise-level anti-debugging protection
4. **Deep Search Mode** - Discover 100+ runtime DEX files from 1 static DEX
5. **Deep Integrity Verification** - Multi-dimensional verification with CRC32, SHA-1, MD5 checks

## 10. Notes and Requirements

1. **New Feature Explanation**:
   - **APK Protection Analysis**: New `analyze` subcommand, supports static analysis of APK protection types
   - **Smart Workflow**: Recommended to analyze APK first, then select unpacking parameters based on results
   - **Deprecated Parameters**: `--detect-protection` parameter deprecated, please use `analyze` subcommand
   - **Backward Compatibility**: Original unpacking command syntax fully compatible, new `dump` subcommand syntax added

2. **Environment Requirements**:
   - `frida-dexdump` tool installed (`pip install frida-tools`)
   - Android device connected via USB with debugging enabled
   - Target application installed on device

3. **Execution Prerequisites**:
   - `frida-server` running on device (requires root privileges)
   - Correct application package name and application can start normally
   - For commercial protection applications, recommend using enhanced scripts

4. **For New Baidu Protection**:
   - Must use **deep search mode (-d parameter)** to break through DEX count limits
   - Need sufficient waiting time for application to fully load (recommend 60+ seconds)
   - Multiple unpacking attempts can improve DEX file coverage
   - Pay attention to dynamically loaded protection files like `baiduprotect*.dex`

5. **Deep Search Mode**:
   - Use `-d` parameter for deep search: `frida-dexdump -U -f <package_name> -d -o ./output/`
   - Suitable for strong protections like new Baidu protection, Tencent protection
   - More thorough search but longer time (multiple rounds of scanning)
   - Can discover deep DEX files not found in normal mode

6. **Common Issues**:
   - If command fails, check if `frida-server` is running
   - Ensure correct application package name, use `adb shell pm list packages` to check
   - First connection may require USB debugging authorization
   - Commercial protection applications may require more waiting time and attempts
   - If normal mode only obtains partial DEX, switch to deep search mode

7. **Output Files**:
   - Default generates `*.dex` files in current directory
   - Use `-o` parameter to specify output directory
   - Multi-DEX applications generate multiple files (classes.dex, classes2.dex, etc.)
   - Enhanced version generates detailed report `enhanced_dexdump_report.md`

## 11. License

MIT License - See [LICENSE](LICENSE) file for details.

## 12. Author

Trx-HaoNing - Security Researcher

## 13. Support

For issues or suggestions, please provide feedback through the OpenClaw community.