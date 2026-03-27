# Android Armor Breaker

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue.svg)](https://clawhub.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org)
[![Frida](https://img.shields.io/badge/Frida-based-red.svg)](https://frida.re)

Android Armor Breaker - A Frida-based unpacking technology for commercial to enterprise-level Android application protection schemes, providing complete **APK reinforcement analysis** and **intelligent DEX extraction** solutions.

## 🚀 Features

- ✅ **APK Protection Analysis** - Static analysis of APK files, identifying protection vendors and protection levels
- ✅ **Environment Auto-check** - Automatically checks Frida environment, device connection, app installation status, root privileges
- ✅ **Intelligent Unpacking** - Selects optimal unpacking strategy based on protection level
- ✅ **Real-time Monitoring** - Tracks Dex file extraction process with live progress display
- ✅ **DEX Integrity Verification** - Verifies integrity and validity of generated DEX files
- ✅ **Enhanced Capabilities** - App warm-up mechanism, multiple unpacking attempts, dynamic loading detection, deep integrity verification

## 🛡️ Supported Protection Schemes

- ✅ **360 Protection** (Verified: Example App 1, 85 DEX files)
- ✅ **Bangbang Enterprise Edition** (Verified: Example App 2, 115 DEX files)
- ✅ **Bangbang Enterprise Lightweight** (Verified: Example App 3, 59 DEX files)
- ⚠️ **New Baidu Protection** (Theoretically supported, pending verification)
- ❌ **Mixed Protections** (360+Tencent, etc., current technical limitations)

## 📦 Quick Start

### Prerequisites
```bash
# Install Frida tools
pip install frida-tools

# Install ADB (Android Debug Bridge)
sudo apt-get install adb

# Ensure Android device is connected with USB debugging enabled
adb devices
```

### Basic Usage
```bash
# Analyze APK protection type (recommended first step)
android-armor-breaker analyze --apk app.apk --verbose

# Execute unpacking with deep search mode
android-armor-breaker --package com.example.app --deep-search --verbose

# Unpack with anti-debug bypass
android-armor-breaker --package com.example.app --bypass-antidebug --verbose
```

## 📊 Test Results

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

## 🔧 Technical Breakthroughs

### 1. **Memory Permission Modification**
- Breaks through `PROT_NONE` memory protection
- Solves memory access violation issues

### 2. **Frida Feature Hiding**
- File renaming, non-standard ports, function name obfuscation
- Avoids script destruction by protection schemes

### 3. **Anti-debug Bypass**
- Staged injection technique
- Breaks through enterprise-level anti-debugging protection

### 4. **Deep Search Mode**
- Discovers 100+ runtime DEX files from 1 static DEX
- Overcomes DEX count limitations in normal mode

### 5. **Deep Integrity Verification**
- Multi-dimensional verification (CRC32, SHA-1, MD5)
- Ensures extracted DEX files are complete and valid

## 🏗️ Project Structure

```
android-armor-breaker/
├── SKILL.md              # OpenClaw skill documentation
├── README.md             # Project documentation
├── LICENSE               # MIT License
├── _meta.json            # Skill metadata
├── scripts/              # Core Python scripts
│   ├── android-armor-breaker          # Main wrapper script
│   ├── apk_protection_analyzer.py     # APK protection analyzer
│   ├── enhanced_dexdump_runner.py     # Enhanced unpacking executor
│   └── antidebug_bypass.py            # Anti-debug bypass module
└── .clawhub/             # ClawHub publishing configuration
    └── origin.json       # Publishing source information
```

## 📝 Usage Examples

### APK Protection Analysis
```bash
# Basic analysis
android-armor-breaker analyze --apk /path/to/app.apk

# Verbose analysis with detailed report
android-armor-breaker analyze --apk /path/to/app.apk --verbose
```

### Application Unpacking
```bash
# Standard unpacking
android-armor-breaker --package com.example.app --verbose

# Deep search mode for commercial protections
android-armor-breaker --package com.example.app --deep-search --verbose

# With anti-debug bypass
android-armor-breaker --package com.example.app --bypass-antidebug --verbose

# Specify custom output directory
android-armor-breaker --package com.example.app --output ./dex_output/ --verbose
```

### Direct Python Script Usage
```bash
# APK protection analysis
python3 scripts/apk_protection_analyzer.py --apk app.apk --verbose

# Enhanced unpacking
python3 scripts/enhanced_dexdump_runner.py --package com.example.app --deep-search --verbose

# Anti-debug bypass
python3 scripts/antidebug_bypass.py --package com.example.app --verbose
```

## 🔍 Detailed Workflow

### Recommended Smart Workflow
```
1. 📥 Obtain APK file
2. 🔍 Analyze protection: android-armor-breaker analyze --apk app.apk
3. 📊 Review analysis report and recommendations
4. ⚡ Execute unpacking with recommended parameters
5. ✅ Verify extracted DEX files
```

### For Commercial Protections
```
# For apps with commercial protections (360, Bangbang, Baidu):
1. Use --deep-search parameter
2. Allow sufficient warm-up time (60+ seconds)
3. Consider multiple unpacking attempts
4. Enable --verbose for detailed progress
```

## ⚠️ Important Notes

### Prerequisites
- Rooted Android device with `frida-server` running
- USB debugging enabled
- Target application installed on device
- Python 3.8+ and Frida tools installed

### For New Baidu Protection
- **Must use deep search mode** (`--deep-search` or `-d` parameter)
- Allow at least 60 seconds for app warm-up
- Multiple unpacking attempts recommended
- Pay attention to dynamically loaded `baiduprotect*.dex` files

### Common Issues
- **Command fails**: Check if `frida-server` is running on device
- **No DEX files extracted**: Try deep search mode, increase wait time
- **Permission denied**: Ensure device is rooted and USB debugging authorized
- **Partial extraction**: Commercial protections may require multiple attempts

## 📚 Documentation

- **SKILL.md**: Complete OpenClaw skill documentation with installation, usage, and technical details
- **GitHub Repository**: https://github.com/Haoning199101/android-armor-breaker
- **ClawHub Page**: https://clawhub.ai/skill/android-armor-breaker

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Trx-HaoNing** - Security Researcher

## 🌟 Support

For questions, issues, or suggestions:
- Open an issue on [GitHub](https://github.com/Haoning199101/android-armor-breaker/issues)
- Contact through OpenClaw community
- Provide feedback via ClawHub platform

## 🔗 Related Projects

- [OpenClaw](https://github.com/openclaw/openclaw) - The platform this skill is built for
- [Frida](https://frida.re) - Dynamic instrumentation toolkit
- [Frida-dexdump](https://github.com/hluwa/frida-dexdump) - Base tool for DEX dumping

---

*Android Armor Breaker is part of the OpenClaw ecosystem, providing professional Android security analysis tools for security researchers and penetration testers.*