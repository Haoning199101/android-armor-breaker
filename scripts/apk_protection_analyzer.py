#!/usr/bin/env python3
"""
APK Reinforcement Type Analyzer
Directly analyze APK files，Detect reinforcement types and protection levels used
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
    """APKReinforcementAnalysis器"""
    
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
        
        # Reinforcement feature library
        self.protection_patterns = {
            # 爱Encrypting
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
            # 360Reinforcement
            "360": [
                (r".*libjiagu.*\.so$", "strong"),           # 任意Directory下的libjiaguLibrary
                (r"assets/libjiagu.*\.so$", "strong"),      # assetsDirectory下的jiaguLibrary（重点）
                (r"lib360\.so$", "strong"),
                (r"jiagu\.dex$", "strong"),
                (r"protect\.jar$", "medium"),
                (r".*360.*\.so$", "medium"),                # 任何360.soFile
                (r"assets/.*360.*", "weak"),                # assets中的360File
                (r"assets/.*jiagu.*", "strong"),            # assets中的jiaguFile
                (r".*jiagu.*", "weak"),                     # File名包含jiagu
            ],
            # 百度Reinforcement
            "baidu": [
                (r"baiduprotect.*\.dex$", "strong"),
                (r"baiduprotect.*\.i\.dex$", "strong"),  # 新百度Reinforcement中间DEXFile
                (r"libbaiduprotect.*\.so$", "strong"),
                (r"libbdprotect.*\.so$", "strong"),
                (r"protect\.jar$", "medium"),
                (r"baiduprotect.*\.jar$", "medium"),  # 百度ReinforcementJARFile
            ],
            # 腾讯Reinforcement
            "tencent": [
                (r"libshell.*\.so$", "strong"),
                (r"libtprotect.*\.so$", "strong"),
                (r"libstub\.so$", "strong"),
                (r"libAntiCheat\.so$", "strong"),  # 腾讯游戏Security(ACE)反作弊核心Library
                (r"tps\.jar$", "medium"),
                (r"libmain\.so$", "weak"),  # Note: 也可能是普通Library
            ],
            # 阿里Reinforcement
            "ali": [
                (r"libmobisec.*\.so$", "strong"),
                (r"aliprotect\.dex$", "strong"),
                (r"aliprotect\.jar$", "medium"),
            ],
            # 梆梆Reinforcement
            "bangcle": [
                (r"libbangcle.*\.so$", "strong"),
                (r"libbc.*\.so$", "strong"),
                (r"bangcle\.jar$", "medium"),
                # 梆梆Reinforcement企业版特征
                (r"libdexjni\.so$", "strong"),
                (r"libDexHelper\.so$", "strong"),
                (r"libdexjni.*\.so$", "strong"),  # 变体
                (r"libdexhelper.*\.so$", "strong"),  # 变体
            ],
            # 娜迦Reinforcement
            "naga": [
                (r"libnaga.*\.so$", "strong"),
                (r"libng.*\.so$", "strong"),
            ],
            # 顶象Reinforcement
            "dingxiang": [
                (r"libdxp.*\.so$", "strong"),
                (r"libdx\.so$", "strong"),
            ],
            # 网易易盾
            "netease": [
                (r"libnesec\.so$", "strong"),
                (r"libneso\.so$", "strong"),
            ],
            # 几维Security（KiwiVM/奇安信/奇虎360）
            "kiwivm": [
                (r"libKwProtectSDK\.so$", "strong"),
                (r"libkiwi.*\.so$", "strong"),           # libkiwi_dumper.so, libkiwicrash.so
                (r"libkwsdataenc\.so$", "strong"),
                (r"libkadp\.so$", "strong"),
                (r"com\.kiwivm\.security\.StubApplication", "strong"),  # Application类
            ],
        }
        
        # 白名单（不视为Reinforcement）
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
            r".*tencent.*\.so$",  # Note：排除腾讯SDK，但不是libtprotect.so
            r"^libc\.so$",
            r"^libz\.so$",
            r"^liblog\.so$",
            r"^libm\.so$",
            r"^libdl\.so$",
            # 常见Application自有Encrypting/SecurityLibrary（非Reinforcement特征）
            r".*Encryptor.*",
            r".*encrypt.*",
            r".*crypto.*",
            r".*security.*",
            r".*secure.*",
            r".*safe.*",
            # r".*protect.*",  # Note：可能是Reinforcement，但排除常见Application自有ProtectionLibrary - 暂时注释，避免漏报百度Reinforcement
            r".*guard.*",
            r".*shield.*",
            r".*defense.*",
            r".*armor.*",
            r".*obfuscate.*",
            r".*antidebug.*",
            r".*anti.*debug.*",
            # 常见SDKLibrary
            r".*volc.*",
            r".*tx.*",
            r".*apminsight.*",
            r".*mmkv.*",
            r".*liteav.*",
            r".*rive.*",
            r".*CtaApi.*",
        ]
    
    def log(self, message: str, level: str = "INFO"):
        """RecordingLog"""
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
        """AnalysisAPKFileReinforcement类型"""
        if not os.path.exists(apk_path):
            self.log(f"APKFile不存在: {apk_path}", "ERROR")
            return self.analysis_results
        
        self.apk_path = apk_path
        self.analysis_results["apk_file"] = os.path.basename(apk_path)
        self.analysis_results["file_size"] = os.path.getsize(apk_path)
        
        self.log("=" * 60)
        self.log("🔍 APKReinforcement类型Analysis")
        self.log(f"目标File: {os.path.basename(apk_path)}")
        self.log(f"FileSize: {self.analysis_results['file_size'] / (1024*1024):.1f} MB")
        self.log("=" * 60)
        
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk_zip:
                # 1. Analyze DEX files
                dex_analysis = self.analyze_dex_files(apk_zip)
                
                # 2. Analysisnative library
                native_lib_analysis = self.analyze_native_libs(apk_zip)
                
                # 3. Analyze AndroidManifest.xml
                manifest_analysis = self.analyze_manifest(apk_zip)
                
                # 4. Analyze resource files
                resource_analysis = self.analyze_resources(apk_zip)
                
                # 5. 综合判断
                self.calculate_protection_level(
                    dex_analysis, 
                    native_lib_analysis, 
                    manifest_analysis, 
                    resource_analysis
                )
                
                # 7. 生成Recommendation
                self.generate_recommendations()
                
        except Exception as e:
            self.log(f"AnalysisAPKFailed: {e}", "ERROR")
        
        return self.analysis_results
    
    def analyze_dex_files(self, apk_zip: zipfile.ZipFile) -> Dict:
        """AnalysisDEXFile特征"""
        self.log("AnalysisDEXFile...")
        
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
            self.log("❌ 未找到DEXFile", "WARNING")
            results["unusual_patterns"].append("no_dex_files")
        elif len(dex_files) == 1:
            self.log(f"✅ 发现 {len(dex_files)} 个DEXFile: {dex_files[0]}")
            # 单DEX可能是Reinforcement特征
            if "classes.dex" in dex_files:
                # 深度Analyze DEX files头
                dex_analysis = self.deep_analyze_dex(apk_zip, dex_files[0])
                results["dex_headers"].append(dex_analysis)
                results["dex_size_analysis"][dex_files[0]] = dex_analysis
        else:
            self.log(f"✅ 发现 {len(dex_files)} 个DEXFile")
            # Analysis第一个DEXFile作为样本
            if dex_files and "classes.dex" in dex_files:
                dex_analysis = self.deep_analyze_dex(apk_zip, "classes.dex")
                results["dex_headers"].append(dex_analysis)
                results["dex_size_analysis"]["classes.dex"] = dex_analysis
        
        # 检查Reinforcement特征DEX
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
        """深度AnalysisDEXFile头"""
        try:
            with apk_zip.open(dex_file) as f:
                # ReadingDEXFile头部（前112字节包含关键Information）
                data = f.read(112)
                if len(data) < 8:
                    return {"status": "error", "reason": "File太小"}
                
                # 检查DEX魔数
                magic = data[0:8]
                is_valid_dex = magic in [b'dex\n035\x00', b'dex\n036\x00', b'dex\n037\x00', b'dex\n038\x00', b'dex\n039\x00']
                
                # 检查FileSize（从偏移0x20开始，4字节小端）
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
                
                # AnalysisResult
                result = {
                    "status": "success",
                    "magic": magic.hex(),
                    "is_valid_dex": is_valid_dex,
                    "file_size": file_size,
                    "checksum": checksum,
                    "signature": signature,
                    "analysis": {}
                }
                
                # 判断是否Encrypting或Obfuscating
                if not is_valid_dex:
                    result["analysis"]["warning"] = "DEX魔数Exception，可能被Encrypting或Modifying"
                    # 尝试检查是否为常见的Reinforcement特征
                    if magic[0:4] == b'\x00\x00\x00\x00':
                        result["analysis"]["suspicion"] = "可能为零填充Encrypting"
                else:
                    result["analysis"]["conclusion"] = "标准DEX格式，可能未Encrypting"
                    
                    # 检查是否有常见的Reinforcement特征
                    # Reading更多Data检查是否有明显的Encrypting模式
                    f.seek(0)
                    sample_data = f.read(1024)
                    zero_count = sample_data.count(b'\x00')
                    if zero_count > 512:  # 超过50%为零
                        result["analysis"]["suspicion"] = "高零值比例，可能为简单Encrypting或填充"
                
                return result
                
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    def analyze_native_libs(self, apk_zip: zipfile.ZipFile) -> Dict:
        """Analysis原生Library特征"""
        self.log("Analysis原生LibraryFile...")
        
        # 检查所有.soFile，包括assets/Directory下的ReinforcementLibrary
        lib_files = [f for f in apk_zip.namelist() if f.endswith('.so')]
        results = {
            "lib_count": len(lib_files),
            "lib_files": lib_files,
            "protection_indicators": [],
            "security_libs": [],
            "sdk_libs": []
        }
        
        if len(lib_files) == 0:
            self.log("❌ 未找到原生LibraryFile", "WARNING")
        else:
            self.log(f"✅ 发现 {len(lib_files)} 个原生LibraryFile")
        
        # 检查Reinforcement feature library
        protection_found = False
        for lib_file in lib_files:
            lib_name = os.path.basename(lib_file)
            
            # 检查是否是白名单SDK
            if self.is_whitelisted(lib_file):
                results["sdk_libs"].append(lib_file)
                continue
            
            # 检查Reinforcement特征
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
            
            # 如果没有匹配Reinforcement特征，检查是否是其他SecurityLibrary
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
            self.log(f"⚠️  发现Reinforcement特征Library", "WARNING")
        else:
            self.log("✅ 未发现明显的Reinforcement特征Library", "SUCCESS")
        
        return results
    
    def analyze_manifest(self, apk_zip: zipfile.ZipFile) -> Dict:
        """AnalysisAndroidManifest.xml"""
        self.log("AnalysisAndroidManifest.xml...")
        
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
                    
                    # 简单文本检查（实际Application中应使用AXML解析器）
                    try:
                        text = content.decode('utf-8', errors='ignore')
                        
                        # 检查Debugging属性
                        if 'android:debuggable="true"' in text:
                            results["debuggable"] = True
                            self.log("⚠️  Application可Debugging (debuggable=true)", "WARNING")
                        
                        # 检查Backing up属性
                        if 'android:allowBackup="false"' in text:
                            results["backup_allowed"] = False
                            self.log("✅ Backing upDisabled (SecurityConfiguration)", "INFO")
                        
                        # 检查Reinforcement相关特征
                        if 'com.ijiami' in text:
                            results["protection_indicators"].append({
                                "type": "manifest",
                                "vendor": "ijiami",
                                "indicator": "Package name包含ijiami"
                            })
                        
                    except:
                        pass
            else:
                self.log("❌ 未找到AndroidManifest.xml", "WARNING")
                
        except Exception as e:
            self.log(f"AnalysisManifestFailed: {e}", "DEBUG")
        
        return results
    
    def analyze_resources(self, apk_zip: zipfile.ZipFile) -> Dict:
        """AnalysisResourceFile"""
        self.log("AnalysisResourceFile...")
        
        results = {
            "resource_count": 0,
            "protection_indicators": [],
            "unusual_files": []
        }
        
        file_list = apk_zip.namelist()
        results["resource_count"] = len(file_list)
        
        # ReinforcementResourceFile特征模式
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
                r"assets/libwbsafeedit.*",  # 腾讯WebSecurity编辑组件
            ],
            "ali": [
                r"assets/aliprotect.*",
                r"assets/alisec.*",
            ],
            "bangcle": [
                r"assets/meta-data/.*",  # 梆梆Reinforcement企业版签名FileDirectory
                r"assets/.*bangcle.*",
                r"assets/.*bangele.*",
                r"assets/.*libdexjni.*",
                r"assets/.*libDexHelper.*",
            ],
            # 网易易盾ResourceFile特征
            "netease": [
                r"assets/netease.*",
                r"assets/yidun.*",
                r"assets/nd.*",
                r"assets/libnesec.*",
                r"assets/libneso.*",
            ]
        }
        
        for file_name in file_list:
            # 跳过白名单File
            if self.is_whitelisted(file_name):
                continue
                
            # 检查是否是明显的ReinforcementResourceFile
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
        """AnalysisDEXFileStatus"""
        status = {
            "is_normal_dex": False,
            "is_encrypted": False,
            "is_obfuscated": False,
            "details": []
        }
        
        # 检查DEX头AnalysisResult
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
                        status["details"].append("DEX魔数Exception")
        
        # 如果没有深度AnalysisResult，使用简单判断
        if not dex_headers and dex_results.get("dex_count", 0) > 0:
            # 假设DEX正常，直到有证据证明Exception
            status["is_normal_dex"] = True
            status["details"].append("未深度Analysis，假设为标准DEX")
        
        return status
    
    def calculate_protection_level(self, dex_results: Dict, native_results: Dict, 
                                  manifest_results: Dict, resource_results: Dict):
        """综合判断Protection级别"""
        
        # 收集所有Protection指标
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
        
        # AnalysisDEXStatus
        dex_status = self.analyze_dex_status(dex_results)
        self.log(f"📊 DEXStatusAnalysis: 正常={dex_status['is_normal_dex']}, Encrypting={dex_status['is_encrypted']}", "DEBUG")
        
        # 计算初始confidence score
        total_score = sum(vendor_scores.values())
        max_score = len(all_indicators) * 3 if all_indicators else 0
        confidence = total_score / max_score if max_score > 0 else 0
        
        # 考虑DEX深度AnalysisResult
        dex_headers = dex_results.get("dex_headers", [])
        if dex_headers:
            for dex_analysis in dex_headers:
                if dex_analysis.get("status") == "success" and dex_analysis.get("is_valid_dex"):
                    # Standard DEX format，大幅降低Reinforcement可能性
                    confidence = confidence * 0.3  # confidence score大幅降低
                    self.log(f"📊 标准DEX格式Detected，大幅降低Reinforcement置信度至 {confidence:.1%}", "DEBUG")
        

        
        # 确定Protection类型 - 使用更严格的判断逻辑
        protection_type = "none"
        protection_level = "basic"
        
        if vendor_scores:
            # 选择得分最高的厂商
            protection_type = max(vendor_scores.items(), key=lambda x: x[1])[0]
            top_score = vendor_scores[protection_type]
            
            # 基于DEXStatus和特征强度进行综合判断
            if dex_status["is_normal_dex"]:
                # DEX正常，需要更强的证据才能判断为Reinforcement
                if top_score >= 2.0 and strong_indicators_count >= 1:
                    protection_level = "commercial"
                elif top_score >= 1.0 and weak_indicators_count <= 2:
                    protection_level = "basic"
                else:
                    # 分数不够高，可能是误判
                    protection_type = "none"
                    protection_level = "basic"
                    confidence = max(confidence * 0.2, 0.1)  # 大幅降低confidence score
            else:
                # DEXException，更容易判断为Reinforcement
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
            # 没有DetectedReinforcement特征
            if dex_results.get("dex_count", 0) == 1:
                # 单DEX可能是简单Protection或未Reinforcement
                protection_type = "unknown"
                protection_level = "basic"
            else:
                protection_type = "none"
                protection_level = "basic"
        
        # 特殊情况：如果只有弱特征且DEX正常，强制判断为无Reinforcement
        if vendor_scores and dex_status["is_normal_dex"]:
            weak_indicators_only = weak_indicators_count > 0 and strong_indicators_count == 0
            if weak_indicators_only and top_score < 1.5:
                protection_type = "none"
                protection_level = "basic"
                confidence = 0.1  # 极低confidence score
                self.log(f"📊 只有弱特征且DEX正常，强制判断为无Reinforcement", "DEBUG")
        
        # 特殊情况：多个DEXFile且都正常，通常不是Reinforcement
        if dex_results.get("dex_count", 0) > 1 and dex_status["is_normal_dex"]:
            if protection_type != "none" and top_score < 2.0:
                protection_type = "none"
                protection_level = "basic"
                confidence = confidence * 0.5
                self.log(f"📊 多个正常DEXFile，降低Reinforcement可能性", "DEBUG")
        
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
        """生成UnpackingRecommendation"""
        protection_type = self.analysis_results["protection_type"]
        protection_level = self.analysis_results["protection_level"]
        confidence = self.analysis_results["confidence_score"]
        
        recommendations = []
        
        # 1. Low confidence warning（优先显示）
        if confidence < 0.3:
            recommendations.append("⚠️  **低置信度Warning**: DetectionResult置信度较低 (低于30%)，可能存在误判")
        
        # 2. 基于Protection类型的Recommendation
        if protection_type == "none" and protection_level == "basic":
            recommendations.extend([
                "✅ Application可能未Reinforcement或使用简单Protection",
                "💡 Recommendation: 使用标准Unpacking模式 (android-armor-breaker --package <Package name>)",
                "📊 预估成功率: 95%以上",
                "⏱️  预估Time: 1-2分钟"
            ])

                
        elif protection_type == "ijiami":
            if protection_level == "enterprise":
                recommendations.extend([
                    "⚠️  Detected爱Encrypting企业版Reinforcement",
                    "💡 Recommendation: 使用激进Unpacking策略",
                    "🛠️  推荐Parameter: --bypass-antidebug --dynamic-puzzle",
                    "📊 预估成功率: 30-50% (基于历史TestingData)",
                    "⏱️  预估Time: 5-10分钟",
                    "🔑 关键: 可能需要Root权限进行MemoryAttack"
                ])
            else:
                recommendations.extend([
                    "✅ Detected爱EncryptingReinforcement (标准版)",
                    "💡 Recommendation: 使用深度搜索模式",
                    "🛠️  推荐Parameter: --deep-search --bypass-antidebug",
                    "📊 预估成功率: 70-85%",
                    "⏱️  预估Time: 2-4分钟"
                ])
                
        elif protection_type == "360":
            recommendations.extend([
                "✅ Detected360Reinforcement",
                "💡 Recommendation: 使用深度搜索模式",
                "🛠️  推荐Parameter: --deep-search",
                "📊 预估成功率: 80-90%",
                "⏱️  预估Time: 2-3分钟"
            ])
            
        elif protection_type == "baidu":
            recommendations.extend([
                "✅ Detected百度Reinforcement",
                "💡 Recommendation: 使用深度搜索模式突破DEX数量限制",
                "🛠️  推荐Parameter: --deep-search",
                "📊 预估成功率: 85-95%",
                "⏱️  预估Time: 2-3分钟",
                "💾 经验: 可突破26个DEX限制，获取完整53个DEX"
            ])
            
        elif protection_type == "tencent":
            recommendations.extend([
                "✅ Detected腾讯Reinforcement",
                "💡 Recommendation: 使用Anti-debugBypass+深度搜索",
                "🛠️  推荐Parameter: --deep-search --bypass-antidebug",
                "📊 预估成功率: 75-85%",
                "⏱️  预估Time: 3-5分钟"
            ])
            
        elif protection_type == "ali":
            # 阿里Reinforcement特别处理，因为容易误判
            if confidence < 0.5:
                recommendations.extend([
                    f"⚠️  Detected阿里Reinforcement (置信度: {confidence*100:.1f}%)",
                    "🔍 **Note**: 阿里ReinforcementDetection容易误判，libEncryptorP.so等Library可能是Application自有Encrypting",
                    "🔄 **Unpacking策略**: 如果确实有Anti-debugProtection，使用 --bypass-antidebug Parameter"
                ])
            else:
                recommendations.extend([
                    "✅ Detected阿里Reinforcement",
                    "💡 Recommendation: 使用自适应策略",
                    "🛠️  推荐Parameter: --bypass-antidebug --deep-search",
                    f"📊 置信度: {confidence*100:.1f}%",
                    "⏱️  预估Time: 3-5分钟"
                ])
                
        else:
            # 其他Reinforcement类型
            recommendations.extend([
                f"✅ Detected {protection_type} Reinforcement (Protection级别: {protection_level})",
                "💡 Recommendation: 尝试自适应策略",
                "🛠️  推荐Parameter: --detect-protection (让技能自动选择最佳策略)",
                f"📊 置信度: {confidence*100:.1f}%",
                "⏱️  预估Time: 2-5分钟"
            ])
        
        # 3. DEXFile直接提取Recommendation（如果DEX数量多且可能未Reinforcement）
        dex_count = self.analysis_results.get("detailed_findings", {}).get("dex", {}).get("dex_count", 0)
        if dex_count >= 2 and confidence < 0.4:
            recommendations.append("📦 **直接提取Recommendation**: 可尝试直接从APK提取DEX: `unzip -j apk '*.dex'`")
        
        self.analysis_results["recommendations"] = recommendations
    
    def print_report(self):
        """打印AnalysisReport"""
        results = self.analysis_results
        
        self.log("=" * 60)
        self.log("📊 APKReinforcementAnalysisReport")
        self.log("=" * 60)
        self.log(f"📦 File: {results['apk_file']}")
        self.log(f"📏 Size: {results['file_size'] / (1024*1024):.1f} MB")
        self.log("")
        
        self.log("🔐 ReinforcementAnalysisResult:")
        self.log(f"  Protection类型: {results['protection_type'].upper()}")
        self.log(f"  Protection级别: {results['protection_level'].upper()}")
        self.log(f"  Detected的厂商: {', '.join(results['detected_vendors']) if results['detected_vendors'] else '无'}")
        self.log(f"  置信度: {results['confidence_score']*100:.1f}%")
        
        self.log("")
        
        # 详细发现
        details = results['detailed_findings']
        if details.get('dex', {}).get('dex_count', 0) > 0:
            dex_info = details['dex']
            self.log(f"📄 DEXFile: {dex_info['dex_count']} 个")
            
            # 显示DEX头AnalysisResult
            dex_headers = dex_info.get('dex_headers', [])
            if dex_headers:
                for dex_analysis in dex_headers[:2]:  # 只显示前2个AnalysisResult
                    if dex_analysis.get('status') == 'success':
                        magic = dex_analysis.get('magic', '未知')
                        is_valid = dex_analysis.get('is_valid_dex', False)
                        file_size = dex_analysis.get('file_size', 0)
                        
                        if is_valid:
                            self.log(f"  ✅ DEX头部: 标准格式 (magic: {magic}), Size: {file_size:,} 字节")
                            if dex_analysis.get('analysis', {}).get('conclusion'):
                                self.log(f"    Analysis: {dex_analysis['analysis']['conclusion']}")
                        else:
                            self.log(f"  ⚠️  DEX头部: Exception格式 (magic: {magic})")
                            if dex_analysis.get('analysis', {}).get('warning'):
                                self.log(f"    Warning: {dex_analysis['analysis']['warning']}")
        
        if details.get('native', {}).get('lib_count', 0) > 0:
            native_info = details['native']
            self.log(f"⚙️  原生Library: {native_info['lib_count']} 个")
            
            # 显示SecurityLibrary（非Reinforcement特征）
            security_libs = native_info.get('security_libs', [])
            if security_libs:
                self.log("  🔒 Detected的SecurityLibrary (可能为Application自有):")
                for lib in security_libs[:3]:  # 只显示前3个
                    self.log(f"    - {os.path.basename(lib)}")
            
            # 显示Reinforcement feature library
            if native_info.get('protection_indicators'):
                self.log("  🔍 Detected的Reinforcement特征Library:")
                for indicator in native_info['protection_indicators'][:5]:  # 只显示前5个
                    self.log(f"    - {indicator['vendor']}: {os.path.basename(indicator['file'])}")
        
        self.log("")
        
        # Recommendation
        self.log("🎯 UnpackingRecommendation:")
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
    
    parser = argparse.ArgumentParser(description='APKReinforcement类型Analysis器')
    parser.add_argument('--apk', '-a', required=True, help='APKFilePath')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细Output')
    
    args = parser.parse_args()
    
    analyzer = ApkProtectionAnalyzer(verbose=args.verbose)
    results = analyzer.analyze_apk(args.apk)
    analyzer.print_report()
    
    # 保存Result到File
    output_file = os.path.splitext(args.apk)[0] + '_protection_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📁 详细Result已保存到: {output_file}")

if __name__ == '__main__':
    main()