#!/usr/bin/env python3
"""
针对新百度加固等商业加固方案，实现DEX文件的完整动态脱壳
"""

import os
import sys
import subprocess
import time
import re
import json
import hashlib
import struct
import zlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set

class EnhancedDexDumpRunner:
    """增强版脱壳执行器 - 针对新百度加固优化"""
    
    def __init__(self, verbose: bool = False, max_attempts: int = 3, deep_search: bool = False, 
                 bypass_antidebug: bool = False):
        self.verbose = verbose
        self.max_attempts = max_attempts  # 最大尝试次数
        self.deep_search = deep_search    # 是否启用深度搜索模式
        self.bypass_antidebug = bypass_antidebug  # 是否启用反调试绕过
        self.all_dex_files = []  # 收集所有DEX文件信息（去重）
        self.execution_log = []  # 执行日志
        self.start_time = None
        self.end_time = None
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.execution_log.append(log_entry)
        
        # 实时输出到控制台
        if level == "INFO":
            print(f"📝 {message}")
        elif level == "SUCCESS":
            print(f"✅ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "ERROR":
            print(f"❌ {message}")
        elif level == "DEBUG" and self.verbose:
            print(f"🔍 {message}")
        
        # 立即刷新输出缓冲区
        import sys
        sys.stdout.flush()
    
    def check_environment(self) -> bool:
        """检查运行环境"""
        self.log("检查运行环境...")
        
        # 检查frida-dexdump
        try:
            result = subprocess.run(["which", "frida-dexdump"], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                self.log("未找到 frida-dexdump 工具", "ERROR")
                self.log("请执行: pip install frida-dexdump", "WARNING")
                return False
            self.log(f"frida-dexdump 路径: {result.stdout.strip()}", "DEBUG")
        except Exception as e:
            self.log(f"检查frida-dexdump失败: {e}", "ERROR")
            return False
        
        # 检查ADB设备连接
        try:
            result = subprocess.run(["adb", "devices"], 
                                   capture_output=True, text=True, timeout=10)
            if "device" not in result.stdout:
                self.log("未找到已连接的Android设备", "ERROR")
                self.log("请确保: 1) USB调试已启用 2) 设备已授权", "WARNING")
                return False
            
            # 提取设备ID
            lines = result.stdout.strip().split('\n')
            device_id = None
            for line in lines[1:]:  # 跳过第一行标题
                if "device" in line:
                    device_id = line.split()[0]
                    break
            
            if device_id:
                self.log(f"找到设备: {device_id}", "SUCCESS")
            else:
                self.log("设备状态异常", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("ADB设备检查超时（10秒）", "ERROR")
            self.log("请检查USB连接和设备授权状态", "WARNING")
            return False
        except Exception as e:
            self.log(f"检查ADB设备失败: {e}", "ERROR")
            return False
        
        # 检查Frida服务
        try:
            result = subprocess.run(["frida-ps", "-U"], 
                                   capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.log("Frida服务可能未运行", "WARNING")
                self.log("请确保设备上已运行 frida-server (需要root权限)", "WARNING")
            else:
                self.log("Frida服务运行正常", "SUCCESS")
        except subprocess.TimeoutExpired:
            self.log("Frida服务检查超时", "WARNING")
        except Exception as e:
            self.log(f"检查Frida服务失败: {e}", "WARNING")
        
        return True
    
    def check_package_installed(self, package_name: str) -> bool:
        """检查应用是否已安装"""
        try:
            result = subprocess.run(
                ["adb", "shell", "pm", "list", "packages", package_name],
                capture_output=True, text=True, timeout=10
            )
            if package_name in result.stdout:
                self.log(f"应用 '{package_name}' 已安装", "SUCCESS")
                return True
            else:
                self.log(f"未找到应用 '{package_name}'", "ERROR")
                self.log("使用 'adb shell pm list packages' 查看所有已安装应用", "WARNING")
                return False
        except subprocess.TimeoutExpired:
            self.log(f"检查应用安装状态超时（10秒）", "ERROR")
            self.log("ADB连接可能不稳定或设备无响应", "WARNING")
            return False
        except Exception as e:
            self.log(f"检查应用安装状态失败: {e}", "ERROR")
            return False
    
    def start_application(self, package_name: str) -> bool:
        """启动应用 - 直接启动脱壳APP"""
        self.log(f"启动应用 '{package_name}'...")
        
        try:
            # 1. 获取应用主Activity - 使用更可靠的cmd package resolve-activity命令
            self.log("获取应用主Activity...")
            main_activity = None
            
            # 方法1: 使用cmd package resolve-activity（Android 7.0+）
            try:
                resolve_cmd = ["adb", "shell", "cmd", "package", "resolve-activity",
                             "--brief", "-c", "android.intent.category.LAUNCHER", package_name]
                result = subprocess.run(resolve_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        main_activity = lines[-1].strip()  # 最后一行是Activity
                        self.log(f"通过resolve-activity找到主Activity: {main_activity}", "DEBUG")
            except Exception as e:
                self.log(f"resolve-activity命令失败: {e}", "DEBUG")
            
            # 方法2: 如果方法1失败，使用dumpsys package（备用）
            if not main_activity:
                self.log("尝试使用dumpsys package获取Activity...", "DEBUG")
                activity_cmd = [
                    "adb", "shell", "dumpsys", "package", package_name,
                    "|", "grep", "-A5", "MAIN", "|", "grep", package_name
                ]
                result = subprocess.run(" ".join(activity_cmd), 
                                       shell=True, capture_output=True, text=True, timeout=10)
                
                for line in result.stdout.split('\n'):
                    if package_name in line and "android.intent.action.MAIN" in line:
                        parts = line.split()
                        if len(parts) > 1:
                            main_activity = parts[1].strip()
                            break
            
            # 方法3: 如果以上都失败，使用通用Activity名称
            if not main_activity:
                # 使用通用Activity名称
                main_activity = f"{package_name}/.MainActivity"
                self.log(f"使用默认Activity: {main_activity}", "WARNING")
            else:
                self.log(f"找到主Activity: {main_activity}", "DEBUG")
            
            # 2. 直接启动应用
            self.log("直接启动应用...")
            start_cmd = ["adb", "shell", "am", "start", "-n", main_activity]
            result = subprocess.run(start_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log(f"应用启动成功: {main_activity}", "SUCCESS")
                return True
            else:
                self.log(f"应用启动失败，返回码: {result.returncode}", "ERROR")
                self.log(f"启动输出: {result.stdout[:200]}...", "DEBUG")
                return False
            
        except Exception as e:
            self.log(f"启动应用过程中出错: {e}", "ERROR")
            return False
    
    def wait_for_application_load(self, wait_time: int = 30) -> bool:
        """等待应用加载"""
        self.log(f"等待应用加载 {wait_time} 秒...")
        
        for i in range(wait_time):
            if i % 5 == 0:  # 每5秒显示一次进度
                remaining = wait_time - i
                self.log(f"等待中... ({remaining}秒剩余)")
            time.sleep(1)
        
        self.log("应用加载等待完成", "SUCCESS")
        return True
    
    def parse_dexdump_output(self, line: str) -> Optional[Dict]:
        """解析frida-dexdump输出，提取DEX文件信息"""
        # 匹配模式: [+] DexMd5=..., SavePath=..., DexSize=...
        pattern = r'\[\+\] DexMd5=([0-9a-f]+),\s+SavePath=([^,]+),\s+DexSize=([0-9a-fx]+)'
        match = re.search(pattern, line)
        
        if match:
            dex_md5, save_path, dex_size = match.groups()
            
            # 转换十六进制大小为十进制字节数
            try:
                size_bytes = int(dex_size, 16)
                size_kb = size_bytes / 1024
                size_mb = size_kb / 1024
                
                dex_info = {
                    'md5': dex_md5,
                    'path': save_path,
                    'size_bytes': size_bytes,
                    'size_kb': round(size_kb, 1),
                    'size_mb': round(size_mb, 2) if size_mb >= 0.1 else 0.0,
                    'timestamp': datetime.now().isoformat()
                }
                
                return dex_info
            except ValueError:
                self.log(f"无法解析DEX大小: {dex_size}", "WARNING")
        
        return None
    
    def execute_single_dexdump(self, package_name: str, output_dir: str, attempt: int = 1) -> Tuple[bool, List[Dict]]:
        """执行单次frida-dexdump"""
        self.log(f"执行第 {attempt} 次脱壳尝试...")
        
        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 反调试绕过（如果启用）
        if self.bypass_antidebug:
            self.log("执行反调试绕过...", "INFO")
            try:
                # 导入反调试绕过模块
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from antidebug_bypass import AntiDebugBypass
                
                # 创建反调试绕过实例
                bypass = AntiDebugBypass(verbose=self.verbose)
                
                # 执行反调试绕过
                bypass_success = bypass.run_bypass(package_name)
                
                if bypass_success:
                    self.log("反调试绕过执行完成", "SUCCESS")
                    # 等待绕过生效
                    self.log("等待绕过生效（5秒）...")
                    time.sleep(5)
                else:
                    self.log("反调试绕过执行失败，但仍继续脱壳", "WARNING")
                    
            except ImportError as e:
                self.log(f"无法导入反调试绕过模块: {e}", "WARNING")
            except Exception as e:
                self.log(f"反调试绕过执行出错: {e}", "WARNING")
        
        # 构建命令
        cmd = [
            'frida-dexdump',
            '-U',
            '-f', package_name,
            '-o', str(output_path)
        ]
        
        # 添加深度搜索参数（如果启用）
        if self.deep_search:
            cmd.append('-d')
            self.log("启用深度搜索模式 (-d 参数)", "SUCCESS")
            self.log("深度搜索模式将进行更彻底的内存扫描，可能发现更多DEX文件", "INFO")
        
        self.log(f"执行命令: {' '.join(cmd)}", "DEBUG")
        
        dex_files = []
        
        try:
            # 使用subprocess.run，设置超时避免无限等待
            self.log("frida-dexdump 进程已启动，开始执行（超时180秒）...")
            
            # 记录开始时间
            start_time = time.time()
            timeout_seconds = 180
            
            # 执行命令并捕获输出
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout_seconds
            )
            
            # 解析输出
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                line = line.rstrip('\n')
                if not line:
                    continue
                
                # 解析DEX文件信息
                dex_info = self.parse_dexdump_output(line)
                if dex_info:
                    dex_files.append(dex_info)
                    # 显示发现的文件
                    size_str = f"{dex_info['size_kb']:.1f}KB"
                    if dex_info['size_mb'] >= 0.1:
                        size_str = f"{dex_info['size_mb']:.2f}MB"
                    
                    self.log(f"发现DEX文件: {Path(dex_info['path']).name} ({size_str})", "SUCCESS")
                
                # 显示进度信息
                elif "Searching..." in line:
                    self.log("正在搜索内存中的DEX文件...")
                elif "Successful found" in line:
                    # 提取找到的DEX数量
                    match = re.search(r'found (\d+) dex', line)
                    if match:
                        count = match.group(1)
                        self.log(f"找到 {count} 个DEX文件", "SUCCESS")
                elif "Starting dump" in line:
                    self.log("开始提取DEX文件...")
                elif "All done" in line:
                    self.log("DEX文件提取完成", "SUCCESS")
                elif "Error" in line or "ERROR" in line:
                    self.log(f"错误: {line}", "ERROR")
                elif self.verbose:
                    # 详细模式下显示所有输出
                    self.log(f"[dexdump] {line}", "DEBUG")
            
            # 检查返回码
            if result.returncode == 0:
                self.log(f"第 {attempt} 次脱壳执行成功", "SUCCESS")
                return True, dex_files
            else:
                self.log(f"第 {attempt} 次脱壳执行失败，返回码: {result.returncode}", "ERROR")
                return False, dex_files
                
        except Exception as e:
            self.log(f"执行frida-dexdump时发生异常: {e}", "ERROR")
            return False, dex_files
    
    def merge_dex_files(self, all_dex_lists: List[List[Dict]]) -> List[Dict]:
        """合并多次脱壳的结果，去重"""
        self.log("合并多次脱壳结果...")
        
        # 使用MD5作为唯一标识去重
        unique_dex_files = {}
        
        for dex_list in all_dex_lists:
            for dex_info in dex_list:
                md5 = dex_info['md5']
                if md5 not in unique_dex_files:
                    unique_dex_files[md5] = dex_info
                else:
                    # 如果已有相同MD5，保留路径更完整的
                    existing = unique_dex_files[md5]
                    if 'path' in dex_info and 'path' in existing:
                        if len(dex_info['path']) > len(existing['path']):
                            unique_dex_files[md5] = dex_info
        
        merged_list = list(unique_dex_files.values())
        self.log(f"合并后共 {len(merged_list)} 个唯一DEX文件", "SUCCESS")
        
        return merged_list
    
    def execute_multi_attempt_dexdump(self, package_name: str, output_dir: str) -> Tuple[bool, List[Dict]]:
        """执行多次脱壳尝试"""
        all_dex_lists = []
        
        for attempt in range(1, self.max_attempts + 1):
            self.log(f"\n{'='*40}")
            self.log(f"第 {attempt}/{self.max_attempts} 次脱壳尝试")
            self.log(f"{'='*40}")
            
            # 每次尝试前等待一段时间
            if attempt > 1:
                wait_time = 30 * attempt  # 递增等待时间
                self.log(f"等待 {wait_time} 秒后再次尝试...")
                time.sleep(wait_time)
                
                # 重新启动应用
                self.start_application(package_name)
            
            success, dex_files = self.execute_single_dexdump(package_name, output_dir, attempt)
            
            if success and dex_files:
                all_dex_lists.append(dex_files)
                self.log(f"第 {attempt} 次脱壳获得 {len(dex_files)} 个DEX文件")
            else:
                self.log(f"第 {attempt} 次脱壳未获得DEX文件", "WARNING")
        
        # 合并结果
        if all_dex_lists:
            merged_dex_files = self.merge_dex_files(all_dex_lists)
            return True, merged_dex_files
        else:
            return False, []
    

    

    
    def _get_expected_md5(self, dex_filename: str) -> Optional[str]:
        """从已收集的DEX文件信息中获取期望的MD5值"""
        for dex_info in self.all_dex_files:
            if Path(dex_info['path']).name == dex_filename:
                return dex_info['md5']
        return None
    
    def _verify_dex_complete(self, dex_path: Path, expected_md5: str = None) -> Dict:
        """
        完整的DEX文件验证
        包括CRC32、SHA-1、MD5和DEX结构验证
        """
        results = {
            'filename': dex_path.name,
            'is_valid': False,
            'checks': [],
            'file_size': 0,
            'actual_md5': None,
            'expected_md5': expected_md5,
            'md5_match': None,
            'magic': None,
            'version': None,
            'crc32_valid': None,
            'sha1_valid': None,
            'dex_structure_valid': None
        }
        
        try:
            # 读取整个文件
            with open(dex_path, 'rb') as f:
                data = f.read()
            
            results['file_size'] = len(data)
            
            # 检查1: 最小文件大小
            if len(data) >= 0x24:  # 至少需要36字节的DEX文件头
                results['checks'].append({'check': 'min_size', 'result': 'PASS', 'message': f"文件大小足够: {len(data)} 字节"})
            else:
                results['checks'].append({'check': 'min_size', 'result': 'FAIL', 'message': f"文件大小不足: {len(data)} 字节（需要至少36字节）"})
                return results
            
            # 检查2: DEX文件头魔数
            magic = data[0:4]
            results['magic'] = magic.hex()
            
            if magic in [b'dex\n', b'dey\n']:
                results['checks'].append({'check': 'magic', 'result': 'PASS', 'message': f"DEX文件头: {magic.decode('ascii', errors='replace')}"})
            else:
                results['checks'].append({'check': 'magic', 'result': 'FAIL', 'message': f"无效的DEX文件头: 0x{magic.hex()}"})
                return results
            
            # 检查3: 版本号
            if len(data) >= 8:
                version = data[4:8]
                results['version'] = version.decode('ascii', errors='replace')
                results['checks'].append({'check': 'version', 'result': 'INFO', 'message': f"DEX版本: {results['version']}"})
            
            # 检查4: CRC32校验（偏移0x8）
            if len(data) >= 12:
                # 提取文件头中的CRC32（小端序）
                expected_crc32 = struct.unpack('<I', data[8:12])[0]
                
                # 计算实际CRC32（从偏移0x12开始到文件末尾）
                # 注意：根据DEX格式规范，CRC32计算从文件头偏移0x12开始
                actual_crc32 = zlib.crc32(data[12:]) & 0xffffffff
                
                results['crc32_valid'] = expected_crc32 == actual_crc32
                if results['crc32_valid']:
                    results['checks'].append({'check': 'crc32', 'result': 'PASS', 'message': f"CRC32校验通过: 0x{expected_crc32:08x}"})
                else:
                    results['checks'].append({'check': 'crc32', 'result': 'FAIL', 'message': f"CRC32校验失败: 期望0x{expected_crc32:08x}, 实际0x{actual_crc32:08x}"})
            
            # 检查5: SHA-1签名验证（偏移0xC，20字节）
            if len(data) >= 32:
                # 提取文件头中的SHA-1（20字节）
                expected_sha1 = data[12:32]
                
                # 计算实际SHA-1（从偏移0x20开始到文件末尾）
                actual_sha1 = hashlib.sha1(data[32:]).digest()
                
                results['sha1_valid'] = expected_sha1 == actual_sha1
                if results['sha1_valid']:
                    results['checks'].append({'check': 'sha1', 'result': 'PASS', 'message': f"SHA-1签名验证通过"})
                else:
                    results['checks'].append({'check': 'sha1', 'result': 'FAIL', 'message': f"SHA-1签名验证失败"})
            
            # 检查6: 文件大小字段验证（偏移0x20）
            if len(data) >= 0x24:
                expected_size = struct.unpack('<I', data[0x20:0x24])[0]
                size_valid = expected_size == len(data)
                if size_valid:
                    results['checks'].append({'check': 'file_size_field', 'result': 'PASS', 'message': f"文件大小字段正确: {expected_size} 字节"})
                else:
                    results['checks'].append({'check': 'file_size_field', 'result': 'FAIL', 'message': f"文件大小字段不匹配: 期望{expected_size}, 实际{len(data)}"})
            
            # 检查7: MD5验证
            actual_md5 = hashlib.md5(data).hexdigest()
            results['actual_md5'] = actual_md5
            
            if expected_md5:
                results['md5_match'] = actual_md5.lower() == expected_md5.lower()
                if results['md5_match']:
                    results['checks'].append({'check': 'md5', 'result': 'PASS', 'message': f"MD5匹配: {actual_md5}"})
                else:
                    results['checks'].append({'check': 'md5', 'result': 'FAIL', 'message': f"MD5不匹配: 期望{expected_md5}, 实际{actual_md5}"})
            else:
                results['checks'].append({'check': 'md5', 'result': 'INFO', 'message': f"计算MD5: {actual_md5}"})
            
            # 检查8: DEX基本结构验证
            # 验证文件头中的各个偏移量是否在文件范围内
            dex_structure_ok = True
            dex_structure_messages = []
            
            if len(data) >= 0x70:  # 足够读取所有文件头信息
                # 读取各个表的大小和偏移
                try:
                    string_ids_size = struct.unpack('<I', data[0x38:0x3c])[0]
                    string_ids_off = struct.unpack('<I', data[0x3c:0x40])[0]
                    
                    type_ids_size = struct.unpack('<I', data[0x40:0x44])[0]
                    type_ids_off = struct.unpack('<I', data[0x44:0x48])[0]
                    
                    # 检查偏移是否在文件范围内
                    if string_ids_off + string_ids_size * 4 > len(data):
                        dex_structure_ok = False
                        dex_structure_messages.append(f"字符串表超出文件范围")
                    else:
                        dex_structure_messages.append(f"字符串表: {string_ids_size} 项")
                    
                    if type_ids_off + type_ids_size * 4 > len(data):
                        dex_structure_ok = False
                        dex_structure_messages.append(f"类型表超出文件范围")
                    else:
                        dex_structure_messages.append(f"类型表: {type_ids_size} 项")
                
                except struct.error:
                    dex_structure_ok = False
                    dex_structure_messages.append(f"无法解析DEX结构")
            
            results['dex_structure_valid'] = dex_structure_ok
            if dex_structure_ok:
                results['checks'].append({'check': 'dex_structure', 'result': 'PASS', 'message': f"DEX结构基本有效: {', '.join(dex_structure_messages)}"})
            else:
                results['checks'].append({'check': 'dex_structure', 'result': 'WARNING', 'message': f"DEX结构可能有问题: {', '.join(dex_structure_messages)}"})
            
            # 综合判断
            # 要求：魔数正确 + CRC32有效 + SHA-1有效（如果存在）
            all_passed = True
            for check in results['checks']:
                if check['result'] == 'FAIL':
                    all_passed = False
                    break
            
            results['is_valid'] = all_passed
            
            return results
            
        except Exception as e:
            results['checks'].append({'check': 'general', 'result': 'ERROR', 'message': f"验证过程中发生异常: {str(e)}"})
            return results
    
    def verify_dex_integrity(self, output_dir: str) -> Dict:
        """验证DEX文件完整性"""
        self.log("开始验证DEX文件完整性...")
        
        output_path = Path(output_dir)
        verification_results = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'details': []
        }
        
        # 查找所有.dex文件
        dex_files = list(output_path.glob("*.dex"))
        verification_results['total_files'] = len(dex_files)
        
        if not dex_files:
            self.log("未找到DEX文件", "WARNING")
            return verification_results
        
        self.log(f"找到 {len(dex_files)} 个DEX文件进行验证")
        
        # 特别检查动态加载的DEX（如baiduprotect*.dex）
        baidu_files = list(output_path.glob("baiduprotect*.dex"))
        if baidu_files:
            self.log(f"发现 {len(baidu_files)} 个百度保护相关DEX文件", "SUCCESS")
        
        for dex_file in dex_files:
            # 获取期望的MD5值（如果已记录）
            expected_md5 = self._get_expected_md5(dex_file.name)
            
            # 执行完整的DEX验证
            complete_validation = self._verify_dex_complete(dex_file, expected_md5)
            
            # 将完整验证结果转换为兼容格式
            file_info = {
                'filename': dex_file.name,
                'path': str(dex_file),
                'size_bytes': complete_validation['file_size'],
                'is_valid': complete_validation['is_valid'],
                'checks': complete_validation['checks'],
                'complete_validation': {
                    'magic': complete_validation['magic'],
                    'version': complete_validation['version'],
                    'crc32_valid': complete_validation['crc32_valid'],
                    'sha1_valid': complete_validation['sha1_valid'],
                    'dex_structure_valid': complete_validation['dex_structure_valid'],
                    'actual_md5': complete_validation['actual_md5'],
                    'expected_md5': complete_validation['expected_md5'],
                    'md5_match': complete_validation['md5_match']
                }
            }
            
            if complete_validation['is_valid']:
                verification_results['valid_files'] += 1
                
                # 检查是否有任何FAIL的验证项
                has_fail = any(check['result'] == 'FAIL' for check in complete_validation['checks'])
                has_critical_fail = any(check['result'] == 'FAIL' and check['check'] in ['crc32', 'sha1', 'md5'] for check in complete_validation['checks'])
                
                if has_critical_fail:
                    self.log(f"⚠️  {dex_file.name} - 关键校验失败", "WARNING")
                elif has_fail:
                    self.log(f"⚠️  {dex_file.name} - 部分验证失败", "WARNING")
                else:
                    self.log(f"✅ {dex_file.name} - 完整验证通过", "SUCCESS")
            else:
                verification_results['invalid_files'] += 1
                self.log(f"❌ {dex_file.name} - 验证未通过", "ERROR")
            
            verification_results['details'].append(file_info)
        
        # 总结 - 添加完整的验证统计
        success_rate = (verification_results['valid_files'] / verification_results['total_files'] * 100) if verification_results['total_files'] > 0 else 0
        
        # 计算详细验证统计
        crc32_passed = 0
        sha1_passed = 0
        md5_matched = 0
        structure_valid = 0
        
        for detail in verification_results['details']:
            if 'complete_validation' in detail:
                cv = detail['complete_validation']
                if cv.get('crc32_valid') is True:
                    crc32_passed += 1
                if cv.get('sha1_valid') is True:
                    sha1_passed += 1
                if cv.get('md5_match') is True:
                    md5_matched += 1
                if cv.get('dex_structure_valid') is True:
                    structure_valid += 1
        
        self.log(f"完整性验证完成: {verification_results['valid_files']}/{verification_results['total_files']} 个文件有效 ({success_rate:.1f}%)", "SUCCESS")
        self.log(f"📊 详细验证统计:", "INFO")
        self.log(f"  - CRC32校验通过: {crc32_passed}/{verification_results['total_files']}", "INFO")
        self.log(f"  - SHA-1签名通过: {sha1_passed}/{verification_results['total_files']}", "INFO")
        self.log(f"  - MD5匹配验证: {md5_matched}/{verification_results['total_files']}", "INFO")
        self.log(f"  - DEX结构有效: {structure_valid}/{verification_results['total_files']}", "INFO")
        
        return verification_results
    
    def generate_enhanced_report(self, package_name: str, output_dir: str, dex_files: List[Dict], verification_results: Dict) -> str:
        """生成增强版执行报告"""
        report_path = Path(output_dir) / "enhanced_dexdump_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 增强版脱壳报告\n\n")
            f.write("## 报告信息\n")
            f.write(f"- **目标应用**: {package_name}\n")
            f.write(f"- **输出目录**: {output_dir}\n")
            f.write(f"- **脱壳策略**: {self.max_attempts} 次尝试 + 功能触发\n")
            
            # 添加搜索模式信息
            if self.deep_search:
                f.write(f"- **搜索模式**: 深度搜索模式 (-d参数)\n")
                f.write(f"- **模式说明**: 针对新百度加固等强力保护，可突破26个DEX限制\n")
                f.write(f"- **成功案例**: com.example.app 从26个突破到53个DEX\n")
            else:
                f.write(f"- **搜索模式**: 普通搜索模式\n")
            
            f.write(f"- **开始时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **结束时间**: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            if self.start_time and self.end_time:
                duration = (self.end_time - self.start_time).total_seconds()
                f.write(f"- **执行耗时**: {duration:.1f} 秒\n")
            
            # DEX文件统计
            f.write("\n## DEX文件统计\n")
            f.write(f"- **提取文件数**: {len(dex_files)}\n")
            f.write(f"- **验证有效数**: {verification_results['valid_files']}\n")
            f.write(f"- **验证无效数**: {verification_results['invalid_files']}\n")
            
            # 文件大小分布
            if dex_files:
                total_size = sum(d['size_bytes'] for d in dex_files)
                avg_size = total_size / len(dex_files) if len(dex_files) > 0 else 0
                max_file = max(dex_files, key=lambda x: x['size_bytes']) if dex_files else None
                min_file = min(dex_files, key=lambda x: x['size_bytes']) if dex_files else None
                
                f.write(f"- **总大小**: {total_size/1024/1024:.2f} MB\n")
                f.write(f"- **平均大小**: {avg_size/1024:.2f} KB\n")
                if max_file:
                    f.write(f"- **最大文件**: {Path(max_file['path']).name} ({max_file['size_bytes']/1024/1024:.2f} MB)\n")
                if min_file:
                    f.write(f"- **最小文件**: {Path(min_file['path']).name} ({min_file['size_bytes']} 字节)\n")
            
            # 文件列表
            if dex_files:
                f.write("\n## 提取的DEX文件\n")
                f.write("| 文件名 | 大小 | MD5 | 状态 |\n")
                f.write("|--------|------|-----|------|\n")
                
                # 按文件名排序
                sorted_dex = sorted(dex_files, key=lambda x: Path(x['path']).name)
                
                for dex_info in sorted_dex:
                    filename = Path(dex_info['path']).name
                    size_str = f"{dex_info['size_kb']:.1f}KB"
                    if dex_info['size_mb'] >= 0.1:
                        size_str = f"{dex_info['size_mb']:.2f}MB"
                    
                    # 查找验证状态
                    status = "未知"
                    for detail in verification_results['details']:
                        if detail['filename'] == filename:
                            status = "有效" if detail['is_valid'] else "无效"
                            break
                    
                    f.write(f"| {filename} | {size_str} | {dex_info['md5']} | {status} |\n")
            
            # 验证详情
            f.write("\n## 完整性验证详情\n")
            
            # 添加完整验证统计摘要
            crc32_passed = 0
            sha1_passed = 0
            md5_matched = 0
            structure_valid = 0
            
            for detail in verification_results['details']:
                if 'complete_validation' in detail:
                    cv = detail['complete_validation']
                    if cv.get('crc32_valid') is True:
                        crc32_passed += 1
                    if cv.get('sha1_valid') is True:
                        sha1_passed += 1
                    if cv.get('md5_match') is True:
                        md5_matched += 1
                    if cv.get('dex_structure_valid') is True:
                        structure_valid += 1
            
            f.write("### 完整验证统计\n")
            f.write(f"- **CRC32校验通过**: {crc32_passed}/{verification_results['total_files']}\n")
            f.write(f"- **SHA-1签名通过**: {sha1_passed}/{verification_results['total_files']}\n")
            f.write(f"- **MD5匹配验证**: {md5_matched}/{verification_results['total_files']}\n")
            f.write(f"- **DEX结构有效**: {structure_valid}/{verification_results['total_files']}\n")
            
            # 各个文件验证详情
            for detail in verification_results['details']:
                f.write(f"\n### {detail['filename']}\n")
                f.write(f"- **文件大小**: {detail['size_bytes']} 字节\n")
                f.write(f"- **验证状态**: {'✅ 有效' if detail['is_valid'] else '❌ 无效'}\n")
                
                # 显示完整验证结果（如果有）
                if 'complete_validation' in detail:
                    cv = detail['complete_validation']
                    f.write("- **完整验证信息**:\n")
                    if cv.get('magic'):
                        f.write(f"  - DEX魔数: 0x{cv['magic']} ({bytes.fromhex(cv['magic']).decode('ascii', errors='replace')})\n")
                    if cv.get('version'):
                        f.write(f"  - DEX版本: {cv['version']}\n")
                    if cv.get('crc32_valid') is not None:
                        status = "✅ 通过" if cv['crc32_valid'] else "❌ 失败"
                        f.write(f"  - CRC32校验: {status}\n")
                    if cv.get('sha1_valid') is not None:
                        status = "✅ 通过" if cv['sha1_valid'] else "❌ 失败"
                        f.write(f"  - SHA-1签名: {status}\n")
                    if cv.get('dex_structure_valid') is not None:
                        status = "✅ 有效" if cv['dex_structure_valid'] else "⚠️ 可能有问题"
                        f.write(f"  - DEX结构: {status}\n")
                    if cv.get('actual_md5'):
                        f.write(f"  - 计算MD5: {cv['actual_md5']}\n")
                        if cv.get('expected_md5'):
                            status = "✅ 匹配" if cv.get('md5_match') else "❌ 不匹配"
                            f.write(f"  - MD5匹配: {status} (期望: {cv['expected_md5']})\n")
                
                f.write("- **检查项目**:\n")
                for check in detail['checks']:
                    status_emoji = "✅" if check['result'] == 'PASS' else "⚠️" if check['result'] == 'WARNING' else "ℹ️" if check['result'] == 'INFO' else "❌"
                    f.write(f"  - {status_emoji} {check['check']}: {check['message']}\n")
            
            # 执行日志
            f.write("\n## 执行日志\n")
            f.write("```\n")
            for log_entry in self.execution_log:
                f.write(f"{log_entry}\n")
            f.write("```\n")
        
        self.log(f"增强版报告已生成: {report_path}", "SUCCESS")
        return str(report_path)
    
    def run(self, package_name: str, output_dir: str) -> bool:
        """增强版脱壳主执行流程"""
        self.log("=" * 60)
        self.log("增强版脱壳执行器 - 基于文档描述的完整方案")
        self.log("针对新百度加固等商业加固优化")
        
        # 显示模式信息
        mode_info = "普通模式"
        if self.deep_search:
            mode_info = "深度搜索模式 (-d参数)"
            self.log(f"📊 模式: {mode_info} - 针对新百度加固等强力保护")
            self.log("💡 经验: 可突破26个DEX限制，完整获取53个DEX")
            self.log("💡 案例: com.example.app 从26个突破到53个DEX")
        else:
            self.log(f"📊 模式: {mode_info} - 普通商业加固")
        
        self.log("=" * 60)
        
        self.start_time = datetime.now()
        
        # 1. 环境检查
        if not self.check_environment():
            return False
        
        # 2. 检查应用是否安装
        if not self.check_package_installed(package_name):
            return False
        
        # 3. 启动应用
        self.log("启动应用...")
        if not self.start_application(package_name):
            self.log("应用启动可能有问题，但仍继续脱壳", "WARNING")
        
        # 4. 等待应用加载
        if not self.wait_for_application_load(wait_time=30):
            self.log("应用加载等待可能有问题，但仍继续脱壳", "WARNING")
        
        # 5. 执行Frida脱壳
        self.log("执行Frida脱壳...")
        self.log("💡 当前策略：专注Frida调试", "INFO")
        
        # Frida脱壳
        success, all_dex_files = self.execute_multi_attempt_dexdump(package_name, output_dir)
        
        # 如果Frida脱壳失败，直接返回失败
        if not success:
            self.log("Frida脱壳失败，专注Frida调试模式结束", "ERROR")
            self.log("失败分析:", "INFO")
            self.log("1. 检查应用是否正常运行且无强反调试", "INFO")
            self.log("2. 检查Frida-server是否正常运行且已隐藏特征", "INFO")
            self.log("3. 尝试不同的应用启动时机和注入策略", "INFO")
            self.log("4. 确认反调试绕过模块是否正确执行", "INFO")
            self.log("⚠️ 注意：当前模式专注Frida脱壳", "WARNING")
            return False
        
        # 6. 验证完整性
        verification_results = self.verify_dex_integrity(output_dir)
        
        self.end_time = datetime.now()
        
        # 7. 生成报告
        report_path = self.generate_enhanced_report(package_name, output_dir, all_dex_files, verification_results)
        
        # 8. 最终总结
        self.log("=" * 60)
        self.log("增强版脱壳任务完成!", "SUCCESS")
        self.log(f"- 提取DEX文件: {len(all_dex_files)} 个")
        self.log(f"- 有效DEX文件: {verification_results['valid_files']} 个")
        self.log(f"- 百度保护DEX: {len([f for f in all_dex_files if 'baiduprotect' in Path(f['path']).name.lower()])} 个")
        self.log(f"- 详细报告: {report_path}")
        
        # 脱壳结果总结
        actual_count = len(all_dex_files)
        self.log(f"- 动态获取: {actual_count} 个DEX文件")
        
        # 深度搜索模式结果评估
        if self.deep_search:
            if actual_count >= 53:
                self.log(f"✅ 深度搜索成功! 获得 {actual_count} 个DEX文件 (超过53个)", "SUCCESS")
                self.log(f"💡 说明: 已突破新百度加固的26个DEX限制", "INFO")
            elif actual_count >= 26:
                self.log(f"⚠️  深度搜索部分成功: 获得 {actual_count} 个DEX文件", "WARNING")
                self.log(f"💡 说明: 突破了普通模式限制，但可能仍有未发现的DEX", "INFO")
            else:
                self.log(f"❌ 深度搜索效果不佳: 仅获得 {actual_count} 个DEX文件", "ERROR")
                self.log(f"💡 建议: 尝试增加等待时间、多次尝试或检查反调试机制", "INFO")
        else:
            # 普通模式评估
            if actual_count >= 26:
                self.log(f"✅ 普通模式成功: 获得 {actual_count} 个DEX文件", "SUCCESS")
            elif actual_count >= 10:
                self.log(f"⚠️  普通模式部分成功: 获得 {actual_count} 个DEX文件", "WARNING")
                self.log(f"💡 建议: 如需更多DEX文件，请尝试 --deep-search 参数", "INFO")
            else:
                self.log(f"❌ 普通模式效果不佳: 仅获得 {actual_count} 个DEX文件", "ERROR")
                self.log(f"💡 建议: 请尝试 --deep-search 参数或检查环境配置", "INFO")
        
        self.log("=" * 60)
        
        return True

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='增强版脱壳执行器 - 针对新百度加固优化')
    parser.add_argument('--package', '-p', required=True, help='Android应用包名')
    parser.add_argument('--output', '-o', default='./enhanced_dex_output', help='输出目录 (默认: ./enhanced_dex_output)')
    parser.add_argument('--attempts', '-a', type=int, default=3, help='脱壳尝试次数 (默认: 3)')
    parser.add_argument('--deep-search', '-d', action='store_true', help='启用深度搜索模式 (针对新百度加固等强力保护)')
    parser.add_argument('--bypass-antidebug', '-b', action='store_true', help='启用反调试绕过（针对强力反调试保护）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出模式')
    
    args = parser.parse_args()
    
    runner = EnhancedDexDumpRunner(
        verbose=args.verbose, 
        max_attempts=args.attempts, 
        deep_search=args.deep_search,
        bypass_antidebug=args.bypass_antidebug
    )
    success = runner.run(args.package, args.output)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()