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
              "label": "Install Frida Tools Suite",
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
**Android Armor Breaker** - Frida-based unpacking technology for the OpenClaw platform, targeting commercial to enterprise-level Android application protection solutions, providing complete **APK Reinforcement Analysis** and **Intelligent DEX Extraction** solutions.

**Frida Unpacking Technology**: Commercial-grade reinforcement breakthrough solution based on the Frida framework, supporting advanced features like deep search, anti-debug bypass, etc.

**Core Features**:
1. ✅ **APK Reinforcement Analysis** - Static analysis of APK files to identify reinforcement vendors and protection levels
2. ✅ **Environment Check** - Automatically checks Frida environment, device connection, app installation status, Root permissions
3. ✅ **Intelligent Unpacking** - Automatically selects the best unpacking strategy based on protection level
4. ✅ **Real-time Monitoring Interface** - Tracks DEX file extraction process, displays progress in real-time
5. ✅ **DEX Integrity Verification** - Verifies the integrity and validity of generated DEX files

**Enhanced Features (for commercial reinforcement)**:
6. ✅ **Application Warm-up Mechanism** - Waits + simulates operations to trigger more DEX loading
7. ✅ **Multiple Unpacking Attempts** - Unpacks at multiple time points, merges results to improve coverage
8. ✅ **Dynamic Loading Detection** - Specifically detects dynamically loaded files like baiduprotect*.dex
9. ✅ **Deep Integrity Verification** - Multi-dimensional verification including file headers, size, Baidu protection features, etc.

## 3. Installation

### 3.1 Automatic Installation via OpenClaw
This skill is configured for automatic dependency installation. When installed through the OpenClaw skill system, it will automatically detect and install the following dependencies:

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
# 1. Download frida-server for the corresponding architecture
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
├── scripts/              # Execution scripts directory
│   ├── android-armor-breaker          # Main wrapper script
│   ├── apk_protection_analyzer.py     # APK reinforcement analyzer
│   ├── enhanced_dexdump_runner.py     # Enhanced unpacking executor
│   └── antidebug_bypass.py            # Anti-debug bypass module
└── .clawhub/             # ClawHub publishing configuration
    └── origin.json       # Publishing source information
```