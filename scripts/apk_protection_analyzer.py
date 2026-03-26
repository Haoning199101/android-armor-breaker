#!/usr/bin/env python3
"""
APK加固类型分析器
直接分析APK文件，检测使用的加固类型和保护级别
"""

import os
import sys
import zipfile
import re
import json
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import struct
import binascii

class ApkProtectionAnalyzer:
    """APK加固分析器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.apk_path = ""
        self.analysis_results = {
            "apk_file": "",
            "file_size": 0,
            "protection_type": "unknown",
            "protection_level": "unknown",
            "detected_vendors": [],
            "confidence_score": 0.0,
            "detailed_findings": {},
            "recommendations": []
        }
        
        # 加固特征库
        self.protection_patterns = {
            # 爱加密
            "ijiami": [
                (r"libijiami.*\.so$", "strong"),
                (r"libexec.*\.so$", "strong"),
                (r"libexecmain.*\.so$", "strong"),
                (r"libdvm.*\.so$", "strong"),
                (r"libsecexe.*\.so$", "strong"),
                (r"libsecmain.*\.so$", "strong"),
                (r"ijiami.*\.dat$", "medium"),
                (r"ijiami.*\.xml$", "medium"),
                (r"\.ijiami\.", "weak"),
            ],
            # 360加固
            "360": [
                (r".*libjiagu.*\.so$", "strong"),           # 任意目录下的libjiagu库
                (r"assets/libjiagu.*\.so$", "strong"),      # assets目录下的jiagu库（重点）
                (r"lib360\.so$", "strong"),
                (r"jiagu\.dex$", "strong"),
                (r"protect\.jar$", "medium"),
                (r".*360.*\.so$", "medium"),                # 任何360.so文件
                (r"assets/.*360.*", "weak"),                # assets中的360文件
                (r"assets/.*jiagu.*", "strong"),            # assets中的jiagu文件
                (r".*jiagu.*", "weak"),                     # 文件名包含jiagu
            ],
            # 百度加固
            "baidu": [
                (r"baiduprotect.*\.dex$", "strong"),
                (r"baiduprotect.*\.i\.dex$", "strong"),  # 新百度加固中间DEX文件
                (r"libbaiduprotect.*\.so$", "strong"),
                (r"libbdprotect.*\.so$", "strong"),
                (r"protect\.jar$", "medium"),
                (r"baiduprotect.*\.jar$", "medium"),  # 百度加固JAR文件
            ],
            # 腾讯加固
            "tencent": [
                (r"libshell.*\.so$", "strong"),
                (r"libtprotect.*\.so$", "strong"),
                (r"libstub\.so$", "strong"),
                (r"libAntiCheat\.so$", "strong"),  # 腾讯游戏安全(ACE)反作弊核心库
                (r"tps\.jar$", "medium"),
                (r"libmain\.so$", "weak"),  # 注意: 也可能是普通库
            ],
            # 阿里加固
            "ali": [
                (r"libmobisec.*\.so$", "strong"),
                (r"aliprotect\.dex$", "strong"),
                (r"aliprotect\.jar$", "medium"),
            ],
            # 梆梆加固
            "bangcle": [
                (r"libbangcle.*\.so$", "strong"),
                (r"libbc.*\.so$", "strong"),
                (r"bangcle\.jar$", "medium"),
                # 梆梆加固企业版特征
                (r"libdexjni\.so$", "strong"),
                (r"libDexHelper\.so$", "strong"),
                (r"libdexjni.*\.so$", "strong"),  # 变体
                (r"libdexhelper.*\.so$", "strong"),  # 变体
            ],
            # 娜迦加固
            "naga": [
                (r"libnaga.*\.so$", "strong"),
                (r"libng.*\.so$", "strong"),
            ],
            # 顶象加固
            "dingxiang": [
                (r"libdxp.*\.so$", "strong"),
                (r"libdx\.so$", "strong"),
            ],
            # 网易易盾
            "netease": [
                (r"libnesec\.so$", "strong"),
                (r"libneso\.so$", "strong"),
            ],
            # 几维安全（KiwiVM/奇安信/奇虎360）
            "kiwivm": [
                (r"libKwProtectSDK\.so$", "strong"),
                (r"libkiwi.*\.so$", "strong"),           # libkiwi_dumper.so, libkiwicrash.so
                (r"libkwsdataenc\.so$", "strong"),
                (r"libkadp\.so$", "strong"),
                (r"com\.kiwivm\.security\.StubApplication", "strong"),  # Application类
            ],
        }
        
        # 白名单（不视为加固）
        self.sdk_whitelist = [
            r".*BaiduSpeechSDK.*",
            r".*baidumap.*",
            r".*AMapSDK.*",
            r".*bugly.*",
            r".*qq.*",
            r".*wechat.*",
            r".*alipay.*",
            r".*alivc.*",       # 阿里云视频SDK
            r".*aliyun.*",      # 阿里云通用SDK
            r".*alibaba.*",     # 阿里巴巴SDK
            r".*umeng.*",
            r".*tencent.*\.so$",  # 注意：排除腾讯SDK，但不是libtprotect.so
            r"^libc\.so$",
            r"^libz\.so$",
            r"^liblog\.so$",
            r"^libm\.so$",
            r"^libdl\.so$",
            # 常见应用自有加密/安全库（非加固特征）
            r".*Encryptor.*",
            r".*encrypt.*",
            r".*crypto.*",
            r".*security.*",
            r".*secure.*",
            r".*safe.*",
            # r".*protect.*",  # 注意：可能是加固，但排除常见应用自有保护库 - 暂时注释，避免漏报百度加固
            r".*guard.*",
            r".*shield.*",
            r".*defense.*",
            r".*armor.*",
            r".*obfuscate.*",
            r".*antidebug.*",
            r".*anti.*debug.*",
            # 常见SDK库
            r".*volc.*",
            r".*tx.*",
            r".*apminsight.*",
            r".*mmkv.*",
            r".*liteav.*",
            r".*rive.*",
            r".*CtaApi.*",
        ]
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        if self.verbose or level in ["WARNING", "ERROR"]:
            prefix = {
                "INFO": "📝",
                "SUCCESS": "✅",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "DEBUG": "🔍"
            }.get(level, "📝")
            print(f"{prefix} {message}")
    

    def analyze_apk(self, apk_path: str) -> Dict:
        """分析APK文件加固类型"""
        if not os.path.exists(apk_path):
            self.log(f"APK文件不存在: {apk_path}", "ERROR")
            return self.analysis_results
        
        self.apk_path = apk_path
        self.analysis_results["apk_file"] = os.path.basename(apk_path)
        self.analysis_results["file_size"] = os.path.getsize(apk_path)
        
        self.log("=" * 60)
        self.log("🔍 APK加固类型分析")
        self.log(f"目标文件: {os.path.basename(apk_path)}")
        self.log(f"文件大小: {self.analysis_results['file_size'] / (1024*1024):.1f} MB")
        self.log("=" * 60)
        
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk_zip:
                # 1. 分析DEX文件
                dex_analysis = self.analyze_dex_files(apk_zip)
                
                # 2. 分析原生库
                native_lib_analysis = self.analyze_native_libs(apk_zip)
                
                # 3. 分析AndroidManifest.xml
                manifest_analysis = self.analyze_manifest(apk_zip)
                
                # 4. 分析资源文件
                resource_analysis = self.analyze_resources(apk_zip)
                
                # 5. 综合判断
                self.calculate_protection_level(
                    dex_analysis, 
                    native_lib_analysis, 
                    manifest_analysis, 
                    resource_analysis
                )
                
                # 7. 生成建议
                self.generate_recommendations()
                
        except Exception as e:
            self.log(f"分析APK失败: {e}", "ERROR")
        
        return self.analysis_results
    
    def analyze_dex_files(self, apk_zip: zipfile.ZipFile) -> Dict:
        """分析DEX文件特征"""
        self.log("分析DEX文件...")
        
        dex_files = [f for f in apk_zip.namelist() if f.endswith('.dex')]
        results = {
            "dex_count": len(dex_files),
            "dex_files": dex_files,
            "protection_indicators": [],
            "unusual_patterns": [],
            "dex_headers": [],
            "dex_size_analysis": {}
        }
        
        if len(dex_files) == 0:
            self.log("❌ 未找到DEX文件", "WARNING")
            results["unusual_patterns"].append("no_dex_files")
        elif len(dex_files) == 1:
            self.log(f"✅ 发现 {len(dex_files)} 个DEX文件: {dex_files[0]}")
            # 单DEX可能是加固特征
            if "classes.dex" in dex_files:
                # 深度分析DEX文件头
                dex_analysis = self.deep_analyze_dex(apk_zip, dex_files[0])
                results["dex_headers"].append(dex_analysis)
                results["dex_size_analysis"][dex_files[0]] = dex_analysis
        else:
            self.log(f"✅ 发现 {len(dex_files)} 个DEX文件")
            # 分析第一个DEX文件作为样本
            if dex_files and "classes.dex" in dex_files:
                dex_analysis = self.deep_analyze_dex(apk_zip, "classes.dex")
                results["dex_headers"].append(dex_analysis)
                results["dex_size_analysis"]["classes.dex"] = dex_analysis
        
        # 检查加固特征DEX
        for dex_file in dex_files:
            for vendor, patterns in self.protection_patterns.items():
                for pattern, strength in patterns:
                    if re.search(pattern, dex_file, re.IGNORECASE):
                        if not self.is_whitelisted(dex_file):
                            results["protection_indicators"].append({
                                "type": "dex",
                                "vendor": vendor,
                                "file": dex_file,
                                "strength": strength,
                                "pattern": pattern
                            })
        
        return results
    
    def deep_analyze_dex(self, apk_zip: zipfile.ZipFile, dex_file: str) -> Dict:
        """深度分析DEX文件头"""
        try:
            with apk_zip.open(dex_file) as f:
                # 读取DEX文件头部（前112字节包含关键信息）
                data = f.read(112)
                if len(data) < 8:
                    return {"status": "error", "reason": "文件太小"}
                
                # 检查DEX魔数
                magic = data[0:8]
                is_valid_dex = magic in [b'dex\n035\x00', b'dex\n036\x00', b'dex\n037\x00', b'dex\n038\x00', b'dex\n039\x00']
                
                # 检查文件大小（从偏移0x20开始，4字节小端）
                if len(data) >= 0x24:
                    file_size = struct.unpack('<I', data[0x20:0x24])[0]
                else:
                    file_size = 0
                
                # 检查校验和（偏移0x08，4字节小端）
                if len(data) >= 0x0C:
                    checksum = struct.unpack('<I', data[0x08:0x0C])[0]
                else:
                    checksum = 0
                
                # 检查签名（偏移0x0C，20字节SHA-1）
                if len(data) >= 0x20:
                    signature = data[0x0C:0x20].hex()
                else:
                    signature = ""
                
                # 分析结果
                result = {
                    "status": "success",
                    "magic": magic.hex(),
                    "is_valid_dex": is_valid_dex,
                    "file_size": file_size,
                    "checksum": checksum,
                    "signature": signature,
                    "analysis": {}
                }
                
                # 判断是否加密或混淆
                if not is_valid_dex:
                    result["analysis"]["warning"] = "DEX魔数异常，可能被加密或修改"
                    # 尝试检查是否为常见的加固特征
                    if magic[0:4] == b'\x00\x00\x00\x00':
                        result["analysis"]["suspicion"] = "可能为零填充加密"
                else:
                    result["analysis"]["conclusion"] = "标准DEX格式，可能未加密"
                    
                    # 检查是否有常见的加固特征
                    # 读取更多数据检查是否有明显的加密模式
                    f.seek(0)
                    sample_data = f.read(1024)
                    zero_count = sample_data.count(b'\x00')
                    if zero_count > 512:  # 超过50%为零
                        result["analysis"]["suspicion"] = "高零值比例，可能为简单加密或填充"
                
                return result
                
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    def analyze_native_libs(self, apk_zip: zipfile.ZipFile) -> Dict:
        """分析原生库特征"""
        self.log("分析原生库文件...")
        
        # 检查所有.so文件，包括assets/目录下的加固库
        lib_files = [f for f in apk_zip.namelist() if f.endswith('.so')]
        results = {
            "lib_count": len(lib_files),
            "lib_files": lib_files,
            "protection_indicators": [],
            "security_libs": [],
            "sdk_libs": []
        }
        
        if len(lib_files) == 0:
            self.log("❌ 未找到原生库文件", "WARNING")
        else:
            self.log(f"✅ 发现 {len(lib_files)} 个原生库文件")
        
        # 检查加固特征库
        protection_found = False
        for lib_file in lib_files:
            lib_name = os.path.basename(lib_file)
            
            # 检查是否是白名单SDK
            if self.is_whitelisted(lib_file):
                results["sdk_libs"].append(lib_file)
                continue
            
            # 检查加固特征
            vendor_found = False
            for vendor, patterns in self.protection_patterns.items():
                for pattern, strength in patterns:
                    if re.search(pattern, lib_file, re.IGNORECASE):
                        if not vendor_found:  # 避免重复添加
                            results["protection_indicators"].append({
                                "type": "native",
                                "vendor": vendor,
                                "file": lib_file,
                                "strength": strength,
                                "pattern": pattern
                            })
                            vendor_found = True
                            protection_found = True
            
            # 如果没有匹配加固特征，检查是否是其他安全库
            if not vendor_found:
                security_patterns = [
                    r"protect", r"secure", r"safe", r"guard", r"shield",
                    r"encrypt", r"crypto", r"decrypt", r"obfuscate",
                    r"anti", r"defense", r"security", r"armor"
                ]
                for pattern in security_patterns:
                    if re.search(pattern, lib_name, re.IGNORECASE):
                        results["security_libs"].append(lib_file)
                        break
        
        if protection_found:
            self.log(f"⚠️  发现加固特征库", "WARNING")
        else:
            self.log("✅ 未发现明显的加固特征库", "SUCCESS")
        
        return results
    
    def analyze_manifest(self, apk_zip: zipfile.ZipFile) -> Dict:
        """分析AndroidManifest.xml"""
        self.log("分析AndroidManifest.xml...")
        
        results = {
            "manifest_found": False,
            "debuggable": False,
            "backup_allowed": True,
            "protection_indicators": []
        }
        
        try:
            if "AndroidManifest.xml" in apk_zip.namelist():
                results["manifest_found"] = True
                with apk_zip.open("AndroidManifest.xml") as manifest_file:
                    content = manifest_file.read()
                    
                    # 简单文本检查（实际应用中应使用AXML解析器）
                    try:
                        text = content.decode('utf-8', errors='ignore')
                        
                        # 检查调试属性
                        if 'android:debuggable="true"' in text:
                            results["debuggable"] = True
                            self.log("⚠️  应用可调试 (debuggable=true)", "WARNING")
                        
                        # 检查备份属性
                        if 'android:allowBackup="false"' in text:
                            results["backup_allowed"] = False
                            self.log("✅ 备份已禁用 (安全配置)", "INFO")
                        
                        # 检查加固相关特征
                        if 'com.ijiami' in text:
                            results["protection_indicators"].append({
                                "type": "manifest",
                                "vendor": "ijiami",
                                "indicator": "包名包含ijiami"
                            })
                        
                    except:
                        pass
            else:
                self.log("❌ 未找到AndroidManifest.xml", "WARNING")
                
        except Exception as e:
            self.log(f"分析Manifest失败: {e}", "DEBUG")
        
        return results
    
    def analyze_resources(self, apk_zip: zipfile.ZipFile) -> Dict:
        """分析资源文件"""
        self.log("分析资源文件...")
        
        results = {
            "resource_count": 0,
            "protection_indicators": [],
            "unusual_files": []
        }
        
        file_list = apk_zip.namelist()
        results["resource_count"] = len(file_list)
        
        # 加固资源文件特征模式
        resource_protection_patterns = {
            "ijiami": [
                r"assets/ijiami.*\.dat$",
                r"assets/ijiami.*\.xml$",
                r"ijiami.*\.properties$",
            ],
            "360": [
                r"assets/jiagu.*",
                r"assets/.*360.*\.dat$",
                r"assets/.*360.*\.xml$",
            ],
            "baidu": [
                r"assets/baiduprotect.*",
                r"assets/baidu.*\.dat$",
            ],
            "tencent": [
                r"assets/tprotect.*",
                r"assets/tencent.*\.dat$",
                r"assets/libwbsafeedit.*",  # 腾讯Web安全编辑组件
            ],
            "ali": [
                r"assets/aliprotect.*",
                r"assets/alisec.*",
            ],
            "bangcle": [
                r"assets/meta-data/.*",  # 梆梆加固企业版签名文件目录
                r"assets/.*bangcle.*",
                r"assets/.*bangele.*",
                r"assets/.*libdexjni.*",
                r"assets/.*libDexHelper.*",
            ],
            # 网易易盾资源文件特征
            "netease": [
                r"assets/netease.*",
                r"assets/yidun.*",
                r"assets/nd.*",
                r"assets/libnesec.*",
                r"assets/libneso.*",
            ]
        }
        
        for file_name in file_list:
            # 跳过白名单文件
            if self.is_whitelisted(file_name):
                continue
                
            # 检查是否是明显的加固资源文件
            for vendor, patterns in resource_protection_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, file_name, re.IGNORECASE):
                        results["protection_indicators"].append({
                            "type": "resource",
                            "vendor": vendor,
                            "file": file_name,
                            "pattern": pattern
                        })
                        break  # 找到一个匹配就跳出内层循环
        
        return results
    
    def is_whitelisted(self, file_name: str) -> bool:
        """检查是否在白名单中"""
        for pattern in self.sdk_whitelist:
            if re.search(pattern, file_name, re.IGNORECASE):
                return True
        return False
    
    def analyze_dex_status(self, dex_results: Dict) -> Dict:
        """分析DEX文件状态"""
        status = {
            "is_normal_dex": False,
            "is_encrypted": False,
            "is_obfuscated": False,
            "details": []
        }
        
        # 检查DEX头分析结果
        dex_headers = dex_results.get("dex_headers", [])
        if dex_headers:
            for header_info in dex_headers:
                if header_info.get("status") == "success":
                    is_valid = header_info.get("is_valid_dex", False)
                    if is_valid:
                        status["is_normal_dex"] = True
                        status["details"].append("标准DEX格式")
                    else:
                        status["is_encrypted"] = True
                        status["details"].append("DEX魔数异常")
        
        # 如果没有深度分析结果，使用简单判断
        if not dex_headers and dex_results.get("dex_count", 0) > 0:
            # 假设DEX正常，直到有证据证明异常
            status["is_normal_dex"] = True
            status["details"].append("未深度分析，假设为标准DEX")
        
        return status
    
    def calculate_protection_level(self, dex_results: Dict, native_results: Dict, 
                                  manifest_results: Dict, resource_results: Dict):
        """综合判断保护级别"""
        
        # 收集所有保护指标
        all_indicators = []
        all_indicators.extend(dex_results.get("protection_indicators", []))
        all_indicators.extend(native_results.get("protection_indicators", []))
        all_indicators.extend(manifest_results.get("protection_indicators", []))
        all_indicators.extend(resource_results.get("protection_indicators", []))
        
        # 按厂商分组，调整弱特征权重
        vendor_scores = {}
        weak_indicators_count = 0
        strong_indicators_count = 0
        
        for indicator in all_indicators:
            vendor = indicator.get("vendor")
            strength = indicator.get("strength", "weak")
            if vendor:
                # 调整权重：弱特征权重降低，强特征权重增加
                score = {"strong": 3, "medium": 1.5, "weak": 0.3}.get(strength, 0.3)  # 弱特征权重大幅降低
                vendor_scores[vendor] = vendor_scores.get(vendor, 0) + score
                
                if strength == "weak":
                    weak_indicators_count += 1
                elif strength == "strong":
                    strong_indicators_count += 1
        
        # 分析DEX状态
        dex_status = self.analyze_dex_status(dex_results)
        self.log(f"📊 DEX状态分析: 正常={dex_status['is_normal_dex']}, 加密={dex_status['is_encrypted']}", "DEBUG")
        
        # 计算初始置信度
        total_score = sum(vendor_scores.values())
        max_score = len(all_indicators) * 3 if all_indicators else 0
        confidence = total_score / max_score if max_score > 0 else 0
        
        # 考虑DEX深度分析结果
        dex_headers = dex_results.get("dex_headers", [])
        if dex_headers:
            for dex_analysis in dex_headers:
                if dex_analysis.get("status") == "success" and dex_analysis.get("is_valid_dex"):
                    # 标准DEX格式，大幅降低加固可能性
                    confidence = confidence * 0.3  # 置信度大幅降低
                    self.log(f"📊 标准DEX格式检测到，大幅降低加固置信度至 {confidence:.1%}", "DEBUG")
        

        
        # 确定保护类型 - 使用更严格的判断逻辑
        protection_type = "none"
        protection_level = "basic"
        
        if vendor_scores:
            # 选择得分最高的厂商
            protection_type = max(vendor_scores.items(), key=lambda x: x[1])[0]
            top_score = vendor_scores[protection_type]
            
            # 基于DEX状态和特征强度进行综合判断
            if dex_status["is_normal_dex"]:
                # DEX正常，需要更强的证据才能判断为加固
                if top_score >= 2.0 and strong_indicators_count >= 1:
                    protection_level = "commercial"
                elif top_score >= 1.0 and weak_indicators_count <= 2:
                    protection_level = "basic"
                else:
                    # 分数不够高，可能是误判
                    protection_type = "none"
                    protection_level = "basic"
                    confidence = max(confidence * 0.2, 0.1)  # 大幅降低置信度
            else:
                # DEX异常，更容易判断为加固
                if top_score >= 3:
                    protection_level = "enterprise"
                elif top_score >= 2:
                    protection_level = "commercial"
                elif top_score >= 1:
                    protection_level = "basic"
                else:
                    protection_type = "none"
                    protection_level = "basic"
        else:
            # 没有检测到加固特征
            if dex_results.get("dex_count", 0) == 1:
                # 单DEX可能是简单保护或未加固
                protection_type = "unknown"
                protection_level = "basic"
            else:
                protection_type = "none"
                protection_level = "basic"
        
        # 特殊情况：如果只有弱特征且DEX正常，强制判断为无加固
        if vendor_scores and dex_status["is_normal_dex"]:
            weak_indicators_only = weak_indicators_count > 0 and strong_indicators_count == 0
            if weak_indicators_only and top_score < 1.5:
                protection_type = "none"
                protection_level = "basic"
                confidence = 0.1  # 极低置信度
                self.log(f"📊 只有弱特征且DEX正常，强制判断为无加固", "DEBUG")
        
        # 特殊情况：多个DEX文件且都正常，通常不是加固
        if dex_results.get("dex_count", 0) > 1 and dex_status["is_normal_dex"]:
            if protection_type != "none" and top_score < 2.0:
                protection_type = "none"
                protection_level = "basic"
                confidence = confidence * 0.5
                self.log(f"📊 多个正常DEX文件，降低加固可能性", "DEBUG")
        
        self.analysis_results.update({
            "protection_type": protection_type,
            "protection_level": protection_level,
            "confidence_score": confidence,
            "detected_vendors": list(vendor_scores.keys()),
            "detailed_findings": {
                "dex": dex_results,
                "native": native_results,
                "manifest": manifest_results,
                "resource": resource_results,
                "dex_status": dex_status,
                "indicator_stats": {
                    "total": len(all_indicators),
                    "weak": weak_indicators_count,
                    "strong": strong_indicators_count
                }
            }
        })
    
    def generate_recommendations(self):
        """生成脱壳建议"""
        protection_type = self.analysis_results["protection_type"]
        protection_level = self.analysis_results["protection_level"]
        confidence = self.analysis_results["confidence_score"]
        
        recommendations = []
        
        # 1. 低置信度警告（优先显示）
        if confidence < 0.3:
            recommendations.append("⚠️  **低置信度警告**: 检测结果置信度较低 (低于30%)，可能存在误判")
        
        # 2. 基于保护类型的建议
        if protection_type == "none" and protection_level == "basic":
            recommendations.extend([
                "✅ 应用可能未加固或使用简单保护",
                "💡 建议: 使用标准脱壳模式 (android-armor-breaker --package <包名>)",
                "📊 预估成功率: 95%以上",
                "⏱️  预估时间: 1-2分钟"
            ])

                
        elif protection_type == "ijiami":
            if protection_level == "enterprise":
                recommendations.extend([
                    "⚠️  检测到爱加密企业版加固",
                    "💡 建议: 使用激进脱壳策略",
                    "🛠️  推荐参数: --bypass-antidebug --dynamic-puzzle",
                    "📊 预估成功率: 30-50% (基于历史测试数据)",
                    "⏱️  预估时间: 5-10分钟",
                    "🔑 关键: 可能需要Root权限进行内存攻击"
                ])
            else:
                recommendations.extend([
                    "✅ 检测到爱加密加固 (标准版)",
                    "💡 建议: 使用深度搜索模式",
                    "🛠️  推荐参数: --deep-search --bypass-antidebug",
                    "📊 预估成功率: 70-85%",
                    "⏱️  预估时间: 2-4分钟"
                ])
                
        elif protection_type == "360":
            recommendations.extend([
                "✅ 检测到360加固",
                "💡 建议: 使用深度搜索模式",
                "🛠️  推荐参数: --deep-search",
                "📊 预估成功率: 80-90%",
                "⏱️  预估时间: 2-3分钟"
            ])
            
        elif protection_type == "baidu":
            recommendations.extend([
                "✅ 检测到百度加固",
                "💡 建议: 使用深度搜索模式突破DEX数量限制",
                "🛠️  推荐参数: --deep-search",
                "📊 预估成功率: 85-95%",
                "⏱️  预估时间: 2-3分钟",
                "💾 经验: 可突破26个DEX限制，获取完整53个DEX"
            ])
            
        elif protection_type == "tencent":
            recommendations.extend([
                "✅ 检测到腾讯加固",
                "💡 建议: 使用反调试绕过+深度搜索",
                "🛠️  推荐参数: --deep-search --bypass-antidebug",
                "📊 预估成功率: 75-85%",
                "⏱️  预估时间: 3-5分钟"
            ])
            
        elif protection_type == "ali":
            # 阿里加固特别处理，因为容易误判
            if confidence < 0.5:
                recommendations.extend([
                    f"⚠️  检测到阿里加固 (置信度: {confidence*100:.1f}%)",
                    "🔍 **注意**: 阿里加固检测容易误判，libEncryptorP.so等库可能是应用自有加密",
                    "🔄 **脱壳策略**: 如果确实有反调试保护，使用 --bypass-antidebug 参数"
                ])
            else:
                recommendations.extend([
                    "✅ 检测到阿里加固",
                    "💡 建议: 使用自适应策略",
                    "🛠️  推荐参数: --bypass-antidebug --deep-search",
                    f"📊 置信度: {confidence*100:.1f}%",
                    "⏱️  预估时间: 3-5分钟"
                ])
                
        else:
            # 其他加固类型
            recommendations.extend([
                f"✅ 检测到 {protection_type} 加固 (保护级别: {protection_level})",
                "💡 建议: 尝试自适应策略",
                "🛠️  推荐参数: --detect-protection (让技能自动选择最佳策略)",
                f"📊 置信度: {confidence*100:.1f}%",
                "⏱️  预估时间: 2-5分钟"
            ])
        
        # 3. DEX文件直接提取建议（如果DEX数量多且可能未加固）
        dex_count = self.analysis_results.get("detailed_findings", {}).get("dex", {}).get("dex_count", 0)
        if dex_count >= 2 and confidence < 0.4:
            recommendations.append("📦 **直接提取建议**: 可尝试直接从APK提取DEX: `unzip -j apk '*.dex'`")
        
        self.analysis_results["recommendations"] = recommendations
    
    def print_report(self):
        """打印分析报告"""
        results = self.analysis_results
        
        self.log("=" * 60)
        self.log("📊 APK加固分析报告")
        self.log("=" * 60)
        self.log(f"📦 文件: {results['apk_file']}")
        self.log(f"📏 大小: {results['file_size'] / (1024*1024):.1f} MB")
        self.log("")
        
        self.log("🔐 加固分析结果:")
        self.log(f"  保护类型: {results['protection_type'].upper()}")
        self.log(f"  保护级别: {results['protection_level'].upper()}")
        self.log(f"  检测到的厂商: {', '.join(results['detected_vendors']) if results['detected_vendors'] else '无'}")
        self.log(f"  置信度: {results['confidence_score']*100:.1f}%")
        
        self.log("")
        
        # 详细发现
        details = results['detailed_findings']
        if details.get('dex', {}).get('dex_count', 0) > 0:
            dex_info = details['dex']
            self.log(f"📄 DEX文件: {dex_info['dex_count']} 个")
            
            # 显示DEX头分析结果
            dex_headers = dex_info.get('dex_headers', [])
            if dex_headers:
                for dex_analysis in dex_headers[:2]:  # 只显示前2个分析结果
                    if dex_analysis.get('status') == 'success':
                        magic = dex_analysis.get('magic', '未知')
                        is_valid = dex_analysis.get('is_valid_dex', False)
                        file_size = dex_analysis.get('file_size', 0)
                        
                        if is_valid:
                            self.log(f"  ✅ DEX头部: 标准格式 (magic: {magic}), 大小: {file_size:,} 字节")
                            if dex_analysis.get('analysis', {}).get('conclusion'):
                                self.log(f"    分析: {dex_analysis['analysis']['conclusion']}")
                        else:
                            self.log(f"  ⚠️  DEX头部: 异常格式 (magic: {magic})")
                            if dex_analysis.get('analysis', {}).get('warning'):
                                self.log(f"    警告: {dex_analysis['analysis']['warning']}")
        
        if details.get('native', {}).get('lib_count', 0) > 0:
            native_info = details['native']
            self.log(f"⚙️  原生库: {native_info['lib_count']} 个")
            
            # 显示安全库（非加固特征）
            security_libs = native_info.get('security_libs', [])
            if security_libs:
                self.log("  🔒 检测到的安全库 (可能为应用自有):")
                for lib in security_libs[:3]:  # 只显示前3个
                    self.log(f"    - {os.path.basename(lib)}")
            
            # 显示加固特征库
            if native_info.get('protection_indicators'):
                self.log("  🔍 检测到的加固特征库:")
                for indicator in native_info['protection_indicators'][:5]:  # 只显示前5个
                    self.log(f"    - {indicator['vendor']}: {os.path.basename(indicator['file'])}")
        
        self.log("")
        
        # 建议
        self.log("🎯 脱壳建议:")
        for rec in results['recommendations']:
            if rec.startswith("✅"):
                self.log(f"  {rec}")
            elif rec.startswith("⚠️"):
                self.log(f"  {rec}")
            elif rec.startswith("💡"):
                self.log(f"  {rec}")
            else:
                self.log(f"    {rec}")
        
        self.log("=" * 60)

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='APK加固类型分析器')
    parser.add_argument('--apk', '-a', required=True, help='APK文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    analyzer = ApkProtectionAnalyzer(verbose=args.verbose)
    results = analyzer.analyze_apk(args.apk)
    analyzer.print_report()
    
    # 保存结果到文件
    output_file = os.path.splitext(args.apk)[0] + '_protection_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📁 详细结果已保存到: {output_file}")

if __name__ == '__main__':
    main()