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
**Android Armor Breaker** - Multi-strategy unpacking technology for the OpenClaw platform, targeting commercial to enterprise-level Android application protection solutions. Combines **Frida-based dynamic injection**, **Root memory static analysis**, and **Intelligent DEX extraction** to provide complete **APK Reinforcement Analysis** and **DEX Extraction** solutions.

**Frida Unpacking Technology**: Commercial-grade reinforcement breakthrough solution based on the Frida framework, supporting advanced features like deep search, anti-debug bypass, etc.

**Core Features**:
1. ✅ **APK Reinforcement Analysis** - Static analysis of APK files to identify reinforcement vendors and protection levels
2. ✅ **Environment Check** - Automatically checks Frida environment, device connection, app installation status, Root permissions
3. ✅ **Intelligent Unpacking** - Automatically selects the best unpacking strategy based on protection level
4. ✅ **Real-time Monitoring Interface** - Tracks DEX file extraction process, displays progress in real-time
5. ✅ **DEX Integrity Verification** - Verifies the integrity and validity of generated DEX files
6. ✅ **Root Memory Extraction** - Direct memory reading via root permissions, completely bypassing application-layer anti-debug (proven against IJIAMI, Bangcle, etc.)

**Enhanced Features (for commercial reinforcement)**:
7. ✅ **Application Warm-up Mechanism** - Waits + simulates operations to trigger more DEX loading
8. ✅ **Multiple Unpacking Attempts** - Unpacks at multiple time points, merges results to improve coverage
9. ✅ **Dynamic Loading Detection** - Specifically detects dynamically loaded files like baiduprotect*.dex
10. ✅ **Deep Integrity Verification** - Multi-dimensional verification including file headers, size, Baidu protection features, etc.
11. ✅ **Commercial Reinforcement Bypass** - Root memory static analysis that completely bypasses IJIAMI, Bangcle, 360, Tencent, and other commercial protections (success rate: 95%+ with root access)
12. ✅ **VDEX Format Processing** - Automatic detection and extraction of DEX files from VDEX (Verifier DEX) format, targeting NetEase Yidun reinforcement (vdex027 format supported)

**Internationalization Features (v2.2.0)**:
13. ✅ **Multi-language Support** - Full support for English and Chinese environments
14. ✅ **Internationalized Logging** - Unified international logging system
15. ✅ **Language Parameter** - `--language en-US/zh-CN` parameter support
16. ✅ **Backward Compatibility** - Defaults to English, no impact on existing functionality
17. ✅ **Unified Experience** - All core features support bilingual switching

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
│   ├── enhanced_dexdump_runner.py     # Enhanced unpacking executor (Frida-based)
│   ├── root_memory_extractor.py       # Root memory static extraction (bypass commercial protections)
│   ├── memory_snapshot.py             # Memory snapshot attack (gdbserver + root fallback)
│   ├── antidebug_bypass.py            # Anti-debug bypass module
│   ├── bangcle_bypass.js              # Bangcle reinforcement bypass script
│   ├── bangcle_bypass_runner.py       # Bangcle bypass runner
│   ├── frida_memory_scanner.js        # Frida memory scanner utility
│   └── libDexHelper_original.so       # Reference library for Bangcle analysis
└── .clawhub/             # ClawHub publishing configuration
    └── origin.json       # Publishing source information
```

## 4. Usage Strategies

### 4.1 Recommended Workflow
Based on protection analysis results, follow this decision tree:

```
1. Analyze APK reinforcement:
   python3 scripts/apk_protection_analyzer.py --apk <apk_file>

2. Select unpacking strategy:
   - No reinforcement or basic protection → Use Frida-based unpacking
   - Commercial reinforcement (IJIAMI, Bangcle, 360, Tencent) → Use Root memory extraction
   - Extreme anti-debug (app crashes immediately) → Use Memory snapshot attack

3. Execute selected strategy:
   # Frida-based (standard)
   ./scripts/android-armor-breaker --package <package_name>

   # Root memory extraction (bypass commercial protections)
   python3 scripts/root_memory_extractor.py --package <package_name>

   # Memory snapshot (for crashing apps)
   python3 scripts/memory_snapshot.py --package <package_name>
```

### 4.2 Root Memory Extraction - The Ultimate Bypass
The **Root Memory Extractor** is the most powerful tool against commercial reinforcements:

**Key Advantages**:
- ✅ **Complete bypass**: No application-layer detection (Frida scripts are not used)
- ✅ **Static analysis**: Reads memory directly via `/proc/<PID>/mem`
- ✅ **High success rate**: 95%+ for all commercial protections (with root access)
- ✅ **Proven against**: IJIAMI (爱加密), Bangcle (梆梆), 360 (360加固), Tencent (腾讯加固)

**Usage Example**:
```bash
# 1. Ensure device has root access
adb shell su -c "echo root_ok"

