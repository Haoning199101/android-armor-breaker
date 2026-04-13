# Android Armor Breaker 快速开始指南
## 版本: v2.1.0 (国际化基本完成版)

## 🚀 30秒快速开始

```bash
# 1. 进入脚本目录
cd android-armor-breaker/scripts

# 2. 确保脚本可执行
chmod +x android-armor-breaker

# 3. 测试功能
./android-armor-breaker --help
```

## 🌐 多语言支持

技能支持英语和中文输出：

```bash
# 英语环境 (默认)
./android-armor-breaker --help --language en-US

# 中文环境
./android-armor-breaker --help --language zh-CN

# 分析APK (中文输出)
./android-armor-breaker analyze --apk app.apk --language zh-CN --verbose

# 脱壳应用 (英语输出)
./android-armor-breaker --package com.example.app --language en-US --deep-search
```

## 🎯 核心功能示例

### 1. APK加固分析
```bash
# 分析APK的加固类型和保护级别
./android-armor-breaker analyze --apk /path/to/app.apk --verbose

# 输出示例:
# ✅ Detected 360 reinforcement (protection level: HIGH)
# ✅ Recommendation: Use Root memory extraction strategy
```

### 2. 智能脱壳（推荐）
```bash
# 自动选择最佳脱壳策略
./android-armor-breaker --package com.target.app --deep-search --verbose

# 如果提供APK文件，智能分析并选择策略
./android-armor-breaker --package com.target.app --apk /path/to/app.apk --verbose
```

### 3. 指定策略脱壳
```bash
# Frida动态脱壳（默认，适用于基础加固）
./android-armor-breaker --package com.target.app --strategy frida --verbose

# Root内存提取（绕过商业级加固：爱加密、梆梆、360等）
./android-armor-breaker --package com.target.app --strategy root --verbose

# 内存快照攻击（针对立即崩溃的应用）
./android-armor-breaker --package com.target.app --strategy snapshot --verbose
```

## 🔧 环境要求

### 必需组件
- **Python 3.8+**: `sudo apt install python3`
- **ADB**: `sudo apt install adb`
- **Android设备**: 已连接并启用USB调试

### 可选组件（按需安装）
- **Frida工具**（Frida策略需要）:
  ```bash
  pip install frida-tools
  ```
- **Root权限**（Root内存提取需要）:
  - 设备已root
  - 已授予ADB root权限

## 📊 支持的加固方案

| 加固方案 | 支持状态 | 推荐策略 |
|----------|----------|----------|
| 无加固/基础加固 | ✅ 完全支持 | Frida动态脱壳 |
| 360加固 | ✅ 完全支持 | Root内存提取 |
| 梆梆企业版 | ✅ 完全支持 | Root内存提取 |
| 爱加密（IJIAMI） | ✅ 完全支持 | Root内存提取 |
| 新百度加固 | ✅ 理论支持 | Root内存提取 |
| 网易易盾 | ✅ 支持（VDEX） | Root内存提取 |
| 混合加固 | ⚠️ 部分支持 | 需手动测试 |

## ⚠️ 常见问题

### Q1: 脚本无法执行
```bash
# 错误: Permission denied
chmod +x android-armor-breaker
```

### Q2: 设备未连接
```bash
# 检查设备连接
adb devices
# 确保设备已授权
```

### Q3: Frida无法工作
```bash
# 安装Frida
pip install frida-tools
# 在设备上启动Frida服务
adb shell
su
/data/local/tmp/frida-server &
```

### Q4: Root内存提取失败
- 确保设备已root
- 确保已授予ADB root权限: `adb root`
- 检查应用是否安装并可以启动

## 🛠️ 高级选项

### 深度搜索模式
```bash
# 启用深度搜索，发现更多DEX文件
./android-armor-breaker --package com.target.app --deep-search --verbose
```

### 反调试绕过
```bash
# 启用反调试绕过技术
./android-armor-breaker --package com.target.app --bypass-antidebug --verbose
```

### 自定义输出目录
```bash
# 指定DEX文件输出目录
./android-armor-breaker --package com.target.app --output ./dex_files --verbose
```

## 📈 性能提示

1. **首次运行较慢**：需要初始化环境和加载资源
2. **内存使用**：Root内存提取可能需要大量内存（1GB+）
3. **时间预估**：
   - APK分析: 10-30秒
   - Frida脱壳: 1-3分钟
   - Root内存提取: 2-5分钟
   - 深度搜索: +1-2分钟

## 🔍 验证结果

脱壳完成后，检查输出目录：
```bash
ls -la ./output_*/  # 自动生成的输出目录
# 应该看到:
# - 多个.dex文件
# - 分析报告.json
# - 执行日志.txt
```

## 📞 获取帮助

### 查看详细帮助
```bash
./android-armor-breaker --help
```

### 查看版本信息
```bash
./android-armor-breaker --version
```

### 测试环境
```bash
# 运行环境测试
python3 test_environment.py
```

---

**提示**: 技能国际化状态约65%完成，核心功能完整，部分输出仍为英文但不影响使用。

*文档版本: v2.1.0-quickstart*
*更新日期: 2026-04-01*