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
              "label": "安装Frida工具套件",
            },
            {
              "id": "python3",
              "kind": "apt",
              "package": "python3",
              "bins": ["python3"],
              "label": "安装Python3",
            },
            {
              "id": "adb",
              "kind": "apt",
              "package": "adb",
              "bins": ["adb"],
              "label": "安装Android调试桥",
            },
          ],
      },
  }
---

## 1. 名称
**android-armor-breaker**

## 2. 描述
**Android应用护甲破坏者** - 基于OpenClaw平台的Frida脱壳技术，针对从商业级到企业级的Android应用保护方案，提供**APK加固分析**与**DEX智能提取**的完整解决方案。

**Frida脱壳技术**：基于Frida框架的商业级加固突破方案，支持深度搜索、反调试绕过等高级功能。

**核心功能**：
1. ✅ **APK加固分析** - 静态分析APK文件，识别加固厂商和保护级别
2. ✅ **环境检查** - 自动检查Frida环境、设备连接、应用安装状态、Root权限
3. ✅ **智能脱壳** - 根据保护级别自动选择最佳脱壳策略
4. ✅ **实时监控界面** - 追踪Dex文件提取过程，实时显示进度
5. ✅ **DEX完整性验证** - 验证生成的DEX文件完整性和有效性

**增强功能（针对商业加固）**：
6. ✅ **应用预热机制** - 等待+模拟操作触发更多DEX加载
7. ✅ **多次脱壳尝试** - 多时间点脱壳，合并结果提高覆盖率
8. ✅ **动态加载检测** - 特别检测baiduprotect*.dex等动态加载文件
9. ✅ **完整性深度验证** - 文件头、大小、百度保护特征等多维度验证

## 3. 安装

### 3.1 通过OpenClaw自动安装
本技能已配置自动依赖安装，当通过OpenClaw技能系统安装时，会自动检测并安装以下依赖：

1. **Frida工具套件** (`frida-tools`) - 包含`frida`和`frida-dexdump`命令
2. **Python3** - 脚本运行环境
3. **Android调试桥** (`adb`) - 设备连接工具

### 3.2 手动安装依赖
如果未通过OpenClaw安装，请手动安装以下依赖：

```bash
# 安装Frida工具
pip install frida-tools

# 安装Python3（如果未安装）
sudo apt-get install python3 python3-pip

# 安装ADB
sudo apt-get install adb

# 在Android设备上运行frida-server
# 1. 下载对应架构的frida-server
# 2. 推送到设备: adb push frida-server /data/local/tmp/
# 3. 设置权限并运行: adb shell "chmod 755 /data/local/tmp/frida-server && /data/local/tmp/frida-server"
```

### 3.3 技能文件结构
安装后，技能文件结构如下：
```
android-armor-breaker/
├── SKILL.md              # 技能文档
├── _meta.json            # 技能元数据
├── LICENSE               # MIT许可证
├── scripts/              # 执行脚本目录
│   ├── android-armor-breaker          # 主包装脚本
│   ├── apk_protection_analyzer.py     # APK加固分析器
│   ├── enhanced_dexdump_runner.py     # 增强脱壳执行器
│   └── antidebug_bypass.py            # 反调试绕过模块
└── .clawhub/             # ClawHub发布配置
    └── origin.json       # 发布来源信息
```

## 4. 关键命令

Android Armor Breaker 提供**子命令系统**，支持`analyze`（APK加固分析）和`dump`（应用脱壳）两个核心功能。

### 4.1 APK加固分析（analyze子命令）
**先分析后脱壳** - 推荐工作流程：先分析APK加固类型，再根据分析结果选择最佳脱壳策略。

```bash
# 基本使用
android-armor-breaker analyze --apk <apk文件路径>

# 详细输出模式
android-armor-breaker analyze --apk <apk文件路径> --verbose

# 示例：分析示例应用APK
android-armor-breaker analyze --apk /path/to/示例应用.apk --verbose
```

**输出结果**：
- 控制台显示加固分析报告（保护类型、保护级别、置信度）
- 生成JSON格式详细报告：`<apk文件名>_protection_analysis.json`
- 提供脱壳策略建议（推荐参数、预估成功率、预估时间）

