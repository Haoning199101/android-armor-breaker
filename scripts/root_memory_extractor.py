#!/usr/bin/env python3
"""
Root Memory Extractor - Direct process memory reading via root permissions, bypassing commercial-grade reinforcement protections
Targets reinforcement solutions like IJIAMI, Bangcle, 360, Tencent that cannot be bypassed by Frida dynamic injection
"""

import os
import sys
import re
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

# 国际化导入
from i18n_logger import get_logger

class RootMemoryExtractor:
    """Root Memory Extractor - Static memory analysis solution that completely bypasses application-layer detection"""

    def __init__(self, verbose: bool = True, language: str = 'en-US'):
        """Initialize RootMemoryExtractor

        Args:
            verbose: Enable verbose logging
            language: Language code (en-US, zh-CN)
        """
        self.logger = get_logger(language=language, verbose=verbose, module="root_memory_extractor")
        self.verbose = verbose
        self.package_name = ""
        self.pid = None
        self.output_dir = None
        self.dex_regions = []  # Found DEX memory regions
        self.extracted_dex_files = []

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
        """获取进程PID(增强版:pidof失败时使用ps回退)"""
        self.log("getting_process_pid", package=package_name)

        try:
            # 策略1:使用pidof获取PID(最快)
            result = subprocess.run(
                ["adb", "shell", f"pidof {package_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                pid_str = result.stdout.strip()
                # pidof可能返回多个PID，取第一个
                if ' ' in pid_str:
                    pid_str = pid_str.split()[0]
                try:
                    pid = int(pid_str)
                    self.log("pid_found", "SUCCESS", pid=pid)
                    return pid
                except ValueError:
                    self.log("pidof_invalid_output", "WARNING", output=pid_str)
                    # 继续尝试其他策略

            # 策略2:pidof失败,使用ps -A | grep(兼容多进程/进程名隐藏)
            self.log("pidof_failed_trying_ps", "WARN")
            ps_result = subprocess.run(
                ["adb", "shell", f"ps -A | grep {package_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if ps_result.returncode == 0 and ps_result.stdout.strip():
                # 解析ps输出,格式如:USER PID PPID VSZ RSS WCHAN ADDR S NAME
                lines = ps_result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 9 and package_name in parts[-1]:
                        try:
                            pid = int(parts[1])
                            self.log("pid_found_via_ps", "SUCCESS", pid=pid)
                            return pid
                        except (ValueError, IndexError):
                            continue

            # 策略3:使用ps -A | grep -v grep(更精确)
            ps_result2 = subprocess.run(
                ["adb", "shell", f"ps -A | grep -v grep | grep {package_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if ps_result2.returncode == 0 and ps_result2.stdout.strip():
                lines = ps_result2.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 9:
                        try:
                            pid = int(parts[1])
                            self.log("pid_found_via_ps_grep", "SUCCESS", pid=pid)
                            return pid
                        except (ValueError, IndexError):
                            continue

            self.log("process_not_found", "ERROR")
            return None

        except Exception as e:
            self.log("pid_lookup_failed", "ERROR", error=str(e))
            return None

    def start_application(self, package_name: str) -> Optional[int]:
        """启动应用"""
        self.log("starting_app", package=package_name)

        try:
            # 先停止应用(确保干净启动)
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
            result = subprocess.run(cmd, capture_output=True, timeout=15)  # text=False for binary output

            if result.returncode != 0:
                self.log("read_maps_failed", "ERROR", stderr=result.stderr[:200] if result.stderr else '')
                return []

            memory_regions = []
            # 解码二进制输出，忽略编码错误
            stdout_text = result.stdout.decode('utf-8', errors='ignore')
            lines = stdout_text.strip().split('\n')

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
            # 注意:需要将地址转换为十进制
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

    def search_dex_in_memory(self, data: bytes, region_info: Dict) -> List[Dict]:
        """在内存数据中搜索DEX文件(增强版:支持模糊搜索加密DEX)"""
        self.log("searching_dex_in_memory", data_size=len(data))

        dex_files = []
        dex_magic = b'dex\n'  # DEX文件标准魔数
        dex_prefix = b'dex'    # DEX前缀(用于模糊搜索)

        # 使用滑动窗口搜索DEX文件头
        search_limit = min(len(data), 100 * 1024 * 1024)  # 最多搜索前100MB

        for offset in range(0, search_limit, 1):  # 逐字节搜索以提高命中率
            # 策略1:标准DEX魔数匹配
            if offset + 4 <= len(data) and data[offset:offset+4] == dex_magic:
                self.log("standard_dex_signature_found", offset=offset)
                dex_info = self._parse_dex_header(data, offset, region_info)
                if dex_info:
                    dex_files.append(dex_info)
                continue

            # 策略2:模糊搜索加密/变形DEX(搜索'dex'前缀)
            if offset + 3 <= len(data) and data[offset:offset+3] == dex_prefix:
                # 可能找到加密的DEX头,尝试多种可能性
                self.log("potential_encrypted_dex_found", offset=offset)

                # 尝试解析可能的DEX头部(假设加密是简单的字节变换)
                # 检查接下来的字节是否可能是版本号或合理值
                if offset + 8 <= len(data):
                    next_byte = data[offset+3]
                    # 允许的第四个字节:0x00-0xFF(任意值,因加密而异)
                    # 尝试解析文件大小字段(偏移量0x20)
                    if offset + 0x24 <= len(data):
                        try:
                            # 尝试读取文件大小字段(可能也被加密)
                            encrypted_size_bytes = data[offset+0x20:offset+0x24]
                            # 简单尝试:如果这四个字节看起来像是合理的大小(1KB-100MB)
                            # 使用启发式方法:检查是否不是全0或全0xFF
                            if encrypted_size_bytes != b'\x00\x00\x00\x00' and encrypted_size_bytes != b'\xff\xff\xff\xff':
                                # 尝试作为小端整数解析
                                possible_size = struct.unpack('<I', encrypted_size_bytes)[0]
                                if 1024 <= possible_size <= 200 * 1024 * 1024:  # 放宽上限
                                    # 创建候选DEX信息(标记为加密)
                                    dex_info = {
                                        'offset': offset,
                                        'file_size': possible_size,
                                        'start_addr': region_info['start'] + offset,
                                        'header_checksum': data[offset+8:offset+12].hex() if offset+12 <= len(data) else "",
                                        'signature': data[offset+12:offset+32].hex()[:16] + "..." if offset+32 <= len(data) else "",
                                        'region_info': region_info,
                                        'encrypted': True,
                                        'confidence': 0.5
                                    }
                                    dex_files.append(dex_info)
                                    self.log("potential_encrypted_dex_added", "INFO",
                                           offset=offset, size=possible_size)
                        except Exception as e:
                            pass  # 忽略解析错误

        self.log("dex_search_complete", found=len(dex_files))
        return dex_files

    def _parse_dex_header(self, data: bytes, offset: int, region_info: Dict) -> Optional[Dict]:
        """解析DEX头部信息"""
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
                            'encrypted': False,
                            'confidence': 1.0
                        }
                        self.log("valid_dex_found", "INFO", offset=offset, file_size=file_size)
                        return dex_info
            except Exception as e:
                self.log("dex_header_parse_error", "WARNING", error=str(e))
        return None

    def extract_dex_file(self, data: bytes, dex_info: Dict, output_dir: Path) -> Optional[str]:
        """提取并保存DEX文件"""
        try:
            offset = dex_info['offset']
            file_size = dex_info['file_size']

            # 检查是否有足够的数据
            if offset + file_size > len(data):
                self.log("insufficient_data_for_dex", "WARNING",
                       offset=offset, file_size=file_size, available=len(data)-offset)
                return None

            # 提取DEX数据
            dex_data = data[offset:offset+file_size]

            # 检查是否为加密DEX
            is_encrypted = dex_info.get('encrypted', False)
            
            # 验证DEX魔数（仅对非加密DEX）
            if not is_encrypted and dex_data[:4] != b'dex\n':
                self.log("invalid_dex_magic", "ERROR")
                return None
            
            # 生成文件名（加密DEX使用不同后缀）
            dex_hash = hex(hash(dex_data) & 0xFFFFFFFF)[2:].zfill(8)
            if is_encrypted:
                filename = f"encrypted_dex_{dex_info['start_addr']:08x}_{dex_hash}.bin"
                self.log("encrypted_dex_detected", "WARNING", offset=offset, size=file_size)
            else:
                filename = f"dex_{dex_info['start_addr']:08x}_{dex_hash}.dex"
            
            filepath = output_dir / filename

            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(dex_data)

            self.log("dex_file_saved", "SUCCESS",
                   filename=filename, size=len(dex_data), path=str(filepath), encrypted=is_encrypted)

            return str(filepath)

        except Exception as e:
            self.log("dex_extraction_failed", "ERROR", error=str(e))
            return None

    def extract(self, package_name: str, output_dir: str = None) -> bool:
        """主提取函数"""
        self.log("starting_root_extraction", package=package_name)
        self.package_name = package_name

        # 1. 检查root权限
        if not self.check_root():
            self.log("root_required", "ERROR")
            return False

        # 2. 获取或启动应用
        pid = self.get_package_pid(package_name)
        if not pid:
            pid = self.start_application(package_name)
            if not pid:
                self.log("cannot_start_application", "ERROR")
                return False

        self.pid = pid

        # 3. 准备输出目录
        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path.cwd() / f"{package_name}_root_extraction_{timestamp}"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir

        self.log("output_directory_ready", "INFO", path=str(output_dir))

        # 4. 读取内存映射
        memory_regions = self.read_process_maps(pid)
        if not memory_regions:
            self.log("no_memory_regions_found", "ERROR")
            return False

        # 5. 提取和分析内存区域
        all_extracted_dex = []
        total_regions = len(memory_regions)

        for i, region in enumerate(memory_regions[:50]):  # 最多处理50个区域
            self.log("processing_region", region_num=i+1, total=total_regions,
                   start=f"0x{region['start']:x}", size=region['size'])

            # 跳过太大的区域(>500MB)
            if region['size'] > 500 * 1024 * 1024:
                self.log("region_too_large", "WARNING", size=region['size'])
                continue

            # 提取内存数据
            data = self.extract_memory_region(pid, region['start'], region['size'])
            if not data:
                continue

            # 在数据中搜索DEX文件
            dex_files = self.search_dex_in_memory(data, region)

            # 提取找到的DEX文件
            for dex_info in dex_files:
                dex_path = self.extract_dex_file(data, dex_info, output_dir)
                if dex_path:
                    dex_info['saved_path'] = dex_path
                    dex_info['region_index'] = i
                    all_extracted_dex.append(dex_info)

        # 6. 生成报告
        report = {
            "package_name": package_name,
            "pid": pid,
            "timestamp": datetime.now().isoformat(),
            "memory_regions_analyzed": len(memory_regions),
            "dex_files_found": len(all_extracted_dex),
            "output_directory": str(output_dir),
            "extracted_dex_files": all_extracted_dex
        }

        report_path = output_dir / "extraction_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.log("extraction_report_saved", "INFO", path=str(report_path))

        # 7. 结果总结
        if all_extracted_dex:
            self.log("root_extraction_success", "SUCCESS",
                   dex_count=len(all_extracted_dex), output_dir=str(output_dir))

            # 列出提取的DEX文件
            for i, dex in enumerate(all_extracted_dex[:5]):
                self.log("extracted_dex_summary", "INFO",
                       index=i+1,
                       addr=f"0x{dex['start_addr']:x}",
                       size=dex['file_size'],
                       path=dex.get('saved_path', 'unknown'))

            if len(all_extracted_dex) > 5:
                self.log("more_dex_files_extracted", "INFO", extra_count=len(all_extracted_dex)-5)

            return True
        else:
            self.log("no_dex_files_extracted", "ERROR")
            return False

def main():
    """Main function for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Root Memory Extractor - Extract DEX files from process memory via root permissions'
    )

    parser.add_argument('--package', '-p', required=True, help='Target application package name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--language', '-l', default='en-US', choices=['en-US', 'zh-CN'],
                       help='Language for output (en-US, zh-CN)')
    parser.add_argument('--output', '-o', help='Output directory for extracted DEX files')

    args = parser.parse_args()

    extractor = RootMemoryExtractor(verbose=args.verbose, language=args.language)

    # 执行提取
    success = extractor.extract(args.package, args.output)

    # 退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()