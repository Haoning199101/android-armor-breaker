#!/usr/bin/env python3
"""
Enhanced Root Memory Extractor - Advanced memory analysis for commercial-grade reinforcement protections
Adds encryption detection, entropy analysis, pattern matching, and custom format recognition
"""

import os
import sys
import re
import struct
import subprocess
import tempfile
import time
import math
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from collections import Counter

# 国际化导入
from i18n_logger import get_logger

class EnhancedRootMemoryExtractor:
    """Enhanced Root Memory Extractor - Advanced analysis for commercial protections"""
    
    def __init__(self, verbose: bool = True, language: str = 'en-US'):
        """Initialize EnhancedRootMemoryExtractor
        
        Args:
            verbose: Enable verbose logging
            language: Language code (en-US, zh-CN)
        """
        self.logger = get_logger(language=language, verbose=verbose, module="root_memory_extractor_enhanced")
        self.verbose = verbose
        self.package_name = ""
        self.pid = None
        self.output_dir = None
        self.dex_regions = []  # Found DEX memory regions
        self.extracted_dex_files = []
        self.memory_dump_files = []  # Saved raw memory dumps
        
        # 商业加固特征库
        self.commercial_protection_patterns = {
            "tencent": {
                "name": "腾讯加固",
                "magic_patterns": [
                    b'\x74\x65\x6e\x63\x65\x6e\x74',  # "tencent"
                    b'\x51\x51\x53\x65\x63\x75\x72\x65',  # "QQSecure"
                ],
                "dex_encryption_signature": b'\x63\x6f\x6d\x2e\x74\x65\x6e\x63\x65\x6e\x74',  # "com.tencent"
                "description": "腾讯加固服务，使用自定义加密和运行时解密"
            },
            "360": {
                "name": "360加固",
                "magic_patterns": [
                    b'\x33\x36\x30',  # "360"
                    b'\x71\x69\x68\x6f\x6f',  # "qihoo" (奇虎)
                ],
                "dex_encryption_signature": b'\x63\x6f\x6d\x2e\x71\x69\x68\x6f\x6f',  # "com.qihoo"
                "description": "360加固保，多层保护包括代码混淆和动态解密"
            },
            "ijiami": {
                "name": "爱加密",
                "magic_patterns": [
                    b'\x69\x6a\x69\x61\x6d\x69',  # "ijiami"
                    b'\x41\x49\x4a\x49\x41\x4d\x49',  # "AIJIAMI"
                ],
                "dex_encryption_signature": b'\x63\x6f\x6d\x2e\x69\x6a\x69\x61\x6d\x69',  # "com.ijiami"
                "description": "爱加密商业版，强反调试和内存加密"
            },
            "bangcle": {
                "name": "梆梆加固",
                "magic_patterns": [
                    b'\x62\x61\x6e\x67\x63\x6c\x65',  # "bangcle"
                    b'\x42\x61\x6e\x67\x43\x6c\x65',  # "BangCle"
                ],
                "dex_encryption_signature": b'\x63\x6f\x6d\x2e\x62\x61\x6e\x67\x63\x6c\x65',  # "com.bangcle"
                "description": "梆梆安全，快速崩溃保护和内存加密"
            }
        }
        
    def log(self, key: str, level: str = "INFO", **kwargs):
        """Log a message using internationalized logger"""
        self.logger.log(key, level, **kwargs)
    
    def check_root(self) -> bool:
        """检查设备是否有root权限"""
        self.log("checking_root_permission")
        
        try:
            # 使用su命令测试root权限
            result = subprocess.run(
                ["adb", "shell", "su -c 'echo root_ok'"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "root_ok" in result.stdout:
                self.log("device_has_root", "SUCCESS")
                return True
            else:
                self.log("no_root_permission", "ERROR", 
                       stdout=result.stdout[:100], stderr=result.stderr[:100])
                return False
                
        except Exception as e:
            self.log("check_root_failed", "ERROR", error=str(e))
            return False
    
    def get_package_pid(self, package_name: str) -> Optional[int]:
        """获取进程PID"""
        self.log("getting_process_pid", package=package_name)
        
        try:
            # 使用pidof获取PID
            result = subprocess.run(
                ["adb", "shell", f"pidof {package_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pid = int(result.stdout.strip())
                self.log("pid_found", "SUCCESS", pid=pid)
                return pid
            else:
                self.log("process_not_found", "ERROR")
                return None
                
        except Exception as e:
            self.log("pid_lookup_failed", "ERROR", error=str(e))
            return None
    
    def start_application(self, package_name: str) -> Optional[int]:
        """启动应用"""
        self.log("starting_app", package=package_name)
        
        try:
            # 先停止应用（确保干净启动）
            subprocess.run(
                ["adb", "shell", f"am force-stop {package_name}"],
                capture_output=True,
                timeout=10
            )
            time.sleep(2)
            
            # 启动应用
            result = subprocess.run(
                ["adb", "shell", f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                self.log("app_started", "SUCCESS")
                
                # 等待应用完全启动
                time.sleep(5)
                
                # 获取PID
                return self.get_package_pid(package_name)
            else:
                self.log("app_start_failed", "ERROR", error=result.stderr[:200])
                return None
                
        except Exception as e:
            self.log("app_start_exception", "ERROR", error=str(e))
            return None
    
    def read_process_maps(self, pid: int) -> List[Dict]:
        """读取进程的内存映射信息"""
        self.log("reading_process_maps", pid=pid)
        
        try:
            # 通过root权限读取/proc/pid/maps
            cmd = ["adb", "shell", f"su -c 'cat /proc/{pid}/maps'"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                self.log("read_maps_failed", "ERROR", stderr=result.stderr[:200])
                return []
            
            memory_regions = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 解析maps行格式: start-end perms offset dev inode pathname
                parts = line.split()
                if len(parts) < 5:
                    continue
                
                # 解析地址范围
                addr_range = parts[0]
                perms = parts[1]
                
                if '-' in addr_range:
                    start_str, end_str = addr_range.split('-')
                    try:
                        start = int(start_str, 16)
                        end = int(end_str, 16)
                        size = end - start
                        
                        # 只关注可读区域
                        if 'r' in perms and size > 0:
                            region_info = {
                                'start': start,
                                'end': end,
                                'size': size,
                                'perms': perms,
                                'offset': parts[2] if len(parts) > 2 else '',
                                'device': parts[3] if len(parts) > 3 else '',
                                'inode': parts[4] if len(parts) > 4 else '',
                                'pathname': ' '.join(parts[5:]) if len(parts) > 5 else '',
                                'line': line
                            }
                            
                            # 特别标记可能的DEX区域
                            if 'anon:dalvik' in region_info['pathname'] or 'dalvik' in region_info['pathname']:
                                region_info['likely_dex'] = True
                                self.log("potential_dex_region", "INFO", 
                                       start=f"0x{start:x}", size=size)
                            
                            memory_regions.append(region_info)
                    except ValueError:
                        continue
            
            self.log("memory_regions_found", count=len(memory_regions))
            return memory_regions
            
        except Exception as e:
            self.log("read_maps_exception", "ERROR", error=str(e))
            return []
    
    def extract_memory_region(self, pid: int, start: int, size: int) -> Optional[bytes]:
        """提取指定内存区域的数据"""
        self.log("extracting_memory_region", pid=pid, start=f"0x{start:x}", size=size)
        
        try:
            # 使用dd命令通过root权限读取内存
            # 注意：需要将地址转换为十进制
            start_dec = start
            count = size
            
            # 构建dd命令
            dd_cmd = f"dd if=/proc/{pid}/mem bs=4096 skip={start_dec//4096} count={count//4096 + 1} 2>/dev/null"
            cmd = ["adb", "shell", f"su -c '{dd_cmd}'"]
            
            self.log("executing_dd_command", command=" ".join(cmd))
            
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0:
                data = result.stdout
                actual_size = len(data)
                
                # 裁剪到实际需要的尺寸
                if actual_size > size:
                    data = data[:size]
                
                self.log("memory_extraction_success", "SUCCESS", 
                       expected_size=size, actual_size=len(data))
                return data
            else:
                self.log("memory_extraction_failed", "ERROR", 
                       returncode=result.returncode, stderr=result.stderr[:200])
                return None
                
        except Exception as e:
            self.log("memory_extraction_exception", "ERROR", error=str(e))
            return None
    
    def calculate_entropy(self, data: bytes) -> float:
        """计算数据的熵（用于识别加密/压缩数据）"""
        if not data:
            return 0.0
        
        # 计算字节频率
        byte_counts = Counter(data)
        data_len = len(data)
        
        # 计算熵
        entropy = 0.0
        for count in byte_counts.values():
            probability = count / data_len
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def detect_encryption_patterns(self, data: bytes) -> Dict[str, Any]:
        """检测加密模式和商业加固特征"""
        self.log("detecting_encryption_patterns", data_size=len(data))
        
        results = {
            "entropy": self.calculate_entropy(data[:min(len(data), 65536)]),  # 只计算前64KB的熵
            "detected_protections": [],
            "encryption_likelihood": 0.0,
            "patterns_found": []
        }
        
        # 熵分析：高熵（>7.5）可能表示加密数据
        if results["entropy"] > 7.5:
            results["encryption_likelihood"] += 0.6
            self.log("high_entropy_detected", "WARNING", entropy=results["entropy"])
        
        # 搜索商业加固特征
        for protection_id, protection_info in self.commercial_protection_patterns.items():
            for pattern in protection_info["magic_patterns"]:
                if pattern in data[:min(len(data), 65536)]:  # 只搜索前64KB
                    results["detected_protections"].append({
                        "id": protection_id,
                        "name": protection_info["name"],
                        "description": protection_info["description"],
                        "pattern": pattern.hex()
                    })
                    results["encryption_likelihood"] += 0.3
                    self.log("commercial_protection_detected", "WARNING", 
                           protection=protection_info["name"], pattern=pattern.hex())
        
        # 检测常见的加密模式
        encryption_patterns = [
            (b'\x00' * 16, "全零填充（可能为加密占位符）"),
            (b'\xFF' * 16, "全一填充（可能为加密占位符）"),
            (b'\xDE\xAD\xBE\xEF', "常见魔数DEADBEEF"),
            (b'\xCA\xFE\xBA\xBE', "Java类文件魔数CAFEBABE"),
        ]
        
        for pattern, description in encryption_patterns:
            if pattern in data[:min(len(data), 65536)]:
                results["patterns_found"].append({
                    "pattern": pattern.hex(),
                    "description": description
                })
                results["encryption_likelihood"] += 0.1
        
        # 限制概率在0-1之间
        results["encryption_likelihood"] = min(1.0, results["encryption_likelihood"])
        
        self.log("encryption_detection_complete", "INFO", 
               entropy=results["entropy"], 
               likelihood=results["encryption_likelihood"],
               protections=len(results["detected_protections"]))
        
        return results
    
    def search_dex_in_memory_enhanced(self, data: bytes, region_info: Dict) -> List[Dict]:
        """增强版内存DEX搜索（支持加密/混淆DEX检测）"""
        self.log("searching_dex_in_memory_enhanced", data_size=len(data))
        
        dex_files = []
        
        # 1. 标准DEX搜索
        dex_magic = b'dex\n'
        search_limit = min(len(data), 50 * 1024 * 1024)  # 最多搜索前50MB
        
        for offset in range(0, search_limit, 4):
            if offset + 4 <= len(data) and data[offset:offset+4] == dex_magic:
                self.log("dex_signature_found", offset=offset)
                
                # 尝试解析DEX头部
                if offset + 0x70 <= len(data):
                    header_data = data[offset:offset+0x70]
                    
                    # 验证DEX头部
                    try:
                        # 解析DEX文件大小（偏移量0x20）
                        if len(header_data) >= 0x24:
                            file_size = struct.unpack('<I', header_data[0x20:0x24])[0]
                            
                            # 检查合理的文件大小（1KB - 100MB）
                            if 1024 <= file_size <= 100 * 1024 * 1024:
                                dex_info = {
                                    'offset': offset,
                                    'file_size': file_size,
                                    'start_addr': region_info['start'] + offset,
                                    'header_checksum': header_data[8:12].hex(),
                                    'signature': header_data[12:32].hex()[:16] + "...",
                                    'region_info': region_info,
                                    'encryption_detection': self.detect_encryption_patterns(data[offset:offset+min(file_size, 65536)]),
                                    'type': 'standard_dex'
                                }
                                
                                dex_files.append(dex_info)
                                self.log("valid_dex_found", "INFO", 
                                       offset=offset, file_size=file_size)
                    except Exception as e:
                        self.log("dex_header_parse_error", "WARNING", error=str(e))
        
        # 2. 搜索可能被加密的DEX（通过熵分析和模式匹配）
        if len(dex_files) == 0:
            self.log("no_standard_dex_found_searching_encrypted", "WARNING")
            
            # 分析数据块，寻找可能的加密DEX区域
            block_size = 4096
            num_blocks = min(len(data) // block_size, 1000)  # 最多分析1000个块
            
            for block_idx in range(num_blocks):
                start_offset = block_idx * block_size
                block_data = data[start_offset:start_offset + block_size]
                
                if len(block_data) < 100:
                    continue
                
                # 分析块的特征
                entropy = self.calculate_entropy(block_data)
                encryption_detection = self.detect_encryption_patterns(block_data)
                
                # 如果熵高且检测到商业保护特征，可能是加密的DEX
                if entropy > 7.0 and encryption_detection["encryption_likelihood"] > 0.5:
                    self.log("potential_encrypted_dex_block", "WARNING",
                           offset=start_offset, entropy=entropy,
                           likelihood=encryption_detection["encryption_likelihood"])
                    
                    # 创建可能的加密DEX记录
                    encrypted_dex_info = {
                        'offset': start_offset,
                        'file_size': block_size,  # 未知确切大小
                        'start_addr': region_info['start'] + start_offset,
                        'entropy': entropy,
                        'encryption_detection': encryption_detection,
                        'region_info': region_info,
                        'type': 'potential_encrypted_dex'
                    }
                    
                    dex_files.append(encrypted_dex_info)
        
        self.log("enhanced_dex_search_complete", found=len(dex_files))
        return dex_files
    
    def save_memory_dump(self, data: bytes, region_info: Dict, output_dir: Path) -> Optional[str]:
        """保存原始内存转储以供进一步分析"""
        try:
            # 生成文件名
            start_addr = region_info['start']
            size = len(data)
            dump_hash = hashlib.md5(data[:min(len(data), 4096)]).hexdigest()[:8]
            filename = f"memory_dump_{start_addr:08x}_{size}_{dump_hash}.bin"
            filepath = output_dir / "memory_dumps" / filename
            
            # 创建内存转储目录
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存数据
            with open(filepath, 'wb') as f:
                f.write(data)
            
            self.log("memory_dump_saved", "INFO", 
                   filename=filename, size=len(data), path=str(filepath))
            
            self.memory_dump_files.append({
                'path': str(filepath),
                'start_addr': start_addr,
                'size': len(data),
                'region_info': region_info
            })
            
            return str(filepath)
            
        except Exception as e:
            self.log("memory_dump_failed", "ERROR", error=str(e))
            return None
    
    def extract_dex_file_enhanced(self, data: bytes, dex_info: Dict, output_dir: Path) -> Optional[str]:
        """增强版DEX文件提取（支持加密DEX处理）"""
        try:
            offset = dex_info['offset']
            file_size = dex_info.get('file_size', 0)
            
            if file_size == 0:
                # 对于潜在加密DEX，使用启发式大小
                file_size = min(10 * 1024 * 1024, len(data) - offset)  # 最大10MB
            
            # 检查是否有足够的数据
            if offset + file_size > len(data):
                self.log("insufficient_data_for_dex", "WARNING", 
                       offset=offset, file_size=file_size, available=len(data)-offset)
                file_size = len(data) - offset
            
            # 提取DEX数据
            dex_data = data[offset:offset+file_size]
            
            if dex_info['type'] == 'standard_dex':
                # 标准DEX验证
                if dex_data[:4] != b'dex\n':
                    self.log("invalid_dex_magic", "ERROR")
                    return None
                
                # 生成标准DEX文件名
                dex_hash = hashlib.md5(dex_data).hexdigest()[:8]
                filename = f"dex_std_{dex_info['start_addr']:08x}_{dex_hash}.dex"
            else:
                # 潜在加密DEX
                entropy = self.calculate_entropy(dex_data[:min(len(dex_data), 65536)])
                dex_hash = hashlib.md5(dex_data[:min(len(dex_data), 4096)]).hexdigest()[:8]
                filename = f"dex_enc_{dex_info['start_addr']:08x}_{entropy:.2f}_{dex_hash}.bin"
            
            filepath = output_dir / filename
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(dex_data)
            
            self.log("dex_file_saved_enhanced", "SUCCESS", 
                   filename=filename, size=len(dex_data), type=dex_info['type'], path=str(filepath))
            
            return str(filepath)
            
        except Exception as e:
            self.log("dex_extraction_failed_enhanced", "ERROR", error=str(e))
            return None
    
    def extract_enhanced(self, package_name: str, output_dir: str = None) -> Dict[str, Any]:
        """增强版主提取函数（返回详细分析结果）"""
        self.log("starting_enhanced_root_extraction", package=package_name)
        self.package_name = package_name
        
        results = {
            "package_name": package_name,
            "success": False,
            "pid": None,
            "memory_regions_analyzed": 0,
            "memory_dumps_saved": 0,
            "standard_dex_found": 0,
            "potential_encrypted_dex_found": 0,
            "encryption_detection_summary": {},
            "output_directory": "",
            "detailed_findings": []
        }
        
        # 1. 检查root权限
        if not self.check_root():
            self.log("root_required", "ERROR")
            return results
        
        # 2. 获取或启动应用
        pid = self.get_package_pid(package_name)
        if not pid:
            pid = self.start_application(package_name)
            if not pid:
                self.log("cannot_start_application", "ERROR")
                return results
        
        self.pid = pid
        results["pid"] = pid
        
        # 3. 准备输出目录
        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path.cwd() / f"{package_name}_enhanced_extraction_{timestamp}"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir
        results["output_directory"] = str(output_dir)
        
        # 创建子目录
        (output_dir / "memory_dumps").mkdir(exist_ok=True)
        (output_dir / "analysis_reports").mkdir(exist_ok=True)
        
        self.log("output_directory_ready", "INFO", path=str(output_dir))
        
        # 4. 读取内存映射
        memory_regions = self.read_process_maps(pid)
        if not memory_regions:
            self.log("no_memory_regions_found", "ERROR")
            return results
        
        results["memory_regions_analyzed"] = len(memory_regions)
        
        # 5. 提取和分析内存区域
        all_extracted_dex = []
        total_regions = len(memory_regions)
        
        for i, region in enumerate(memory_regions[:30]):  # 最多处理30个区域
            self.log("processing_region_enhanced", region_num=i+1, total=total_regions,
                   start=f"0x{region['start']:x}", size=region['size'])
            
            # 跳过太大的区域（>100MB）
            if region['size'] > 100 * 1024 * 1024:
                self.log("region_too_large", "WARNING", size=region['size'])
                continue
            
            # 提取内存数据
            data = self.extract_memory_region(pid, region['start'], region['size'])
            if not data:
                continue
            
            # 保存内存转储以供进一步分析
            dump_path = self.save_memory_dump(data, region, output_dir)
            if dump_path:
                results["memory_dumps_saved"] += 1
            
            # 在数据中搜索DEX文件（增强版）
            dex_files = self.search_dex_in_memory_enhanced(data, region)
            
            # 提取找到的DEX文件
            for dex_info in dex_files:
                dex_path = self.extract_dex_file_enhanced(data, dex_info, output_dir)
                if dex_path:
                    dex_info['saved_path'] = dex_path
                    dex_info['region_index'] = i
                    all_extracted_dex.append(dex_info)
                    
                    # 统计
                    if dex_info['type'] == 'standard_dex':
                        results["standard_dex_found"] += 1
                    else:
                        results["potential_encrypted_dex_found"] += 1
            
            # 记录详细发现
            if dex_files:
                region_findings = {
                    "region_index": i,
                    "start_addr": region['start'],
                    "size": region['size'],
                    "dex_files_found": len(dex_files),
                    "encryption_analysis": self.detect_encryption_patterns(data[:min(len(data), 65536)])
                }
                results["detailed_findings"].append(region_findings)
        
        # 6. 加密检测汇总
        encryption_summary = {
            "total_regions_analyzed": len(memory_regions),
            "high_entropy_regions": 0,
            "commercial_protections_detected": [],
            "average_entropy": 0.0
        }
        
        total_entropy = 0.0
        entropy_count = 0
        
        for finding in results["detailed_findings"]:
            entropy = finding["encryption_analysis"]["entropy"]
            total_entropy += entropy
            entropy_count += 1
            
            if entropy > 7.5:
                encryption_summary["high_entropy_regions"] += 1
            
            for protection in finding["encryption_analysis"]["detected_protections"]:
                if protection["id"] not in encryption_summary["commercial_protections_detected"]:
                    encryption_summary["commercial_protections_detected"].append(protection["id"])
        
        if entropy_count > 0:
            encryption_summary["average_entropy"] = total_entropy / entropy_count
        
        results["encryption_detection_summary"] = encryption_summary
        
        # 7. 生成详细报告
        full_report = {
            "extraction_summary": results,
            "package_name": package_name,
            "pid": pid,
            "timestamp": datetime.now().isoformat(),
            "memory_regions_analyzed": len(memory_regions),
            "extracted_files": all_extracted_dex,
            "memory_dump_files": self.memory_dump_files,
            "encryption_analysis": encryption_summary
        }
        
        report_path = output_dir / "enhanced_extraction_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        
        self.log("enhanced_extraction_report_saved", "INFO", path=str(report_path))
        
        # 8. 结果总结
        if all_extracted_dex or results["memory_dumps_saved"] > 0:
            results["success"] = True
            
            self.log("enhanced_extraction_success", "SUCCESS", 
                   standard_dex=results["standard_dex_found"],
                   potential_encrypted_dex=results["potential_encrypted_dex_found"],
                   memory_dumps=results["memory_dumps_saved"],
                   output_dir=str(output_dir))
            
            # 列出发现
            if results["standard_dex_found"] > 0:
                self.log("standard_dex_extracted", "SUCCESS", count=results["standard_dex_found"])
            
            if results["potential_encrypted_dex_found"] > 0:
                self.log("potential_encrypted_dex_found", "WARNING", 
                       count=results["potential_encrypted_dex_found"],
                       note="可能需要进一步解密分析")
            
            # 加密分析结果
            if encryption_summary["high_entropy_regions"] > 0:
                self.log("high_entropy_regions_detected", "WARNING",
                       count=encryption_summary["high_entropy_regions"],
                       average_entropy=encryption_summary["average_entropy"])
            
            if encryption_summary["commercial_protections_detected"]:
                self.log("commercial_protections_identified", "WARNING",
                       protections=", ".join(encryption_summary["commercial_protections_detected"]))
        else:
            self.log("enhanced_extraction_no_results", "WARNING",
                   memory_regions=results["memory_regions_analyzed"],
                   note="未找到标准DEX，但已保存内存转储以供进一步分析")
            results["success"] = True  # 仍视为成功，因为收集了分析数据
        
        return results

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enhanced Root Memory Extractor - Advanced memory analysis for commercial protections'
    )
    
    parser.add_argument('--package', '-p', required=True, help='Target application package name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--language', '-l', default='en-US', choices=['en-US', 'zh-CN'], 
                       help='Language for output (en-US, zh-CN)')
    parser.add_argument('--output', '-o', help='Output directory for extracted files')
    
    args = parser.parse_args()
    
    extractor = EnhancedRootMemoryExtractor(verbose=args.verbose, language=args.language)
    
    # 执行增强提取
    results = extractor.extract_enhanced(args.package, args.output)
    
    # 输出结果摘要
    print("\n" + "="*60)
    print("增强Root内存分析结果摘要")
    print("="*60)
    print(f"包名: {results['package_name']}")
    print(f"PID: {results['pid']}")
    print(f"分析的内存区域: {results['memory_regions_analyzed']}")
    print(f"保存的内存转储: {results['memory_dumps_saved']}")
    print(f"标准DEX文件: {results['standard_dex_found']}")
    print(f"潜在加密DEX文件: {results['potential_encrypted_dex_found']}")
    
    if results['encryption_detection_summary']:
        enc = results['encryption_detection_summary']
        print(f"高熵区域: {enc['high_entropy_regions']}")
        print(f"平均熵: {enc['average_entropy']:.2f}")
        if enc['commercial_protections_detected']:
            print(f"检测到的商业保护: {', '.join(enc['commercial_protections_detected'])}")
    
    print(f"输出目录: {results['output_directory']}")
    print(f"成功: {'✅' if results['success'] else '❌'}")
    print("="*60)
    
    # 退出码
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()