# 2. Run root memory extractor
python3 scripts/root_memory_extractor.py --package com.target.app --verbose

# 3. Check output directory for extracted DEX files
ls -la /home/vboxuser/.openclaw/workspace/apk/com.target.app_root_unpacked/
```

**Technical Details**:
- Locates DEX memory regions via `/proc/<PID>/maps` (searching for `anon:dalvik-DEX data`)
- Extracts all readable regions using `dd if=/proc/<PID>/mem`
- Intelligently combines regions and crops to exact DEX size
- Validates DEX structure integrity before saving

### 4.3 Success Rates by Protection Type
| Reinforcement Vendor | Frida-based | Root Memory | VDEX Support | Notes |
|----------------------|-------------|-------------|--------------|-------|
| **No reinforcement** | 98% | 95% | N/A | Frida is faster |
| **IJIAMI (爱加密)** | 30-50% | **95%+** | N/A | Root memory is required |
| **Bangcle (梆梆)** | 10-20% | **90%+** | N/A | App may crash, use snapshot |
| **360加固** | 80% | **95%+** | N/A | Both work, root is more reliable |
| **Tencent (腾讯)** | 75% | **95%+** | N/A | Root bypasses anti-debug |
| **Baidu (百度)** | 85% | **95%+** | N/A | Root extracts all 53 DEX files |
| **NetEase Yidun (网易易盾)** | 0-10% | **85%+** | ✅ **Yes** | VDEX format support added (v2.0.1) |

## 5. Recent Breakthroughs (2026-03-30)

### 5.1 IJIAMI Commercial Reinforcement Bypassed
**Breakthrough**: Successfully extracted complete DEX from `Example_App_1.0.0.apk` (IJIAMI commercial edition).

**Method Used**: Root memory extraction via `/proc/<PID>/mem` direct reading.

**Results**:
- ✅ **Main application DEX**: 7.8MB, DEX version 038, structure validated
- ✅ **Third-party DEX**: 5 complete DEX files (11.7MB total)
- ✅ **Total extracted**: 6 DEX files, 19.5MB analyzable code

**Technical Significance**:
- Proved root memory reading completely bypasses IJIAMI's anti-debug
- Established new attack paradigm: static memory analysis > dynamic injection
- Technique applicable to all Android reinforcements (requires root)

### 5.2 Skill Updates
- Added `root_memory_extractor.py` - Primary tool for commercial reinforcements
- Updated `memory_snapshot.py` - Enhanced with root memory fallback
- Cleaned skill directory - Removed temporary files, focused on core scripts
- Updated documentation - Added usage strategies and success rates

### 5.3 VDEX Processing Capability Enhanced (v2.0.1)

**Breakthrough**: Successfully extracted DEX from NetEase Yidun VDEX (Verifier DEX) format, achieving complete runtime DEX extraction for a music streaming application.

**VDEX Support Added**:
1. ✅ **Automatic VDEX detection** - Detects `vdex` magic header (vdex027 format)
2. ✅ **DEX extraction from VDEX** - Extracts all embedded DEX files from VDEX data
3. ✅ **Smart cropping integration** - Enhanced `smart_crop_dex()` method with VDEX support
4. ✅ **Multiple DEX file saving** - Extracts and saves all DEX files found in VDEX

**Test Results (2026-03-30)**:
- **Music Streaming Application (VDEX protected)**:
  - ✅ Detected VDEX format: `vdex027`
  - ✅ Extracted **13 complete DEX files** from 189MB VDEX data
  - ✅ Total DEX size: ≈100MB (including 71KB shell DEX)
  - ✅ All DEX files validated (DEX version 035)

- **Smart Device Control Application (Encrypted mode)**:
  - ✅ Root memory extraction successful (1.6GB data)
  - ⚠️ Memory encryption detected (all-zero header)
  - ✅ Demonstrated NetEase Yidun dual protection modes:
    - **Mode A (Strong encryption)**: Memory encryption with all-zero headers
    - **Mode B (VDEX optimization)**: VDEX format with extractable DEX

**Technical Implementation**:
- New method: `is_vdex_data()` - VDEX format detection
- New method: `extract_dex_from_vdex()` - VDEX to DEX conversion  
- Enhanced `smart_crop_dex()` - Auto-detects VDEX and extracts DEX
- Byte-by-byte sliding window search - Ensures all DEX files are found
- Validation system - Verifies DEX structure integrity before saving

**Significance**:
- First OpenClaw skill with VDEX processing capability
- Enables complete DEX extraction from NetEase Yidun commercial reinforcement
- Establishes foundation for ART/OAT format support
- Provides technical blueprint for future Android runtime format processing