### 4.2 应用脱壳（dump子命令）
**Frida脱壳技术** - 基于Frida框架的商业级加固突破方案。

```bash
# 完整语法
android-armor-breaker dump --package <包名> [选项]

# 启用深度搜索模式（针对商业加固）
android-armor-breaker dump --package <包名> --deep-search --verbose

# 启用反调试绕过（针对强力反调试）
android-armor-breaker dump --package <包名> --bypass-antidebug --verbose
```

### 4.3 简写语法（向后兼容）
```bash
# 简写形式（自动识别为dump命令）
android-armor-breaker --package <包名> --output ./dex_output/

# 深度搜索模式
android-armor-breaker --package <包名> --deep-search --verbose

# 反调试绕过
android-armor-breaker --package <包名> --bypass-antidebug

# 弃用参数（显示警告，建议使用analyze子命令）
android-armor-breaker --package <包名> --detect-protection
```

### 4.4 推荐工作流程
```
📋 智能工作流程（推荐）：
1. 📥 获取APK文件
2. 🔍 android-armor-breaker analyze --apk app.apk
3. 📊 查看加固分析报告和脱壳建议
4. ⚡ 根据建议执行脱壳：android-armor-breaker --package <包名> [对应参数]
```

### 4.5 直接使用Python脚本
```bash
# APK加固分析工具
python3 scripts/apk_protection_analyzer.py --apk <apk文件路径> --verbose

# 增强版脱壳执行器
python3 scripts/enhanced_dexdump_runner.py --package <包名> --deep-search --verbose

# 反调试绕过模块
python3 scripts/antidebug_bypass.py --package <包名> --verbose
```



## 7. 技术实现细节

### 7.1 针对新百度加固的优化策略
- **深度搜索模式（-d参数）**：针对新百度加固等强力保护，使用`-d`参数进行更彻底的内存扫描，突破普通模式的DEX数量限制
- **多次脱壳尝试**：在应用启动后不同时间点执行多次脱壳，捕获动态加载的DEX
- **应用预热机制**：模拟用户操作触发更多功能加载
- **动态加载检测**：特别关注 `baiduprotect*.dex` 等动态加载的保护文件
- **完整性深度验证**：多维度验证DEX文件有效性



### 7.2 核心算法
```python
# 多次脱壳尝试合并算法
def merge_dex_files(self, all_dex_lists: List[List[Dict]]) -> List[Dict]:
    """合并多次脱壳的结果，去重"""
    unique_dex_files = {}
    for dex_list in all_dex_lists:
        for dex_info in dex_list:
            md5 = dex_info['md5']
            if md5 not in unique_dex_files:
                unique_dex_files[md5] = dex_info
    return list(unique_dex_files.values())

# DEX完整性验证算法
def verify_dex_header(self, dex_file: Path) -> bool:
    """验证DEX文件头"""
    with open(dex_file, 'rb') as f:
        header = f.read(4)
        return header in [b'dex\n', b'dey\n']

### 7.3 完整的DEX文件验证（增强版）
新增的完整验证功能包括：

1. **CRC32校验**：验证DEX文件头偏移0x8处的CRC32校验和
2. **SHA-1签名验证**：验证偏移0xC处的20字节SHA-1签名
3. **MD5匹配验证**：重新计算文件MD5并与frida-dexdump输出的MD5比对
4. **DEX结构验证**：验证文件头中的字符串表、类型表等偏移量是否有效
5. **文件大小验证**：验证文件大小字段与实际文件大小匹配

**验证算法示例**：
```python
def _verify_dex_complete(self, dex_path: Path, expected_md5: str = None) -> Dict:
    """完整的DEX文件验证"""
    # 1. CRC32验证
    expected_crc32 = struct.unpack('<I', data[8:12])[0]
    actual_crc32 = zlib.crc32(data[12:]) & 0xffffffff
    
    # 2. SHA-1验证  
    expected_sha1 = data[12:32]
    actual_sha1 = hashlib.sha1(data[32:]).digest()
    
    # 3. MD5验证
    actual_md5 = hashlib.md5(data).hexdigest()
    
    # 4. DEX结构验证
    string_ids_size = struct.unpack('<I', data[0x38:0x3c])[0]
    string_ids_off = struct.unpack('<I', data[0x3c:0x40])[0]
    
    return {
        'crc32_valid': expected_crc32 == actual_crc32,
        'sha1_valid': expected_sha1 == actual_sha1,
        'md5_match': actual_md5.lower() == expected_md5.lower() if expected_md5 else None
    }
