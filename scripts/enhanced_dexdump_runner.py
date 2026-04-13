#!/usr/bin/env python3
"""
Enhanced DexDump Runner - Actual Frida-based DEX unpacking implementation
修复版本：实际执行frida-dexdump脱壳
"""

import os
import sys
import subprocess
import time
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# 国际化导入
from i18n_logger import get_logger
from antidebug_bypass import AntiDebugBypass

class EnhancedDexDumpRunner:
    """Enhanced DexDump Runner - Actual implementation"""
    
    def __init__(self, verbose: bool = False, max_attempts: int = 3, deep_search: bool = False, 
                 bypass_antidebug: bool = False, language: str = 'en-US'):
        """Initialize EnhancedDexDumpRunner
        
        Args:
            verbose: Enable verbose logging
            max_attempts: Maximum number of attempts
            deep_search: Enable deep search mode
            bypass_antidebug: Enable anti-debug bypass
            language: Language code (en-US, zh-CN)
        """
        self.logger = get_logger(language=language, verbose=verbose, module="enhanced_dexdump_runner")
        self.verbose = verbose
        self.max_attempts = max_attempts
        self.deep_search = deep_search
        self.bypass_antidebug = bypass_antidebug
        self.output_dir = None
        self.extracted_dex_files = []
        self.antidebug_bypass_instance = None  # 存储反调试绕过实例
        
    def log(self, key: str, level: str = "INFO", **kwargs):
        """Log a message using internationalized logger"""
        self.logger.log(key, level, **kwargs)
    
    def check_environment(self) -> bool:
        """检查运行环境"""
        self.log("checking_environment")
        
        # 检查frida-dexdump
        try:
            result = subprocess.run(["which", "frida-dexdump"], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                self.log("frida_dexdump_not_found", "ERROR")
                self.log("install_frida_dexdump", "WARNING")
                return False
            self.log("frida_dexdump_found", path=result.stdout.strip())
        except Exception as e:
            self.log("check_frida_dexdump_failed", "ERROR", error=str(e))
            return False
        
        # 检查ADB设备连接
        try:
            result = subprocess.run(["adb", "devices"], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                self.log("adb_command_failed", "ERROR")
                return False
            
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                self.log("no_connected_devices", "ERROR")
                return False
            
            # 检查是否有设备在线
            device_lines = [line for line in lines[1:] if line.strip() and 'device' in line]
            if not device_lines:
                self.log("no_online_devices", "ERROR")
                self.log("enable_usb_debugging", "WARNING")
                return False
            
            self.log("devices_found", count=len(device_lines))
            return True
            
        except Exception as e:
            self.log("check_adb_failed", "ERROR", error=str(e))
            return False
    
    def get_package_pid(self, package_name: str) -> Optional[int]:
        """获取应用进程PID（修复多PID处理）"""
        self.log("getting_package_pid", package=package_name)
        
        try:
            result = subprocess.run(
                ["adb", "shell", f"pidof {package_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pid_str = result.stdout.strip()
                # pidof可能返回多个PID（如"25886 25909"），取第一个
                if ' ' in pid_str:
                    pid_str = pid_str.split()[0]
                
                try:
                    pid = int(pid_str)
                    self.log("pid_found", "SUCCESS", pid=pid, original_output=result.stdout.strip())
                    return pid
                except ValueError:
                    self.log("pidof_invalid_output", "WARNING", output=pid_str)
                    # 尝试使用ps命令回退
                    
            # pidof失败，尝试使用ps命令
            self.log("pidof_failed_trying_ps", "WARNING")
            ps_result = subprocess.run(
                ["adb", "shell", f"ps -A | grep {package_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if ps_result.returncode == 0 and ps_result.stdout.strip():
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
            
            self.log("process_not_found", "ERROR")
            return None
                
        except Exception as e:
            self.log("pid_lookup_failed", "ERROR", error=str(e))
            return None
    
    def start_application(self, package_name: str) -> Optional[int]:
        """启动应用"""
        self.log("starting_application", package=package_name)
        
        try:
            # 先停止应用（确保干净启动）
            subprocess.run(
                ["adb", "shell", f"am force-stop {package_name}"],
                capture_output=True,
                timeout=5
            )
            time.sleep(1)
            
            # 启动应用
            result = subprocess.run(
                ["adb", "shell", f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.log("application_started", "SUCCESS")
                
                # 等待应用完全启动
                time.sleep(3)
                
                # 获取PID
                return self.get_package_pid(package_name)
            else:
                self.log("application_start_failed", "ERROR", error=result.stderr[:100])
                return None
                
        except Exception as e:
            self.log("application_start_exception", "ERROR", error=str(e))
            return None
    
    def ensure_application_running(self, package_name: str) -> Optional[int]:
        """确保应用正在运行，返回PID"""
        pid = self.get_package_pid(package_name)
        if pid:
            return pid
        
        # 应用未运行，启动它
        self.log("application_not_running", "INFO")
        return self.start_application(package_name)
    
    def setup_frida_server(self) -> bool:
        """设置Frida服务器特征隐藏（历史成功策略）"""
        self.log("setting_up_frida_server", "INFO")
        
        try:
            # 1. 重命名frida-server（历史成功策略）
            original_server = "/data/local/tmp/frida-server-17.7.3-android-arm64"
            disguised_server = "/data/local/tmp/libcrypto.so"
            
            if os.path.exists(original_server):
                # 重命名frida-server
                subprocess.run(["adb", "shell", f"mv {original_server} {disguised_server}"], 
                              capture_output=True)
                self.log("frida_server_disguised", "INFO")
            
            # 2. 设置端口转发（使用非默认端口）
            subprocess.run(["adb", "forward", "tcp:28080", "tcp:28080"], 
                          capture_output=True)
            self.log("port_forwarding_set", "INFO", port="28080")
            
            # 3. 确保frida-dexdump使用正确的连接方式
            return True
            
        except Exception as e:
            self.log("frida_server_setup_failed", "ERROR", error=str(e))
            return False
    
    def execute_frida_dexdump(self, package_name: str, output_dir: str = None) -> bool:
        """执行frida-dexdump进行脱壳（使用历史成功策略）"""
        self.log("executing_frida_dexdump", package=package_name)
        
        # 1. 设置Frida服务器隐藏
        if not self.setup_frida_server():
            self.log("frida_server_setup_failed", "WARNING")
        
        # 2. 确保应用正在运行
        pid = self.ensure_application_running(package_name)
        if not pid:
            self.log("cannot_start_application", "ERROR")
            return False
        
        # 3. 准备输出目录（确保绝对路径）
        if not output_dir:
            output_dir = Path.cwd() / f"{package_name}_dex_output"
        else:
            output_dir = Path(output_dir)
        
        output_dir = output_dir.resolve()  # 转换为绝对路径
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir
        
        # 4. 构建frida-dexdump命令（使用attach模式，历史成功策略）
        cmd = ["frida-dexdump", "-U", "-p", str(pid)]
        
        # 添加深度搜索参数（如果启用）
        if self.deep_search:
            cmd.append("-d")
            self.log("deep_search_enabled", "INFO")
        
        # 切换到输出目录执行
        original_cwd = Path.cwd()
        try:
            os.chdir(output_dir)
            self.log("running_frida_dexdump", "INFO", cmd=" ".join(cmd), cwd=str(output_dir))
            
            # 执行frida-dexdump，设置超时为180秒
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            # 检查执行结果
            # 首先统计提取的DEX文件（无论返回码如何）
            # 使用递归查找，因为frida-dexdump可能在子目录中创建DEX文件
            dex_files = list(output_dir.rglob("*.dex"))
            dex_count = len(dex_files)
            
            # 记录查找结果
            if dex_count == 0:
                # 检查是否有子目录
                subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
                self.log("searching_for_dex", "INFO", 
                       output_dir=str(output_dir), subdir_count=len(subdirs))
                for subdir in subdirs[:3]:  # 只记录前3个子目录
                    self.log("found_subdirectory", "DEBUG", path=str(subdir))
            
            if dex_count > 0:
                self.log("frida_dexdump_success_with_dex", "SUCCESS", 
                       count=dex_count, output_dir=str(output_dir), returncode=result.returncode)
                
                # 记录DEX文件信息
                self.extracted_dex_files = []
                for i, dex_file in enumerate(dex_files):
                    size_bytes = dex_file.stat().st_size
                    size_kb = size_bytes / 1024
                    size_mb = size_kb / 1024
                    
                    dex_info = {
                        'index': i + 1,
                        'name': dex_file.name,
                        'path': str(dex_file),
                        'size_bytes': size_bytes,
                        'size_kb': round(size_kb, 1),
                        'size_mb': round(size_mb, 2)
                    }
                    self.extracted_dex_files.append(dex_info)
                    
                    # 只记录前5个文件的详细信息
                    if i < 5:
                        self.log("dex_file_extracted", "INFO", 
                               index=i+1, file=dex_file.name, size=f"{size_kb:.1f}KB")
                
                if dex_count > 5:
                    self.log("more_dex_files", "INFO", extra_count=dex_count-5)
                
                # 如果有DEX文件，即使returncode不为0也返回成功
                return True
            else:
                # 没有找到DEX文件，检查返回码
                if result.returncode == 0:
                    self.log("no_dex_files_found", "WARNING",
                           stdout_preview=result.stdout[:200] if result.stdout else '')
                    # 检查是否有其他输出
                    if result.stdout and "Successful found" in result.stdout:
                        self.log("found_dex_in_memory", "INFO", stdout_preview=result.stdout[:200])
                else:
                    self.log("frida_dexdump_failed_no_dex", "ERROR", 
                           returncode=result.returncode, 
                           stdout_preview=result.stdout[:300] if result.stdout else '',
                           stderr_preview=result.stderr[:500] if result.stderr else '')
                return False
                
        except subprocess.TimeoutExpired:
            self.log("frida_dexdump_timeout", "ERROR", timeout=180)
            return False
        except Exception as e:
            self.log("frida_dexdump_exception", "ERROR", error=str(e))
            return False
        finally:
            os.chdir(original_cwd)
    
    def run_antidebug_bypass(self, package_name: str) -> bool:
        """运行实际的反调试绕过（集成AntiDebugBypass模块）"""
        if not self.bypass_antidebug:
            self.log("antidebug_bypass_disabled", "INFO")
            return True
        
        self.log("starting_antidebug_bypass", "INFO", package=package_name)
        
        try:
            # 实例化反调试绕过引擎
            bypass = AntiDebugBypass(verbose=self.verbose, language=self.language)
            
            # 首先停止应用以确保干净状态
            subprocess.run(
                ["adb", "shell", f"am force-stop {package_name}"],
                capture_output=True,
                timeout=5
            )
            time.sleep(2)
            
            # 启动应用并注入反调试脚本
            self.log("starting_frida_injection", "INFO")
            
            # 尝试获取PID（如果应用已在运行）
            pid_result = subprocess.run(
                ["adb", "shell", f"pidof {package_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            pid = None
            if pid_result.returncode == 0 and pid_result.stdout.strip():
                pid_str = pid_result.stdout.strip()
                # pidof可能返回多个PID，取第一个
                if ' ' in pid_str:
                    pid_str = pid_str.split()[0]
                
                try:
                    pid = int(pid_str)
                    self.log("existing_pid_found", "INFO", pid=pid, original_output=pid_result.stdout.strip())
                except ValueError:
                    self.log("invalid_pid_format", "WARNING", output=pid_str)
                    # 使用get_package_pid方法作为回退
                    pid = self.get_package_pid(package_name)
            
            # 启动反调试注入
            injection_success = bypass.start_frida_injection(package_name, pid)
            if not injection_success:
                self.log("antidebug_injection_failed", "ERROR")
                return False
            
            # 等待注入生效并验证
            self.log("waiting_for_bypass_effect", "INFO")
            time.sleep(3)
            
            verification_success = bypass.verify_bypass_effectiveness(package_name)
            if not verification_success:
                self.log("bypass_verification_failed", "WARNING")
                # 仍然继续，可能部分绕过生效
            
            self.log("antidebug_bypass_completed", "SUCCESS")
            
            # 保存引用以便后续清理
            self.antidebug_bypass_instance = bypass
            return True
            
        except Exception as e:
            self.log("antidebug_bypass_failed", "ERROR", error=str(e))
            return False
    
    def unpack(self, package_name: str, output_dir: str = None) -> bool:
        """主脱壳函数"""
        self.log("starting_unpack_process", package=package_name)
        
        # 1. 检查环境
        if not self.check_environment():
            self.log("environment_check_failed", "ERROR")
            return False
        
        # 2. 运行反调试绕过（如果启用）
        if self.bypass_antidebug:
            if not self.run_antidebug_bypass(package_name):
                self.log("antidebug_bypass_failed_continue", "WARNING")
        
        # 3. 执行frida-dexdump脱壳
        success = False
        for attempt in range(1, self.max_attempts + 1):
            self.log("unpack_attempt", "INFO", attempt=attempt, max_attempts=self.max_attempts)
            
            success = self.execute_frida_dexdump(package_name, output_dir)
            if success:
                break
            else:
                if attempt < self.max_attempts:
                    self.log("retry_unpack", "WARNING", next_attempt=attempt+1)
                    time.sleep(2)  # 等待后重试
        
        # 4. 输出结果
        if success:
            self.log("unpack_success", "SUCCESS", 
                   dex_count=len(self.extracted_dex_files),
                   output_dir=str(self.output_dir))
            
            # 生成结果报告
            report = {
                "package_name": package_name,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "dex_count": len(self.extracted_dex_files),
                "output_dir": str(self.output_dir),
                "extracted_files": self.extracted_dex_files
            }
            
            # 保存报告
            if self.output_dir:
                report_path = self.output_dir / "unpack_report.json"
                with open(report_path, 'w') as f:
                    json.dump(report, f, indent=2)
                self.log("report_saved", "INFO", path=str(report_path))
            
            return True
        else:
            self.log("unpack_failed", "ERROR", 
                   attempts=self.max_attempts, package=package_name)
            return False

def main():
    """命令行入口 - 实际执行脱壳"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enhanced DexDump Runner - Actual Frida-based DEX unpacking'
    )
    
    parser.add_argument('--package', '-p', required=True, help='Target application package name')
    parser.add_argument('--output', '-o', help='Output directory for extracted DEX files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--language', '-l', default='en-US', choices=['en-US', 'zh-CN'], 
                       help='Language for output (en-US, zh-CN)')
    parser.add_argument('--deep-search', action='store_true', help='Enable deep search mode')
    parser.add_argument('--bypass-antidebug', action='store_true', help='Enable anti-debug bypass')
    parser.add_argument('--max-attempts', type=int, default=3, help='Maximum unpacking attempts')
    
    args = parser.parse_args()
    
    runner = EnhancedDexDumpRunner(
        verbose=args.verbose,
        language=args.language,
        deep_search=args.deep_search,
        bypass_antidebug=args.bypass_antidebug,
        max_attempts=args.max_attempts
    )
    
    # 执行脱壳
    success = runner.unpack(args.package, args.output)
    
    # 退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()