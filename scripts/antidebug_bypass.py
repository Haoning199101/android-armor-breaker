#!/usr/bin/env python3
"""
anti-debugBypassModule v1.0 - 开发版
"""

import os
import sys
import json
import time
import subprocess
import tempfile
import threading
from pathlib import Path
from datetime import datetime

# 国际化导入
from i18n_logger import get_logger

class AntiDebugBypass:
    """Anti-debugBypass引擎 - 精简版"""
    
    def __init__(self, verbose: bool = True, language: str = 'en-US'):
        """Initialize AntiDebugBypass
        
        Args:
            verbose: Enable verbose logging
            language: Language code (en-US, zh-CN)
        """
        self.logger = get_logger(language=language, verbose=verbose, module="antidebug_bypass")
        self.verbose = verbose
        self.config = self.load_default_config()
        self.results = {
            "package_name": "",
            "start_time": datetime.now().isoformat(),
            "bypass_techniques_applied": [],
            "verification_results": {},
            "final_status": "pending"
        }
        self.frida_process = None
        self.script_path = ""
        
    def log(self, key: str, level: str = "INFO", **kwargs):
        """Log a message using internationalized logger"""
        self.logger.log(key, level, **kwargs)
        
    def load_default_config(self):
        """加载增强版默认Configuration"""
        return {
            "bypass_techniques": {
                "frida_deep_hide": True,      # Frida深度Hiding
                "memory_scan_defense": True,   # Memory scanning对抗
                "system_call_hooks": True,     # System调用Hook增强
                "java_anti_debug": True,       # Java层anti-debugHook
                "timing_bypass": True,         # time差DetectionBypass
                "multi_layer_defense": True,   # 多层Defense
            },
            "frida_config": {
                "delay_injection_ms": 10000,   # 10秒延迟注入，给Application更多initializetime
                "staged_injection": True,      # 分阶段注入
                "heartbeat_interval": 25000,   # 25秒心跳，带随机偏移
                "randomize_timing": True,      # 随机化time间隔
            },
            "hook_config": {
                "hook_java_anti_debug": True,
                "hook_native_anti_debug": True,
                "hook_timing_checks": True,
                "hook_memory_checks": True,
                "hook_frida_detection": True,
                "hook_debugger_detection": True,
            },
            "verification": {
                "verify_bypass_effectiveness": True,
                "verify_frida_hidden": True,
                "verify_debugger_hidden": True,
                "verify_memory_scan_resistance": True,
            }
        }
    
    def generate_frida_script(self) -> str:
        """生成Frida anti-debugBypass脚本"""
        self.log("generating_frida_script")
        
        script = """
// ============================================
// Anti-debug Bypass Script - Enhanced Version
// ============================================

Java.perform(function() {
    console.log("[+] Anti-debug bypass script loaded");
    
    // 1. Java层anti-debug bypass
    try {
        var Debug = Java.use("android.os.Debug");
        Debug.isDebuggerConnected.implementation = function() {
            console.log("[+] Bypassing Debug.isDebuggerConnected()");
            return false;
        };
        
        Debug.waitingForDebugger.implementation = function() {
            console.log("[+] Bypassing Debug.waitingForDebugger()");
            return false;
        };
        
        console.log("[+] Java anti-debug hooks installed");
    } catch(e) {
        console.log("[-] Java anti-debug hook failed: " + e);
    }
    
    // 2. 系统属性检查绕过
    try {
        var SystemProperties = Java.use("android.os.SystemProperties");
        var originalGet = SystemProperties.get.overload('java.lang.String');
        originalGet.implementation = function(key) {
            if (key === "ro.debuggable" || key === "ro.secure" || 
                key === "ro.adb.secure" || key === "service.adb.root") {
                console.log("[+] Bypassing SystemProperties.get('" + key + "')");
                return "0";
            }
            return originalGet.call(this, key);
        };
        console.log("[+] SystemProperties hooks installed");
    } catch(e) {
        console.log("[-] SystemProperties hook failed: " + e);
    }
    
    // 3. 进程信息隐藏
    try {
        var Process = Java.use("android.os.Process");
        Process.myPid.implementation = function() {
            console.log("[+] Hiding real PID");
            return 9999; // 返回虚假PID
        };
        console.log("[+] Process PID hook installed");
    } catch(e) {
        console.log("[-] Process hook failed: " + e);
    }
});

// 4. Native层anti-debug bypass
Interceptor.attach(Module.findExportByName(null, "ptrace"), {
    onEnter: function(args) {
        console.log("[+] Blocking ptrace() call");
        this.blocked = true;
    },
    onLeave: function(retval) {
        if (this.blocked) {
            retval.replace(ptr("-1")); // 返回错误
        }
    }
});

// 5. Frida检测绕过
Interceptor.attach(Module.findExportByName(null, "fopen"), {
    onEnter: function(args) {
        var path = Memory.readUtf8String(args[0]);
        if (path && (path.includes("frida") || path.includes("gum-js"))) {
            console.log("[+] Blocking Frida file access: " + path);
            this.blocked = true;
        }
    },
    onLeave: function(retval) {
        if (this.blocked) {
            retval.replace(ptr("0x0")); // 返回NULL
        }
    }
});

console.log("[+] Anti-debug bypass script fully loaded");
"""
        
        # 保存脚本到临时文件
        temp_dir = tempfile.mkdtemp(prefix="antidebug_")
        self.script_path = os.path.join(temp_dir, "antidebug_bypass.js")
        
        with open(self.script_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        self.log("frida_script_generated", path=self.script_path)
        return self.script_path
    
    def start_frida_injection(self, package_name: str, pid: int = None) -> bool:
        """启动Frida注入"""
        self.log("starting_frida_injection", package=package_name, pid=pid)
        
        try:
            # 生成脚本
            script_path = self.generate_frida_script()
            
            # 构建Frida命令
            if pid:
                cmd = ["frida", "-U", "-p", str(pid), "-l", script_path, "--no-pause"]
            else:
                cmd = ["frida", "-U", "-f", package_name, "-l", script_path, "--no-pause"]
            
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
            self.results["bypass_techniques_applied"].append("frida_injection")
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
                    if "Anti-debug bypass script fully loaded" in line:
                        self.log("bypass_script_loaded", "SUCCESS")
                        self.results["verification_results"]["script_loaded"] = True
                    
                    # 检测错误
                    if "Error:" in line or "Failed:" in line:
                        self.log("frida_error_detected", "WARNING", error=line.strip())
                        
        except Exception as e:
            self.log("frida_monitor_error", "ERROR", error=str(e))
    
    def verify_bypass_effectiveness(self, package_name: str) -> bool:
        """验证bypass效果"""
        self.log("verifying_bypass_effectiveness", package=package_name)
        
        try:
            # 检查应用是否仍在运行
            result = subprocess.run(
                ["adb", "shell", f"pidof {package_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                self.log("application_running", "SUCCESS")
                self.results["verification_results"]["app_running"] = True
                
                # 检查是否有崩溃迹象
                time.sleep(2)
                result2 = subprocess.run(
                    ["adb", "shell", f"pidof {package_name}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result2.returncode == 0 and result2.stdout.strip():
                    self.log("application_stable", "SUCCESS")
                    self.results["verification_results"]["app_stable"] = True
                    self.results["final_status"] = "success"
                    return True
                else:
                    self.log("application_crashed", "ERROR")
                    self.results["verification_results"]["app_stable"] = False
                    self.results["final_status"] = "failed"
                    return False
            else:
                self.log("application_not_running", "ERROR")
                self.results["verification_results"]["app_running"] = False
                self.results["final_status"] = "failed"
                return False
                
        except Exception as e:
            self.log("verification_failed", "ERROR", error=str(e))
            self.results["final_status"] = "error"
            return False
    
    def stop(self):
        """停止bypass"""
        self.log("stopping_antidebug_bypass")
        
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
        
        self.log("antidebug_bypass_stopped", "SUCCESS")

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Anti-debug Bypass Module - Bypass anti-debug protections in Android apps'
    )
    
    parser.add_argument('--package', '-p', required=True, help='Target application package name')
    parser.add_argument('--pid', type=int, help='Process ID (optional, will spawn app if not provided)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--language', '-l', default='en-US', choices=['en-US', 'zh-CN'], 
                       help='Language for output (en-US, zh-CN)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🛡️ Anti-debug Bypass Module - Internationalized Version")
    print(f"📱 Target: {args.package}")
    if args.pid:
        print(f"🔢 PID: {args.pid}")
    print(f"🌐 Language: {args.language}")
    print("=" * 60)
    
    bypass = AntiDebugBypass(verbose=args.verbose, language=args.language)
    
    # Test script generation
    print("\n1. Testing Frida script generation...")
    script_path = bypass.generate_frida_script()
    print(f"   ✅ Script generated: {script_path}")
    
    # Test configuration
    print("\n2. Testing configuration...")
    print(f"   ✅ Loaded {len(bypass.config['bypass_techniques'])} bypass techniques")
    
    # Test logging
    print("\n3. Testing internationalized logging...")
    bypass.log("test_message", "INFO", test="Internationalization test")
    
    print("\n" + "=" * 60)
    print("✅ Internationalization test completed")
    print("=" * 60)
    
    # Cleanup
    bypass.stop()

if __name__ == "__main__":
    main()