```

## 8. 使用示例

### 8.1 APK加固分析示例（推荐先分析后脱壳）
```bash
# 分析APK加固类型
android-armor-breaker analyze --apk /path/to/app.apk --verbose

# 分析示例应用APK（测试案例）
android-armor-breaker analyze --apk /path/to/示例应用.apk --verbose

# 分析结果：
# 📊 保护类型: ALI (阿里加固)
# 🛡️ 保护级别: COMMERCIAL (商业级)
# 💡 建议: 使用深度搜索模式脱壳
```

### 8.2 智能脱壳示例（根据分析结果选择参数）
```bash
# 根据分析结果执行脱壳（商业级加固）
android-armor-breaker --package com.example.app --deep-search --verbose

# 针对强力反调试保护
android-armor-breaker --package com.example.app --bypass-antidebug --verbose

# Frida脱壳标准模式
android-armor-breaker --package com.example.app --verbose

# 指定输出目录
android-armor-breaker --package com.example.app --output ./dex_output/ --verbose
```

### 8.3 某应用脱壳（普通模式）
```bash
python3 scripts/enhanced_dexdump_runner.py \
  --package 包名 \
  --output ./dump_dex/ \
  --attempts 3 \
  --verbose
```

### 8.4 新百度加固应用脱壳（深度搜索模式）
```bash
# 针对新百度加固等强力保护，必须使用深度搜索模式
python3 scripts/enhanced_dexdump_runner.py \
  --package <包名> \
  --output ./deep_output/ \
  --deep-search \
  --attempts 3 \
  --verbose

# 直接使用frida-dexdump命令（等价于上述Python脚本）
frida-dexdump -U -f <包名> -d -o ./direct_output/
```



## 9. 注意事项
1. **新功能说明**：
   - **APK加固分析**：新增`analyze`子命令，支持静态分析APK加固类型
   - **智能工作流程**：推荐先分析APK，再根据分析结果选择脱壳参数
   - **弃用参数**：`--detect-protection`参数已弃用，请使用`analyze`子命令
   - **向后兼容**：原有脱壳命令语法完全兼容，新增`dump`子命令语法

2. **环境要求**：
   - 已安装 `frida-dexdump` 工具 (`pip install frida-tools`)
   - Android设备已通过USB连接并启用调试
   - 目标应用已安装在设备上

3. **执行前提**：
   - 设备上已运行 `frida-server` (需要root权限)
   - 应用包名正确且应用可正常启动
   - 对于商业加固应用，建议使用增强版脚本

4. **针对新百度加固**：
   - 必须使用**深度搜索模式（-d参数）**突破DEX数量限制
   - 需要足够的等待时间让应用完全加载（建议60秒以上）
   - 多次脱壳尝试可提高DEX文件覆盖率
   - 关注动态加载的 `baiduprotect*.dex` 等保护文件

5. **深度搜索模式**：
   - 使用`-d`参数进行深度搜索：`frida-dexdump -U -f <包名> -d -o ./output/`
   - 适用于新百度加固、腾讯加固等强力保护
   - 搜索更彻底但耗时更长（进行多轮扫描）
   - 可发现普通模式找不到的深层DEX文件

6. **常见问题**：
   - 如果命令失败，检查 `frida-server` 是否正在运行
   - 确保应用包名正确，可以使用 `adb shell pm list packages` 查看
   - 首次连接可能需要授权USB调试
   - 商业加固应用可能需要更多等待时间和尝试次数
   - 如果普通模式只能获得部分DEX，请切换到深度搜索模式

7. **输出文件**：
   - 默认在当前目录生成 `*.dex` 文件
   - 使用 `-o` 参数指定输出目录
   - 多DEX应用会生成多个文件 (classes.dex, classes2.dex等)
   - 增强版会生成详细报告 `enhanced_dexdump_report.md`
