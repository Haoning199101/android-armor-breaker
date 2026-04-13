#!/usr/bin/env python3
"""
Bangcle加固Bypass执行器 - 针对梆梆加固的快速崩溃应用
"""

import os
import sys
import time
import subprocess
import tempfile
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

# 国际化导入
from i18n_logger import get_logger

class BangcleBypassRunner:
    """Bangcle加固Bypass执行器"""
    
    def __init__(self, verbose: bool = True, language: str = 'en-US'):
        """Initialize BangcleBypassRunner
        
        Args:
            verbose: Enable verbose logging
            language: Language code (en-US, zh-CN)
        """
        self.logger = get_logger(language=language, verbose=verbose, module="bangcle_bypass_runner")
        self.verbose = verbose
        self.package_name = ""
        self.pid = None
        self.frida_process = None
        self.script_path = ""
        self.results = {
            "package_name": "",
            "start_time": datetime.now().isoformat(),
            "bypass_attempts": 0,
            "successful_bypass": False,
            "crash_detected": False,
            "final_status": "pending"
        }
        
    def log(self, key: str, level: str = "INFO", **kwargs):
        """Log a message using internationalized logger"""
        self.logger.log(key, level, **kwargs)
    
    def check_environment(self) -> bool:
        """检查运行环境"""
        self.log("checking_environment")
        
        # 检查Frida
        try:
            result = subprocess.run(["which", "frida"], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                self.log("frida_not_found", "ERROR")
                return False
            self.log("frida_found", path=result.stdout.strip())
        except Exception as e:
            self.log("check_frida_failed", "ERROR", error=str(e))
            return False
        
        # 检查ADB
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
            
            device_lines = [line for line in lines[1:] if line.strip() and 'device' in line]
            if not device_lines:
                self.log("no_online_devices", "ERROR")
                return False
            
            self.log("devices_found", count=len(device_lines))
            return True
            
        except Exception as e:
            self.log("check_adb_failed", "ERROR", error=str(e))
            return False
    
    def generate_bangcle_bypass_script(self) -> str:
        """生成Bangcle加固Bypass脚本"""
        self.log("generating_bangcle_bypass_script")
        
        script = """
// ============================================
// Bangcle Reinforcement Bypass Script
// ============================================

Java.perform(function() {
    console.log("[+] Bangcle bypass script loaded");
    
    // 1. Hook Bangcle加固检测点
    try {
        // 常见的Bangcle加固类
        var bangcleClasses = [
            "com.bangcle.protect",
            "com.bangcle.anti",
            "com.bangcle.security",
            "com.bangcle.protection",
            "com.bangcle.Protect",
            "com.bangcle.AntiDebug",
            "com.bangcle.DebugDetect",
            "com.bangcle.FridaDetect"
        ];
        
        for (var i = 0; i < bangcleClasses.length; i++) {
            try {
                var clazz = Java.use(bangcleClasses[i]);
                console.log("[+] Found Bangcle class: " + bangcleClasses[i]);
                
                // Hook所有方法
                var methods = clazz.class.getDeclaredMethods();
                for (var j = 0; j < methods.length; j++) {
                    var methodName = methods[j].getName();
                    if (methodName.includes("detect") || 
                        methodName.includes("check") || 
                        methodName.includes("isDebug") ||
                        methodName.includes("isFrida") ||
                        methodName.includes("isHook")) {
                        
                        try {
                            clazz[methodName].overload().implementation = function() {
                                console.log("[+] Bypassing Bangcle method: " + methodName);
                                return false; // 返回false表示未检测到
                            };
                            console.log("[+] Hooked Bangcle method: " + methodName);
                        } catch(e) {
                            // 忽略参数不匹配的方法
                        }
                    }
                }
            } catch(e) {
                // 类不存在，继续下一个
            }
        }
    } catch(e) {
        console.log("[-] Bangcle class hook failed: " + e);
    }
    
    // 2. Hook系统调试检测
    try {
        var Debug = Java.use("android.os.Debug");
        Debug.isDebuggerConnected.implementation = function() {
            console.log("[+] Bypassing Debug.isDebuggerConnected() for Bangcle");
            return false;
        };
        
        Debug.waitingForDebugger.implementation = function() {
            console.log("[+] Bypassing Debug.waitingForDebugger() for Bangcle");
            return false;
        };
        
        console.log("[+] System debug hooks installed for Bangcle");
    } catch(e) {
        console.log("[-] System debug hook failed: " + e);
    }
    
    // 3. Hook进程信息
    try {
        var Process = Java.use("android.os.Process");
        Process.myPid.implementation = function() {
            console.log("[+] Hiding real PID for Bangcle");
            return 12345; // 返回虚假PID
        };
        
        Process.myUid.implementation = function() {
            console.log("[+] Hiding real UID for Bangcle");
            return 1000; // 返回虚假UID
        };
        
        console.log("[+] Process hooks installed for Bangcle");
    } catch(e) {
        console.log("[-] Process hook failed: " + e);
    }
    
    // 4. Hook文件访问（防止Bangcle检测Frida文件）
    try {
        var File = Java.use("java.io.File");
        File.exists.implementation = function() {
            var path = this.getPath();
            if (path && (path.includes("frida") || 
                         path.includes("gum-js") || 
                         path.includes("libfrida") ||
                         path.includes("re.frida"))) {
                console.log("[+] Blocking Frida file detection: " + path);
                return false; // 文件不存在
            }
            return this.exists();
        };
        
        console.log("[+] File access hooks installed for Bangcle");
    } catch(e) {
        console.log("[-] File hook failed: " + e);
    }
});

// 5. Native层Hook
Interceptor.attach(Module.findExportByName(null, "ptrace"), {
    onEnter: function(args) {
        console.log("[+] Blocking ptrace() for Bangcle");
        this.blocked = true;
    },
    onLeave: function(retval) {
        if (this.blocked) {
            retval.replace(ptr("-1")); // 返回错误
        }
    }
});

// 6. 内存扫描检测绕过
Interceptor.attach(Module.findExportByName(null, "fopen"), {
    onEnter: function(args) {
        var path = Memory.readUtf8String(args[0]);
        if (path && (path.includes("/proc/") || 
                     path.includes("/maps") || 
                     path.includes("/status") ||
                     path.includes("/mem"))) {
            console.log("[+] Blocking memory scan: " + path);
            this.blocked = true;
        }
    },
    onLeave: function(retval) {
        if (this.blocked) {
            retval.replace(ptr("0x0")); // 返回NULL
        }
    }
});

console.log("[+] Bangcle bypass script fully loaded");
"""
        
        # 保存脚本到临时文件
        temp_dir = tempfile.mkdtemp(prefix="bangcle_bypass_")
        self.script_path = os.path.join(temp_dir, "bangcle_bypass.js")
        
        with open(self.script_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        self.log("bangcle_script_generated", path=self.script_path)
        return self.script_path
    
    def start_application(self, package_name: str) -> bool:
        """启动应用"""
        self.log("starting_application", package=package_name)
        
        try:
            # 先停止应用
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
                
                # 等待应用启动
                time.sleep(2)
                
                # 获取PID
                pid = self.get_package_pid(package_name)
                if pid:
                    self.pid = pid
                    self.log("pid_obtained", "SUCCESS", pid=pid)
                    return True
                else:
                    self.log("pid_not_found", "ERROR")
                    self.results["crash_detected"] = True
                    return False
            else:
                self.log("application_start_failed", "ERROR", error=result.stderr[:100])
                return False
                
        except Exception as e:
            self.log("application_start_exception", "ERROR", error=str(e))
            return False
    
    def get_package_pid(self, package_name: str) -> Optional[int]:
        """获取应用进程PID"""
        try:
            result = subprocess.run(
                ["adb", "shell", f"pidof {package_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
            else:
                return None
                
        except Exception as e:
            self.log("pid_lookup_failed", "ERROR", error=str(e))
            return None
    
    def inject_frida_script(self) -> bool:
        """注入Frida脚本"""
        self.log("injecting_frida_script")
        
        if not self.pid:
            self.log("no_pid_available", "ERROR")
            return False
        
        try:
            script_path = self.generate_bangcle_bypass_script()
            
            # 构建Frida命令
            cmd = ["frida", "-U", "-p", str(self.pid), "-l", script_path, "--no-pause"]
            
            self.log("executing_frida_command", command=" ".join(cmd))
            
            # 启动Frida进程
            self.frida_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动输出监控线程
            monitor_thread = threading.Thread(
                target=self.monitor_frida_output,
                args=(self.frida_process,)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
            
            self.log("frida_injection_started", "SUCCESS")
            self.results["bypass_attempts"] += 1
            return True
            
        except Exception as e:
            self.log("frida_injection_failed", "ERROR", error=str(e))
            return False
    
    def monitor_frida_output(self, process):
        """监控Frida输出"""
        try:
            for line in process.stdout:
                if line.strip():
                    self.log("frida_output", level="DEBUG", message=line.strip())
                    
                    # 检测成功消息
                    if "Bangcle bypass script fully loaded" in line:
                        self.log("bangcle_bypass_successful", "SUCCESS")
                        self.results["successful_bypass"] = True
                        self.results["final_status"] = "success"
                    
                    # 检测错误
                    if "Error:" in line or "Failed:" in line:
                        self.log("frida_error_detected", "WARNING", error=line.strip())
                        
        except Exception as e:
            self.log("frida_monitor_error", "ERROR", error=str(e))
    
    def verify_bypass(self) -> bool:
        """验证bypass效果"""
        self.log("verifying_bypass")
        
        if not self.pid:
            self.log("no_pid_for_verification", "ERROR")
            return False
        
        try:
            # 检查应用是否仍在运行
            time.sleep(3)  # 等待一段时间
            
            current_pid = self.get_package_pid(self.package_name)
            if current_pid and current_pid == self.pid:
                self.log("application_still_running", "SUCCESS")
                return True
            else:
                self.log("application_crashed_after_bypass", "ERROR")
                self.results["crash_detected"] = True
                self.results["final_status"] = "failed"
                return False
                
        except Exception as e:
            self.log("verification_failed", "ERROR", error=str(e))
            return False
    
    def stop(self):
        """停止bypass"""
        self.log("stopping_bangcle_bypass")
        
        if self.frida_process:
            self.frida_process.terminate()
            try:
                self.frida_process.wait(timeout=5)
                self.log("frida_process_stopped", "SUCCESS")
            except subprocess.TimeoutExpired:
                self.frida_process.kill()
                self.log("frida_process_killed", "WARNING")
        
        # 清理临时文件
        if self.script_path and os.path.exists(self.script_path):
            try:
                os.remove(self.script_path)
                script_dir = os.path.dirname(self.script_path)
                if os.path.exists(script_dir):
                    os.rmdir(script_dir)
                self.log("temp_files_cleaned", "SUCCESS")
            except Exception as e:
                self.log("cleanup_failed", "WARNING", error=str(e))
        
        self.log("bangcle_bypass_stopped", "SUCCESS")

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Bangcle Reinforcement Bypass Runner - Bypass Bangcle protection'
    )
    
    parser.add_argument('--package', '-p', required=True, help='Target application package name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--language', '-l', default='en-US', choices=['en-US', 'zh-CN'], 
                       help='Language for output (en-US, zh-CN)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔓 Bangcle Bypass Runner - Internationalized Version")
    print(f"📱 Target: {args.package}")
    print(f"🌐 Language: {args.language}")
    print("=" * 60)
    
    runner = BangcleBypassRunner(verbose=args.verbose, language=args.language)
    
    # Test environment check
    print("\n1. Testing environment check...")
    if runner.check_environment():
        print("   ✅ Environment check passed")
    else:
        print("   ❌ Environment check failed")
    
    # Test script generation
    print("\n2. Testing Bangcle bypass script generation...")
    script_path = runner.generate_bangcle_bypass_script()
    print(f"   ✅ Script generated: {script_path}")
    
    # Test logging
    print("\n3. Testing internationalized logging...")
    runner.log("test_message", "INFO", test="Bangcle bypass test")
    
    print("\n" + "=" * 60)
    print("✅ Internationalization test completed")
    print("=" * 60)
    
    # Cleanup
    runner.stop()

if __name__ == "__main__":
    main()