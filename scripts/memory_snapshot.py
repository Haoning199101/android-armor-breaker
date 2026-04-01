#!/usr/bin/env python3
"""
Memory Snapshot Attacker - 针对快速崩溃应用的内存快照攻击
专门处理Bangcle等启动后立即崩溃的加固应用
"""

import os
import sys
import subprocess
import time
import tempfile
import struct
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# 国际化导入
from i18n_logger import get_logger

class MemorySnapshotAttacker:
    """内存快照攻击器 - 针对快速崩溃应用"""
    
    def __init__(self, verbose: bool = True, language: str = 'en-US'):
        """Initialize MemorySnapshotAttacker
        
        Args:
            verbose: Enable verbose logging
            language: Language code (en-US, zh-CN)
        """
        self.logger = get_logger(language=language, verbose=verbose, module="memory_snapshot")
        self.verbose = verbose
        self.package_name = ""
        self.pid = None
        self.output_dir = None
        self.snapshot_data = bytearray()
        self.crash_detected = False
        self.gdbserver_available = False
        
    def log(self, key: str, level: str = "INFO", **kwargs):
        """Log a message using internationalized logger"""
        self.logger.log(key, level, **kwargs)
    
    def check_gdbserver(self) -> bool:
        """检查gdbserver是否可用"""
        self.log("checking_gdbserver")
        
        try:
            # 检查设备上是否有gdbserver
            result = subprocess.run(
                ["adb", "shell", "which gdbserver"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "gdbserver" in result.stdout:
                self.log("gdbserver_available", "SUCCESS")
                self.gdbserver_available = True
                return True
            else:
                self.log("gdbserver_not_found", "WARNING")
                # 尝试检查是否有预装的gdbserver
                result2 = subprocess.run(
                    ["adb", "shell", "ls /system/bin/gdbserver 2>/dev/null || echo 'not_found'"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if "gdbserver" in result2.stdout:
                    self.log("system_gdbserver_found", "SUCCESS")
                    self.gdbserver_available = True
                    return True
                else:
                    self.log("no_gdbserver_available", "WARNING")
                    return False
                
        except Exception as e:
            self.log("check_gdbserver_failed", "ERROR", error=str(e))
            return False
    
    def check_root(self) -> bool:
        """检查root权限（备用方案）"""
        self.log("checking_root_for_fallback")
        
        try:
            result = subprocess.run(
                ["adb", "shell", "su -c 'echo root_ok'"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "root_ok" in result.stdout:
                self.log("root_available", "SUCCESS")
                return True
            else:
                self.log("no_root_access", "WARNING")
                return False
                
        except Exception as e:
            self.log("check_root_failed", "ERROR", error=str(e))
            return False
    
    def get_package_pid(self, package_name: str) -> Optional[int]:
        """获取应用进程PID"""
        self.log("getting_package_pid", package=package_name)
        
        try:
            result = subprocess.run(
                ["adb", "shell", f"pidof {package_name}"],
                capture_output=True,
                text=True,
                timeout=5
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
        """启动应用并监控崩溃"""
        self.log("starting_application_monitor", package=package_name)
        
        try:
            # 先停止应用
            subprocess.run(
                ["adb", "shell", f"am force-stop {package_name}"],
                capture_output=True,
                timeout=5
            )
            time.sleep(1)
            
            # 启动应用并监控
            start_time = time.time()
            result = subprocess.run(
                ["adb", "shell", f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.log("application_started", "SUCCESS")
                
                # 快速获取PID（应用可能很快崩溃）
                time.sleep(1)
                pid = self.get_package_pid(package_name)
                
                if pid:
                    # 监控应用是否快速崩溃
                    monitor_time = 5  # 监控5秒
                    for i in range(monitor_time):
                        current_pid = self.get_package_pid(package_name)
                        if not current_pid or current_pid != pid:
                            self.log("application_crashed_detected", "WARNING", elapsed=i+1)
                            self.crash_detected = True
                            return pid  # 返回崩溃前的PID
                        time.sleep(1)
                    
                    self.log("application_stable", "SUCCESS")
                    return pid
                else:
                    self.log("pid_not_found_after_start", "ERROR")
                    return None
            else:
                self.log("application_start_failed", "ERROR", error=result.stderr[:100])
                return None
                
        except Exception as e:
            self.log("application_start_exception", "ERROR", error=str(e))
            return None
    
    def attach_gdbserver(self, pid: int) -> bool:
        """附加gdbserver到进程"""
        self.log("attaching_gdbserver", pid=pid)
        
        if not self.gdbserver_available:
            self.log("gdbserver_not_available", "ERROR")
            return False
        
        try:
            # 在后台启动gdbserver
            gdbserver_cmd = f"gdbserver :1234 --attach {pid}"
            background_cmd = f"{gdbserver_cmd} > /dev/null 2>&1 &"
            
            result = subprocess.run(
                ["adb", "shell", background_cmd],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.log("gdbserver_started", "SUCCESS", pid=pid)
                time.sleep(2)  # 等待gdbserver启动
                return True
            else:
                self.log("gdbserver_start_failed", "ERROR", stderr=result.stderr[:200])
                return False
                
        except Exception as e:
            self.log("gdbserver_attach_exception", "ERROR", error=str(e))
            return False
    
    def capture_memory_via_gdbserver(self, pid: int) -> Optional[bytes]:
        """通过gdbserver捕获内存"""
        self.log("capturing_memory_via_gdbserver", pid=pid)
        
        try:
            # 这里需要实际实现gdbserver内存读取
            # 由于复杂度较高，先记录为待实现功能
            self.log("gdbserver_memory_capture_not_implemented", "WARNING",
                    message="gdbserver内存捕获功能待实现，使用root备用方案")
            
            # 使用root备用方案
            return self.capture_memory_via_root(pid)
            
        except Exception as e:
            self.log("gdbserver_capture_failed", "ERROR", error=str(e))
            return None
    
    def capture_memory_via_root(self, pid: int) -> Optional[bytes]:
        """通过root权限捕获内存（备用方案）"""
        self.log("capturing_memory_via_root", pid=pid)
        
        try:
            # 检查root权限
            if not self.check_root():
                self.log("root_required_for_memory_capture", "ERROR")
                return None
            
            # 读取内存映射
            maps_cmd = f"su -c 'cat /proc/{pid}/maps'"
            result = subprocess.run(
                ["adb", "shell", maps_cmd],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                self.log("unable_read_memory_maps", "ERROR", stderr=result.stderr[:200])
                return None
            
            maps_output = result.stdout
            lines = maps_output.strip().split('\n')
            self.log("memory_maps_found", count=len(lines))
            
            # 分析内存映射，找到可读区域
            memory_regions = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    addr_range = parts[0]
                    perms = parts[1]
                    
                    if 'r' in perms:  # 可读区域
                        start_str, end_str = addr_range.split('-')
                        start = int(start_str, 16)
                        end = int(end_str, 16)
                        size = end - start
                        
                        # 过滤合理的区域大小
                        if 1024 <= size <= 50 * 1024 * 1024:  # 1KB 到 50MB
                            memory_regions.append({
                                'start': start,
                                'end': end,
                                'size': size,
                                'perms': perms,
                                'line': line
                            })
            
            self.log("readable_regions_found", count=len(memory_regions))
            
            if not memory_regions:
                self.log("no_readable_regions", "ERROR")
                return None
            
            # 捕获内存数据
            all_data = bytearray()
            for i, region in enumerate(memory_regions[:15]):  # 最多捕获15个区域
                self.log("capturing_region", region_num=i+1, total=len(memory_regions),
                       start=f"0x{region['start']:x}", size=region['size'])
                
                # 使用dd命令读取内存
                start_dec = region['start']
                # 计算需要读取的块数（每块4KB）
                block_count = (region['size'] + 4095) // 4096
                
                dd_cmd = f"dd if=/proc/{pid}/mem bs=4096 skip={start_dec//4096} count={block_count} 2>/dev/null"
                root_cmd = f"su -c '{dd_cmd}'"
                
                result = subprocess.run(
                    ["adb", "shell", root_cmd],
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout:
                    data = result.stdout
                    # 裁剪到实际区域大小
                    if len(data) > region['size']:
                        data = data[:region['size']]
                    
                    all_data.extend(data)
                    self.log("region_captured", "SUCCESS", 
                           region_size=region['size'], captured=len(data))
                else:
                    self.log("region_capture_failed", "WARNING",
                           start=f"0x{region['start']:x}", error=result.stderr[:100] if result.stderr else "unknown")
            
            if all_data:
                self.log("memory_snapshot_captured", "SUCCESS", size=len(all_data))
                return bytes(all_data)
            else:
                self.log("no_memory_data_captured", "ERROR")
                return None
                
        except Exception as e:
            self.log("memory_capture_failed", "ERROR", error=str(e))
            return None
    
    def capture_memory_snapshot(self, pid: int) -> Optional[bytes]:
        """捕获内存快照 - 主函数"""
        self.log("capturing_memory_snapshot", pid=pid)
        
        # 优先使用gdbserver（如果可用）
        if self.gdbserver_available:
            self.log("using_gdbserver_for_capture", "INFO")
            snapshot = self.capture_memory_via_gdbserver(pid)
            if snapshot:
                return snapshot
            else:
                self.log("gdbserver_capture_failed_try_root", "WARNING")
        
        # 备用方案：使用root权限
        self.log("using_root_for_capture", "INFO")
        return self.capture_memory_via_root(pid)
    
    def search_dex_in_snapshot(self, snapshot_data: bytes) -> List[Dict]:
        """在快照数据中搜索DEX文件"""
        self.log("searching_dex_in_snapshot", size=len(snapshot_data))
        
        dex_files = []
        
        # 搜索DEX头部
        dex_magic = b'dex\n'
        search_limit = min(len(snapshot_data), 50 * 1024 * 1024)  # 最多搜索前50MB
        
        for offset in range(0, search_limit, 4):  # 更细粒度的搜索
            if offset + 4 <= len(snapshot_data) and snapshot_data[offset:offset+4] == dex_magic:
                self.log("dex_signature_found", offset=offset)
                
                # 尝试解析DEX头部
                if offset + 0x70 <= len(snapshot_data):
                    header_data = snapshot_data[offset:offset+0x70]
                    
                    # 验证DEX头部
                    try:
                        # 解析DEX文件大小（偏移量0x20）
                        if len(header_data) >= 0x24:
                            file_size = struct.unpack('<I', header_data[0x20:0x24])[0]
                            
                            # 检查合理的文件大小（1KB - 50MB）
                            if 1024 <= file_size <= 50 * 1024 * 1024:
                                dex_info = {
                                    'offset': offset,
                                    'file_size': file_size,
                                    'header_checksum': header_data[8:12].hex(),
                                    'signature': header_data[12:32].hex()[:16] + "...",
                                    'valid': True
                                }
                                
                                dex_files.append(dex_info)
                                self.log("valid_dex_found", "INFO", 
                                       offset=offset, file_size=file_size)
                    except Exception as e:
                        self.log("dex_header_parse_error", "WARNING", error=str(e))
        
        self.log("dex_search_complete", found=len(dex_files))
        return dex_files
    
    def extract_dex_from_snapshot(self, snapshot_data: bytes, dex_info: Dict, output_dir: Path) -> Optional[str]:
        """从快照数据中提取DEX文件"""
        try:
            offset = dex_info['offset']
            file_size = dex_info['file_size']
            
            # 检查是否有足够的数据
            if offset + file_size > len(snapshot_data):
                self.log("insufficient_data_for_dex", "WARNING", 
                       offset=offset, file_size=file_size, available=len(snapshot_data)-offset)
                return None
            
            # 提取DEX数据
            dex_data = snapshot_data[offset:offset+file_size]
            
            # 验证DEX魔数
            if dex_data[:4] != b'dex\n':
                self.log("invalid_dex_magic", "ERROR")
                return None
            
            # 生成文件名
            import hashlib
            dex_hash = hashlib.md5(dex_data).hexdigest()[:8]
            filename = f"dex_snapshot_{dex_info['offset']:08x}_{dex_hash}.dex"
            filepath = output_dir / filename
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(dex_data)
            
            self.log("dex_file_saved", "SUCCESS", 
                   filename=filename, size=len(dex_data), path=str(filepath))
            
            return str(filepath)
            
        except Exception as e:
            self.log("dex_extraction_failed", "ERROR", error=str(e))
            return None
    
    def attack(self, package_name: str, output_dir: str = None) -> bool:
        """主攻击函数"""
        self.log("starting_memory_snapshot_attack", package=package_name)
        self.package_name = package_name
        
        # 1. 检查gdbserver
        self.check_gdbserver()
        
        # 2. 启动应用并检测崩溃
        pid = self.start_application(package_name)
        if not pid:
            self.log("cannot_start_application", "ERROR")
            return False
        
        self.pid = pid
        
        # 3. 如果是崩溃应用，立即捕获内存
        if self.crash_detected:
            self.log("crash_detected_capturing_memory", "WARNING")
        else:
            self.log("application_stable_attempting_capture", "INFO")
        
        # 4. 捕获内存快照
        snapshot = self.capture_memory_snapshot(pid)
        if not snapshot:
            self.log("memory_capture_failed", "ERROR")
            return False
        
        self.snapshot_data = bytearray(snapshot)
        
        # 5. 准备输出目录
        if not output_dir:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_dir = Path.cwd() / f"{package_name}_snapshot_{timestamp}"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir
        
        # 6. 在快照中搜索DEX文件
        dex_files = self.search_dex_in_snapshot(snapshot)
        
        # 7. 提取DEX文件
        extracted_count = 0
        for i, dex_info in enumerate(dex_files):
            if dex_info.get('valid', False):
                dex_path = self.extract_dex_from_snapshot(snapshot, dex_info, output_dir)
                if dex_path:
                    dex_info['saved_path'] = dex_path
                    extracted_count += 1
        
        # 8. 生成报告
        report = {
            "package_name": package_name,
            "pid": pid,
            "crash_detected": self.crash_detected,
            "gdbserver_used": self.gdbserver_available,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "snapshot_size": len(snapshot),
            "dex_files_found": len(dex_files),
            "dex_files_extracted": extracted_count,
            "output_directory": str(output_dir)
        }
        
        report_path = output_dir / "snapshot_attack_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log("attack_report_saved", "INFO", path=str(report_path))
        
        # 9. 结果总结
        if extracted_count > 0:
            self.log("snapshot_attack_success", "SUCCESS", 
                   dex_count=extracted_count, output_dir=str(output_dir))
            return True
        else:
            self.log("no_dex_extracted", "WARNING",
                   snapshot_size=len(snapshot), dex_found=len(dex_files))
            return False

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Memory Snapshot Attacker - Capture memory from crashing applications'
    )
    
    parser.add_argument('--package', '-p', required=True, help='Target application package name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--language', '-l', default='en-US', choices=['en-US', 'zh-CN'], 
                       help='Language for output (en-US, zh-CN)')
    parser.add_argument('--output', '-o', help='Output directory for extracted DEX files')
    
    args = parser.parse_args()
    
    attacker = MemorySnapshotAttacker(verbose=args.verbose, language=args.language)
    
    # 执行攻击
    success = attacker.attack(args.package, args.output)
    
    # 退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()