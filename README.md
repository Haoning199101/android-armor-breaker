# Android Armor Breaker

Android应用护甲破坏者 - 基于OpenClaw平台的Frida脱壳技术，针对从商业级到企业级的Android应用保护方案，提供**APK加固分析**与**DEX智能提取**的完整解决方案。

## 功能特性

- ✅ **APK加固分析** - 静态分析APK文件，识别加固厂商和保护级别
- ✅ **环境检查** - 自动检查Frida环境、设备连接、应用安装状态、Root权限
- ✅ **智能脱壳** - 根据保护级别自动选择最佳脱壳策略
- ✅ **实时监控界面** - 追踪Dex文件提取过程，实时显示进度
- ✅ **DEX完整性验证** - 验证生成的DEX文件完整性和有效性
- ✅ **增强功能** - 应用预热机制、多次脱壳尝试、动态加载检测、完整性深度验证

## 支持的加固方案

- ✅ 360加固（已验证：示例应用1，85个DEX）
- ✅ 梆梆企业版（已验证：示例应用2，115个DEX）
- ✅ 梆梆企业版轻量级（已验证：示例应用3，59个DEX）
- ⚠️ 新百度加固（理论支持，待验证）
- ❌ 混合加固（360+腾讯等，当前技术限制）

## 快速开始

### 安装依赖
```bash
pip install frida-tools
sudo apt-get install adb
```

### 基本使用
```bash
# 分析APK加固类型
android-armor-breaker analyze --apk app.apk --verbose

# 执行脱壳
android-armor-breaker --package com.example.app --deep-search --verbose

# 针对强反调试应用
android-armor-breaker --package com.example.app --bypass-antidebug --verbose
```

## 测试结果

基于2026年3月18-19日实际测试：

| 应用 | 加固类型 | DEX数量 | 结果 |
|------|----------|---------|------|
| 示例应用1 | 360加固 | 85个 | ✅ 成功 |
| 示例应用2 | 梆梆企业版 | 115个 | ✅ 成功 |
| 示例应用3 | 梆梆企业版 | 59个 | ✅ 成功 |
| 示例应用4 | 360+腾讯混合 | 0个 | ❌ 失败 |

**成功率**: 75% (3/4应用成功)
**总DEX文件**: 259个
**总文件大小**: 约1.6GB

## 技术突破

1. **内存权限修改** - 突破`PROT_NONE`内存保护，解决访问违规问题
2. **Frida特征隐藏** - 重命名文件、非标准端口、函数名混淆，避免脚本销毁
3. **反调试绕过** - 分阶段注入，突破企业级反调试保护
4. **深度搜索模式** - 从1个静态DEX发现100+个运行时DEX
5. **完整性深度验证** - CRC32、SHA-1、MD5多维度校验

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

Trx-HaoNing - 安全研究员

## 支持

如有问题或建议，请通过OpenClaw社区反馈。