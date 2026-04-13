#!/usr/bin/env python3
"""
APK reinforcement Type Analyzer
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

# 国际化导入
from i18n_logger import get_logger

class ApkprotectionAnalyzer:
    """APKreinforcementanalysis器"""
    
    def __init__(self, verbose: bool = True, language: str = 'en-US', json_mode: bool = False):
        """Initialize ApkprotectionAnalyzer
        
        Args:
            verbose: Enable verbose logging
            language: Language code (en-US, zh-CN)
            json_mode: If True, suppresses log output for clean JSON output
        """
        self.logger = get_logger(language=language, verbose=verbose, module="apk_protection_analyzer")
        self.verbose = verbose
        self.json_mode = json_mode
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
        
        # reinforcement feature library
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
                (r"libmain\.so$", "weak"),  # 注意：也可能是普通库
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
        }
    
    def log(self, key: str, level: str = "INFO", **kwargs):
        """Log a message, but suppress if in JSON mode"""
        if self.json_mode:
            return  # 在JSON模式下不输出日志
        self.logger.log(key, level, **kwargs)
    
    def analyze_apk(self, apk_path: str) -> Dict:
        """分析APK文件"""
        self.log("analyzing_apk", apk=apk_path)
        
        if not os.path.exists(apk_path):
            self.log("apk_file_not_found", "ERROR", path=apk_path)
            return self.analysis_results
        
        self.apk_path = apk_path
        self.analysis_results["apk_file"] = apk_path
        self.analysis_results["file_size"] = os.path.getsize(apk_path)
        
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk_zip:
                file_list = apk_zip.namelist()
                self.log("apk_opened", file_count=len(file_list))
                
                # 分析每个文件
                findings = {}
                for vendor, patterns in self.protection_patterns.items():
                    vendor_findings = []
                    for pattern, strength in patterns:
                        matched_files = [f for f in file_list if re.search(pattern, f, re.IGNORECASE)]
                        if matched_files:
                            vendor_findings.append({
                                "pattern": pattern,
                                "strength": strength,
                                "files": matched_files[:5],  # 只显示前5个匹配文件
                                "count": len(matched_files)
                            })
                    
                    if vendor_findings:
                        findings[vendor] = vendor_findings
                        self.log("vendor_detected", vendor=vendor, count=len(vendor_findings))
                
                # 确定加固类型
                if findings:
                    # 按匹配强度排序
                    vendors_by_strength = []
                    for vendor, vendor_findings in findings.items():
                        strong_matches = sum(1 for f in vendor_findings if f["strength"] == "strong")
                        medium_matches = sum(1 for f in vendor_findings if f["strength"] == "medium")
                        weak_matches = sum(1 for f in vendor_findings if f["strength"] == "weak")
                        
                        # 计算置信度分数
                        confidence = (strong_matches * 0.7 + medium_matches * 0.3 + weak_matches * 0.1) / 10
                        confidence = min(confidence, 1.0)
                        
                        vendors_by_strength.append({
                            "vendor": vendor,
                            "confidence": confidence,
                            "strong_matches": strong_matches,
                            "medium_matches": medium_matches,
                            "weak_matches": weak_matches
                        })
                    
                    # 按置信度排序
                    vendors_by_strength.sort(key=lambda x: x["confidence"], reverse=True)
                    
                    if vendors_by_strength:
                        top_vendor = vendors_by_strength[0]
                        self.analysis_results["protection_type"] = top_vendor["vendor"]
                        self.analysis_results["confidence_score"] = top_vendor["confidence"]
                        self.analysis_results["detected_vendors"] = [v["vendor"] for v in vendors_by_strength[:3]]
                        
                        # 确定保护级别
                        if top_vendor["confidence"] > 0.7:
                            self.analysis_results["protection_level"] = "enterprise"
                        elif top_vendor["confidence"] > 0.3:
                            self.analysis_results["protection_level"] = "commercial"
                        else:
                            self.analysis_results["protection_level"] = "basic"
                        
                        self.log("protection_analysis_complete", "SUCCESS",
                                type=top_vendor["vendor"],
                                confidence=top_vendor["confidence"],
                                level=self.analysis_results["protection_level"])
                else:
                    self.analysis_results["protection_type"] = "none"
                    self.analysis_results["protection_level"] = "none"
                    self.analysis_results["confidence_score"] = 1.0
                    self.log("no_protection_detected", "INFO")
                
                self.analysis_results["detailed_findings"] = findings
                
                # 生成建议
                self.generate_recommendations()
                
                return self.analysis_results
                
        except Exception as e:
            self.log("apk_analysis_failed", "ERROR", error=str(e))
            return self.analysis_results
    
    def generate_recommendations(self):
        """生成解包建议"""
        protection_type = self.analysis_results["protection_type"]
        protection_level = self.analysis_results["protection_level"]
        
        recommendations = []
        
        if protection_type == "none":
            recommendations.append("使用标准Frida动态解包策略")
        elif protection_type in ["ijiami", "bangcle", "360", "tencent"]:
            recommendations.append("使用Root内存提取策略（商业加固）")
            if protection_level == "enterprise":
                recommendations.append("可能需要多次尝试和特殊处理")
        elif protection_type == "baidu":
            recommendations.append("使用增强版Frida解包（新百度加固）")
        elif protection_type == "netease":
            recommendations.append("使用Root内存提取 + VDEX处理（网易易盾）")
        else:
            recommendations.append("先尝试Frida动态解包，失败后使用Root内存提取")
        
        self.analysis_results["recommendations"] = recommendations
        self.log("recommendations_generated", count=len(recommendations))

def main():
    """Main function for testing"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(
        description='APK Protection Analyzer - Detect reinforcement types and protection levels'
    )
    
    parser.add_argument('--apk', '-a', required=True, help='APK file path to analyze')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--language', '-l', default='en-US', choices=['en-US', 'zh-CN'], 
                       help='Language for output (en-US, zh-CN)')
    parser.add_argument('--json', '-j', action='store_true', help='Output results as JSON')
    parser.add_argument('--output', '-o', help='Output JSON file path (default: <apk_name>_protection_analysis.json)')
    
    args = parser.parse_args()
    
    # 在JSON模式下，我们抑制日志输出以保持干净的JSON
    analyzer = ApkprotectionAnalyzer(verbose=args.verbose, language=args.language, json_mode=args.json)
    
    # 执行分析
    result = analyzer.analyze_apk(args.apk)
    
    # JSON输出模式
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 保存JSON文件（如果指定了输出文件）
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        # 自动生成JSON文件
        apk_base = os.path.splitext(args.apk)[0]
        json_file = f"{apk_base}_protection_analysis.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 文本输出（保持向后兼容）
    print("=" * 60)
    print("🔍 APK Protection Analyzer - Internationalized Version")
    print(f"📁 APK: {args.apk}")
    print(f"🌐 Language: {args.language}")
    print("=" * 60)
    
    print("\n1. Testing APK analysis...")
    print(f"\n2. Analysis Results:")
    print(f"   文件: {result.get('apk_file', 'N/A')}")
    print(f"   大小: {result.get('file_size', 0):,} bytes")
    print(f"   加固类型: {result.get('protection_type', 'unknown')}")
    print(f"   保护级别: {result.get('protection_level', 'unknown')}")
    print(f"   置信度: {result.get('confidence_score', 0.0):.1%}")
    
    vendors = result.get('detected_vendors', [])
    if vendors:
        print(f"   检测到的厂商: {', '.join(vendors)}")
    
    recommendations = result.get('recommendations', [])
    if recommendations:
        print(f"\n3. 建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    print("\n" + "=" * 60)
    print("✅ Internationalization test completed")
    print("=" * 60)

if __name__ == "__main__":
    main()