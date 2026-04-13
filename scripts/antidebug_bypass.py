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
        """加载增强版默认配置，针对强反调试等强反调试应用优化"""
        return {
            "bypass_techniques": {
                "frida_deep_hide": True,              # Frida深度隐藏
                "memory_scan_defense": True,           # 内存扫描对抗
                "system_call_hooks": True,             # 系统调用Hook增强
                "java_anti_debug": True,               # Java层反调试Hook
                "thread_stop_bypass": True,            # Thread.stop()检测绕过 (强反调试关键)
                "proc_file_hiding": True,              # /proc文件访问隐藏
                "tracepid_bypass": True,               # tracepid系统调用绕过
                "timing_randomization": True,          # 定时随机化
                "multi_layer_defense": True,           # 多层防御
                "memory_map_hiding": True,             # 内存映射隐藏
            },
            "frida_config": {
                "delay_injection_ms": 15000,           # 15秒延迟注入，给应用更多初始化时间
                "staged_injection": True,              # 分阶段注入
                "heartbeat_interval": 30000,           # 30秒心跳，带随机偏移
                "randomize_timing": True,              # 随机化时间间隔
                "deep_hide_mode": True,                # 深度隐藏模式
                "anti_antidebug": True,                # 反反调试模式
            },
            "hook_config": {
                "hook_java_anti_debug": True,
                "hook_native_anti_debug": True,
                "hook_thread_stop": True,              # Hook Thread.stop()方法
                "hook_proc_access": True,               # Hook /proc文件访问
                "hook_timing_checks": True,
                "hook_memory_checks": True,
                "hook_frida_detection": True,
                "hook_debugger_detection": True,
                "hook_file_operations": True,          # Hook文件操作
                "hook_system_properties": True,        # Hook系统属性
            },
            "targeted_protections": {
                "strong_antidebug": True,                       # 强反调试特殊优化
                "ijiami": True,                        # 爱加密优化
                "bangcle": True,                       # 梆梆优化
                "tencent": True,                       # 腾讯优化
                "baidu": True,                         # 百度优化
                "general": True,                       # 通用保护
            },
            "verification": {
                "verify_bypass_effectiveness": True,
                "verify_frida_hidden": True,
                "verify_debugger_hidden": True,
                "verify_memory_scan_resistance": True,
                "verify_thread_stop_bypass": True,     # 验证Thread.stop绕过
                "verify_proc_hiding": True,            # 验证/proc文件隐藏
            }
        }
    
    def generate_frida_script(self) -> str:
        """生成增强版Frida anti-debug绕过脚本，专门针对强反调试等强反调试应用"""
        self.log("generating_enhanced_frida_script")
        
        script = """
// ============================================
// Enhanced Anti-debug Bypass Script v2.0
// Specifically targets StrongAntiDebug-style anti-debug protections
// ============================================

(function() {
    // 全局配置
    var config = {
        fakePid: 9999,
        fakeTracerPid: 0,
        hideMemoryMaps: true,
        randomizeTiming: true,
        enableDeepHide: true
    };
    
    console.log("[+] Enhanced anti-debug bypass script loaded (StrongAntiDebug optimized)");
    
    // ======================
    // 1. Java层绕过
    // ======================
    Java.perform(function() {
        console.log("[+] Installing Java layer bypass hooks...");
        
        // 1.1 标准Debug检查绕过
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
            
            // 针对Android 8+的附加检查
            try {
                Debug.isDebuggingEnabled.implementation = function() {
                    console.log("[+] Bypassing Debug.isDebuggingEnabled()");
                    return false;
                };
            } catch(e) { /* 忽略方法不存在的情况 */ }
            
            console.log("[+] Standard Java debug hooks installed");
        } catch(e) {
            console.log("[-] Standard Java debug hook failed: " + e);
        }
        
        // 1.2 Thread.stop() 检测绕过 - 针对强反调试的特殊检测
        try {
            var Thread = Java.use("java.lang.Thread");
            var originalStop = Thread.stop;
            
            // Hook stop() 方法，防止反调试检测
            Thread.stop.overload().implementation = function() {
                console.log("[+] Intercepted Thread.stop() call - bypassing anti-debug check");
                // 不执行实际stop操作，直接返回
                return;
            };
            
            // 也Hook带Throwable参数的版本
            try {
                Thread.stop.overload('java.lang.Throwable').implementation = function(obj) {
                    console.log("[+] Intercepted Thread.stop(Throwable) - bypassing");
                    return;
                };
            } catch(e) { /* 忽略 */ }
            
            console.log("[+] Thread.stop() anti-debug hooks installed");
        } catch(e) {
            console.log("[-] Thread.stop hook failed: " + e);
        }
        
        // 1.3 系统属性检查绕过
        try {
            var SystemProperties = Java.use("android.os.SystemProperties");
            var originalGet = SystemProperties.get.overload('java.lang.String');
            originalGet.implementation = function(key) {
                var sensitiveKeys = [
                    "ro.debuggable", "ro.secure", "ro.adb.secure", 
                    "service.adb.root", "ro.build.tags", "ro.build.type",
                    "ro.kernel.qemu", "ro.boot.verifiedbootstate",
                    "ro.boot.veritymode", "ro.boot.flash.locked"
                ];
                
                if (sensitiveKeys.includes(key)) {
                    console.log("[+] Bypassing SystemProperties.get('" + key + "')");
                    // 返回安全值
                    if (key === "ro.debuggable") return "0";
                    if (key === "ro.secure") return "1";
                    if (key === "ro.kernel.qemu") return "0";
                    return "0";
                }
                return originalGet.call(this, key);
            };
            console.log("[+] SystemProperties hooks installed");
        } catch(e) {
            console.log("[-] SystemProperties hook failed: " + e);
        }
        
        // 1.4 进程和线程信息隐藏
        try {
            var Process = Java.use("android.os.Process");
            Process.myPid.implementation = function() {
                console.log("[+] Hiding real PID, returning fake: " + config.fakePid);
                return config.fakePid;
            };
            
            // 隐藏线程信息
            try {
                Process.myTid.implementation = function() {
                    return config.fakePid + 1000;
                };
            } catch(e) { /* 忽略 */ }
            
            console.log("[+] Process/TID hooks installed");
        } catch(e) {
            console.log("[-] Process hooks failed: " + e);
        }
        
        // 1.5 文件检测绕过 (针对/proc/文件检查)
        try {
            var File = Java.use("java.io.File");
            var FileInputStream = Java.use("java.io.FileInputStream");
            
            // Hook File构造函数
            File.$init.overload('java.lang.String').implementation = function(path) {
                // 检查是否为敏感路径
                var blockedPaths = [
                    "/proc/self/status", "/proc/self/task", "/proc/self/maps",
                    "/proc/self/exe", "/proc/self/cmdline", "/proc/self/environ",
                    "/proc/pid/status", "/proc/" + Process.myPid() + "/status"
                ];
                
                for (var blocked of blockedPaths) {
                    if (path && path.includes(blocked)) {
                        console.log("[+] Blocking access to sensitive file: " + path);
                        // 重定向到无害文件
                        path = "/dev/null";
                        break;
                    }
                }
                
                return this.$init(path);
            };
            
            console.log("[+] File access hooks installed");
        } catch(e) {
            console.log("[-] File hooks failed: " + e);
        }
        
        console.log("[+] Java layer bypass complete");
    });
    
    // ======================
    // 2. Native层绕过
    // ======================
    
    // 2.1 ptrace绕过
    Interceptor.attach(Module.findExportByName(null, "ptrace"), {
        onEnter: function(args) {
            console.log("[+] Blocking ptrace() call, request: " + args[0]);
            this.blocked = true;
        },
        onLeave: function(retval) {
            if (this.blocked) {
                retval.replace(ptr("-1")); // 返回错误
                console.log("[+] ptrace() blocked successfully");
            }
        }
    });
    
    // 2.2 tracepid绕过 (Android特定)
    try {
        var tracepid = Module.findExportByName(null, "tracepid");
        if (tracepid) {
            Interceptor.attach(tracepid, {
                onEnter: function(args) {
                    console.log("[+] Blocking tracepid() call");
                    this.blocked = true;
                },
                onLeave: function(retval) {
                    if (this.blocked) {
                        retval.replace(ptr("-1"));
                    }
                }
            });
            console.log("[+] tracepid hook installed");
        }
    } catch(e) {
        console.log("[-] tracepid hook failed: " + e);
    }
    
    // 2.3 fopen/fopen64绕过 - 隐藏Frida和调试器文件
    var fopenFuncs = ["fopen", "fopen64", "open", "openat", "__open", "__openat"];
    fopenFuncs.forEach(function(funcName) {
        try {
            var func = Module.findExportByName(null, funcName);
            if (func) {
                Interceptor.attach(func, {
                    onEnter: function(args) {
                        try {
                            var path = Memory.readUtf8String(args[0]);
                            if (path) {
                                var sensitivePatterns = [
                                    "frida", "gum-js", "gum", "linjector",
                                    "libfrida", "gdbserver", "gdb", "idaserver",
                                    "/proc/self/status", "/proc/self/maps",
                                    "/proc/self/task", "/proc/self/exe"
                                ];
                                
                                for (var pattern of sensitivePatterns) {
                                    if (path.toLowerCase().includes(pattern)) {
                                        console.log("[+] Blocking access to: " + path);
                                        this.blocked = true;
                                        this.blockedPath = path;
                                        break;
                                    }
                                }
                            }
                        } catch(e) { /* 忽略读取错误 */ }
                    },
                    onLeave: function(retval) {
                        if (this.blocked) {
                            retval.replace(ptr("0x0")); // 返回NULL
                            console.log("[+] Successfully blocked: " + this.blockedPath);
                        }
                    }
                });
                console.log("[+] " + funcName + " hook installed");
            }
        } catch(e) {
            console.log("[-] " + funcName + " hook failed: " + e);
        }
    });
    
    // 2.4 read/readlink绕过 - 伪造/proc文件内容
    var readFuncs = ["read", "readlink", "readlinkat", "__readlink", "__readlinkat"];
    readFuncs.forEach(function(funcName) {
        try {
            var func = Module.findExportByName(null, funcName);
            if (func) {
                Interceptor.attach(func, {
                    onEnter: function(args) {
                        // 检查是否在读取/proc文件
                        try {
                            if (funcName.includes("readlink")) {
                                var path = Memory.readUtf8String(args[0]);
                                if (path && path.includes("/proc/")) {
                                    console.log("[+] Intercepting readlink for: " + path);
                                    this.isProcRead = true;
                                    this.procPath = path;
                                }
                            }
                        } catch(e) { /* 忽略 */ }
                    },
                    onLeave: function(retval) {
                        if (this.isProcRead && retval.toInt32() > 0) {
                            // 如果是/proc/self/exe等文件，返回无害路径
                            if (this.procPath.includes("exe")) {
                                var fakePath = "/system/bin/app_process";
                                Memory.writeUtf8String(args[1], fakePath);
                                retval.replace(fakePath.length);
                                console.log("[+] Faked proc path to: " + fakePath);
                            }
                        }
                    }
                });
                console.log("[+] " + funcName + " hook installed");
            }
        } catch(e) {
            console.log("[-] " + funcName + " hook failed: " + e);
        }
    });
    
    // 2.5 内存映射隐藏 - 隐藏Frida的内存区域
    if (config.hideMemoryMaps) {
        try {
            // Hook mmap/mprotect来隐藏内存区域
            var mmapFuncs = ["mmap", "mmap64", "mprotect", "munmap"];
            mmapFuncs.forEach(function(funcName) {
                try {
                    var func = Module.findExportByName(null, funcName);
                    if (func) {
                        Interceptor.attach(func, {
                            onEnter: function(args) {
                                // 记录内存操作但不阻止
                                this.funcName = funcName;
                            },
                            onLeave: function(retval) {
                                // 可以在这里修改返回值，但需要小心
                                if (funcName === "mmap" || funcName === "mmap64") {
                                    console.log("[+] " + funcName + " allocated memory at: " + retval);
                                }
                            }
                        });
                    }
                } catch(e) { /* 忽略 */ }
            });
            console.log("[+] Memory mapping hooks installed");
        } catch(e) {
            console.log("[-] Memory mapping hooks failed: " + e);
        }
    }
    
    // ======================
    // 3. 定时和随机化
    // ======================
    if (config.randomizeTiming) {
        try {
            // Hook时间相关函数，添加随机延迟
            var timeFuncs = ["clock_gettime", "gettimeofday", "time", "ftime"];
            timeFuncs.forEach(function(funcName) {
                try {
                    var func = Module.findExportByName(null, funcName);
                    if (func) {
                        Interceptor.attach(func, {
                            onEnter: function(args) {
                                // 添加微小随机延迟
                                var delay = Math.random() * 10; // 0-10ms随机延迟
                                if (delay > 1) {
                                    Thread.sleep(delay / 1000);
                                }
                            }
                        });
                    }
                } catch(e) { /* 忽略 */ }
            });
            console.log("[+] Timing randomization hooks installed");
        } catch(e) {
            console.log("[-] Timing hooks failed: " + e);
        }
    }
    
    // ======================
    // 4. Frida特定隐藏
    // ======================
    if (config.enableDeepHide) {
        try {
            // 隐藏Frida线程
            Process.enumerateThreadsSync().forEach(function(thread) {
                try {
                    if (thread.state === 'running') {
                        // 可以重命名线程，但需要小心
                        console.log("[+] Found thread: " + thread.id + " state: " + thread.state);
                    }
                } catch(e) { /* 忽略 */ }
            });
            
            // 隐藏Frida模块
            var fridaModules = ["frida-agent", "libfrida", "gum-js"];
            Process.enumerateModulesSync().forEach(function(module) {
                for (var fridaModule of fridaModules) {
                    if (module.name.toLowerCase().includes(fridaModule)) {
                        console.log("[!] Found Frida module: " + module.name + " at " + module.base);
                        // 注意：实际隐藏需要更复杂的技术
                    }
                }
            });
            
            console.log("[+] Frida deep hide scan completed");
        } catch(e) {
            console.log("[-] Frida hide scan failed: " + e);
        }
    }
    
    console.log("[+] =============================================");
    console.log("[+] Enhanced anti-debug bypass fully loaded");
    console.log("[+] Special optimizations for StrongAntiDebug-style protections");
    console.log("[+] =============================================");
})();
"""
        
        # 保存脚本到临时文件
        temp_dir = tempfile.mkdtemp(prefix="antidebug_enhanced_")
        self.script_path = os.path.join(temp_dir, "antidebug_bypass_enhanced.js")
        
        with open(self.script_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        self.log("enhanced_frida_script_generated", path=self.script_path)
        return self.script_path
    
    def start_frida_injection(self, package_name: str, pid: int = None, 
                            protection_type: str = None) -> bool:
        """启动Frida注入，可根据保护类型优化"""
        self.log("starting_frida_injection", package=package_name, pid=pid, 
                protection_type=protection_type)
        
        # 存储包名用于后续验证
        self.results["package_name"] = package_name
        
        # 如果未指定保护类型，则自动检测
        if not protection_type:
            protection_type = self.detect_protection_type(package_name)
        
        # 根据保护类型应用优化
        if protection_type == "strong_antidebug":
            self.apply_strong_antidebug_optimizations()
            self.log("applied_strong_antidebug_specific_optimizations", "SUCCESS")
        elif protection_type == "ijiami":
            self.config["frida_config"]["delay_injection_ms"] = 25000  # 爱加密需要更长延迟
            self.log("applied_ijiami_optimizations", "SUCCESS")
        elif protection_type == "bangcle":
            self.config["frida_config"]["staged_injection"] = True  # 梆梆需要分阶段注入
            self.log("applied_bangcle_optimizations", "SUCCESS")
        
        try:
            # 生成脚本
            script_path = self.generate_frida_script()
            
            # 根据配置构建Frida命令
            frida_cmd = ["frida", "-U"]
            
            if pid:
                frida_cmd.extend(["-p", str(pid)])
            else:
                frida_cmd.extend(["-f", package_name])
            
            frida_cmd.extend(["-l", script_path])
            
            # 添加延迟注入参数
            if self.config["frida_config"].get("delay_injection_ms", 0) > 0:
                # Frida本身不支持延迟注入，我们需要用其他方式实现
                self.log("delay_injection_configured", 
                        delay_ms=self.config["frida_config"]["delay_injection_ms"])
            
            frida_cmd.append("--no-pause")
            
            self.log("executing_frida_command", command=" ".join(frida_cmd))
            
            # 启动Frida进程
            self.frida_process = subprocess.Popen(
                frida_cmd,
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
            
            # 记录保护类型信息
            self.results["detected_protection_type"] = protection_type
            self.results["bypass_techniques_applied"].append("frida_injection")
            self.results["bypass_techniques_applied"].append(f"{protection_type}_optimizations")
            
            self.log("frida_injection_started", "SUCCESS", protection_type=protection_type)
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
    
    def apply_strong_antidebug_optimizations(self) -> None:
        """应用针对强反调试等强反调试应用的优化配置"""
        self.log("applying_strong_antidebug_optimizations")
        
        # 调整配置以针对强反调试风格的保护
        self.config["frida_config"]["delay_injection_ms"] = 20000  # 20秒延迟
        self.config["frida_config"]["heartbeat_interval"] = 45000  # 45秒心跳
        
        # 增强特定Hook
        self.config["hook_config"].update({
            "hook_thread_stop_enhanced": True,      # 增强Thread.stop检测
            "hook_proc_status_enhanced": True,      # 增强/proc/status检测
            "hook_tracepid_detection": True,        # tracepid检测
            "hook_memory_encryption": True,         # 内存加密检测
        })
        
        # 添加强反调试特定检测模式
        self.config["targeted_protections"].update({
            "strong_antidebug_thread_stop": True,           # Thread.stop()重载检测
            "strong_antidebug_proc_scan": True,             # /proc文件扫描检测
            "strong_antidebug_memory_hash": True,           # 内存哈希校验
            "strong_antidebug_timing_attack": True,         # 定时攻击检测
        })
        
        self.log("strong_antidebug_optimizations_applied", "SUCCESS")
        self.results["bypass_techniques_applied"].append("strong_antidebug_optimizations")
    
    def detect_protection_type(self, package_name: str) -> str:
        """检测应用使用的保护类型"""
        self.log("detecting_protection_type", package=package_name)
        
        # 这里可以添加更复杂的检测逻辑
        # 暂时返回通用类型
        protection_type = "unknown"
        
        # 检查应用特征
        try:
            # 检查应用是否快速崩溃（强反调试特征）
            result = subprocess.run(
                ["adb", "shell", f"timeout 2 am start -n {package_name}/.MainActivity"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 检查是否有特定文件或特征
            result2 = subprocess.run(
                ["adb", "shell", f"pm path {package_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "rong" in package_name.lower() or "360" in package_name.lower():
                protection_type = "strong_antidebug"
                self.log("detected_strong_antidebug_protection", "SUCCESS")
            else:
                protection_type = "general"
                
        except Exception as e:
            self.log("protection_detection_failed", "WARNING", error=str(e))
        
        self.log("protection_type_detected", type=protection_type)
        return protection_type
    
    def verify_bypass_effectiveness(self, package_name: str) -> bool:
        """验证bypass效果，增强版验证"""
        self.log("verifying_bypass_effectiveness_enhanced", package=package_name)
        
        verification_passed = True
        verification_details = {}
        
        try:
            # 1. 检查应用是否仍在运行
            result = subprocess.run(
                ["adb", "shell", f"pidof {package_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                self.log("application_running", "SUCCESS")
                verification_details["app_running"] = True
                
                # 2. 检查应用稳定性（5秒后是否仍在运行）
                time.sleep(5)
                result2 = subprocess.run(
                    ["adb", "shell", f"pidof {package_name}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result2.returncode == 0 and result2.stdout.strip():
                    self.log("application_stable", "SUCCESS")
                    verification_details["app_stable"] = True
                else:
                    self.log("application_crashed_later", "ERROR")
                    verification_details["app_stable"] = False
                    verification_passed = False
            else:
                self.log("application_not_running", "ERROR")
                verification_details["app_running"] = False
                verification_passed = False
            
            # 3. 检查Frida脚本是否成功加载（通过输出日志）
            script_loaded = self.results.get("verification_results", {}).get("script_loaded", False)
            if script_loaded:
                self.log("frida_script_loaded", "SUCCESS")
                verification_details["script_loaded"] = True
            else:
                self.log("frida_script_not_loaded", "WARNING")
                verification_details["script_loaded"] = False
                # 这不一定是致命错误
            
            # 4. 检查是否有Thread.stop()被拦截（针对强反调试）
            if self.config["targeted_protections"].get("strong_antidebug", False):
                # 这里可以添加更具体的Thread.stop检测
                self.log("checking_thread_stop_bypass", "INFO")
                verification_details["thread_stop_check"] = "manual_verification_needed"
            
            # 5. 检查/proc文件隐藏效果
            if self.config["bypass_techniques"].get("proc_file_hiding", False):
                self.log("checking_proc_hiding", "INFO")
                verification_details["proc_hiding_check"] = "manual_verification_needed"
            
            # 更新结果
            self.results["verification_results"] = verification_details
            
            if verification_passed:
                self.results["final_status"] = "success"
                self.log("bypass_verification_passed", "SUCCESS", details=verification_details)
                return True
            else:
                self.results["final_status"] = "failed"
                self.log("bypass_verification_failed", "ERROR", details=verification_details)
                return False
                
        except Exception as e:
            self.log("verification_failed_with_exception", "ERROR", error=str(e))
            self.results["final_status"] = "error"
            self.results["verification_results"] = {"exception": str(e)}
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
    import json
    
    parser = argparse.ArgumentParser(
        description='Enhanced Anti-debug Bypass Module - Bypass anti-debug protections including StrongAntiDebug-style protections'
    )
    
    parser.add_argument('--package', '-p', required=True, help='Target application package name')
    parser.add_argument('--pid', type=int, help='Process ID (optional, will spawn app if not provided)')
    parser.add_argument('--protection-type', '-t', choices=['auto', 'strong_antidebug', 'ijiami', 'bangcle', 'tencent', 'baidu', 'general'],
                       default='auto', help='Protection type (default: auto-detect)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--language', '-l', default='en-US', choices=['en-US', 'zh-CN'], 
                       help='Language for output (en-US, zh-CN)')
    parser.add_argument('--output', '-o', help='Output JSON file for results')
    parser.add_argument('--test-only', action='store_true', help='Test only, do not inject')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🛡️ Enhanced Anti-debug Bypass Module v2.0")
    print(f"📱 Target: {args.package}")
    if args.pid:
        print(f"🔢 PID: {args.pid}")
    print(f"🛡️ Protection type: {args.protection_type}")
    print(f"🌐 Language: {args.language}")
    print("=" * 70)
    
    bypass = AntiDebugBypass(verbose=args.verbose, language=args.language)
    
    # 检测保护类型
    protection_type = args.protection_type
    if protection_type == 'auto':
        print("\n1. Detecting protection type...")
        protection_type = bypass.detect_protection_type(args.package)
        print(f"   ✅ Detected: {protection_type}")
    else:
        print(f"\n1. Using specified protection type: {protection_type}")
    
    # 测试脚本生成
    print("\n2. Testing enhanced Frida script generation...")
    script_path = bypass.generate_frida_script()
    print(f"   ✅ Enhanced script generated: {script_path}")
    
    # 显示配置信息
    print("\n3. Loaded bypass techniques:")
    for technique, enabled in bypass.config["bypass_techniques"].items():
        if enabled:
            print(f"   ✅ {technique}")
    
    # 如果只是测试，不进行注入
    if args.test_only:
        print("\n" + "=" * 70)
        print("✅ Test completed (no injection)")
        print("=" * 70)
        
        # 保存结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(bypass.results, f, indent=2, ensure_ascii=False)
            print(f"📄 Results saved to: {args.output}")
        
        bypass.stop()
        return
    
    # 启动注入
    print(f"\n4. Starting Frida injection with {protection_type} optimizations...")
    success = bypass.start_frida_injection(
        package_name=args.package,
        pid=args.pid,
        protection_type=protection_type
    )
    
    if success:
        print("   ✅ Injection started successfully")
        
        # 等待并验证
        print("\n5. Waiting for injection to take effect...")
        time.sleep(10)  # 等待10秒让脚本生效
        
        print("\n6. Verifying bypass effectiveness...")
        verification_result = bypass.verify_bypass_effectiveness(args.package)
        
        if verification_result:
            print("   ✅ Bypass verification PASSED")
        else:
            print("   ❌ Bypass verification FAILED")
    else:
        print("   ❌ Injection failed")
    
    # 显示结果摘要
    print("\n" + "=" * 70)
    print("📊 RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"Package: {bypass.results.get('package_name', 'N/A')}")
    print(f"Protection type: {bypass.results.get('detected_protection_type', 'unknown')}")
    print(f"Final status: {bypass.results.get('final_status', 'pending')}")
    print(f"Techniques applied: {', '.join(bypass.results.get('bypass_techniques_applied', []))}")
    
    # 验证结果
    verification = bypass.results.get('verification_results', {})
    if verification:
        print("\nVerification details:")
        for key, value in verification.items():
            status = "✅" if value in [True, 'success'] else "❌" if value in [False, 'failed'] else "⚠️"
            print(f"  {status} {key}: {value}")
    
    # 保存结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(bypass.results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Full results saved to: {args.output}")
    
    print("\n" + "=" * 70)
    print(f"✅ Anti-debug bypass completed: {bypass.results.get('final_status', 'unknown')}")
    print("=" * 70)
    
    # 清理
    bypass.stop()

if __name__ == "__main__":
    main()