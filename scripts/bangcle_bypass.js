// Bangcle (梆梆) 加固专用反调试绕过脚本 v1.0
// 目标：对抗目标金融应用等使用 Bangcle 加固的应用
// 特性：多层 Hook、实时监控、自适应绕过

Java.perform(function() {
    console.log("[Bangcle-Bypass] 🛡️ 初始化梆梆加固专用绕过脚本");
    console.log("[Bangcle-Bypass] 📅 生成时间: " + new Date().toISOString());
    
    // 全局状态跟踪
    var bypassState = {
        initialized: false,
        layersApplied: 0,
        detectionsBlocked: 0,
        nativeHooks: {},
        javaHooks: {},
        startTime: Date.now(),
        packageName: "",
        libsFound: []
    };
    
    // 发送状态更新
    function sendUpdate(message, data) {
        var update = {
            type: "bangcle_bypass_update",
            timestamp: new Date().toISOString(),
            message: message,
            data: data || {},
            state: bypassState
        };
        send(update);
    }
    
    // 记录检测事件
    function logDetection(source, method, action) {
        var event = {
            time: new Date().toISOString(),
            source: source,
            method: method,
            action: action,
            blocked: bypassState.detectionsBlocked
        };
        console.log("[Detection] " + source + "." + method + " -> " + action);
        bypassState.detectionsBlocked++;
    }
    
    // ==================== 第1层: BANGCLE 专用检测 Hook ====================
    
    function applyBangcleSpecificHooks() {
        console.log("[Bangcle-Bypass] 🔍 应用梆梆专用检测 Hook...");
        
        // 查找 Bangcle 关键库
        var targetLibs = ["libDexHelper.so", "libdexjni.so", "libbangcle.so", "libsecshell.so"];
        
        targetLibs.forEach(function(libName) {
            var libBase = Module.findBaseAddress(libName);
            if (libBase) {
                console.log("[+] 发现 Bangcle 库: " + libName + " @ " + libBase);
                bypassState.libsFound.push(libName);
                
                // 枚举库中所有导出函数
                try {
                    var exports = Module.enumerateExports(libName);
                    exports.forEach(function(exp) {
                        var expName = exp.name.toLowerCase();
                        
                        // 匹配反调试相关函数
                        var debugPatterns = [
                            "anti", "debug", "detect", "check", "protect",
                            "security", "safe", "shield", "guard", "verify"
                        ];
                        
                        var isDebugFunc = debugPatterns.some(function(pattern) {
                            return expName.includes(pattern);
                        });
                        
                        if (isDebugFunc) {
                            console.log("[Hook] 拦截 Bangcle 函数: " + exp.name + " @ " + exp.address);
                            
                            Interceptor.attach(exp.address, {
                                onEnter: function(args) {
                                    this.funcName = exp.name;
                                    logDetection(libName, exp.name, "调用拦截");
                                },
                                onLeave: function(retval) {
                                    // 强制返回安全状态
                                    if (!retval.isNull()) {
                                        // 根据不同返回类型处理
                                        if (retval.toInt32) {
                                            var intVal = retval.toInt32();
                                            if (intVal !== 0) { // 0 通常表示成功/安全
                                                console.log("[Bypass] 修改返回值: " + exp.name + " (" + intVal + " -> 0)");
                                                retval.replace(ptr(0));
                                            }
                                        }
                                    }
                                }
                            });
                            
                            bypassState.nativeHooks[exp.name] = {
                                library: libName,
                                address: exp.address,
                                hooked: true
                            };
                        }
                    });
                } catch(e) {
                    console.log("[-] 枚举导出函数失败: " + e);
                }
            }
        });
        
        // Hook 系统调用 - Bangcle 可能使用的检测方法
        var syscalls = ["ptrace", "open", "openat", "read", "write", "fopen", "fopen64"];
        
        syscalls.forEach(function(syscall) {
            var syscallAddr = Module.findExportByName(null, syscall);
            if (syscallAddr) {
                Interceptor.attach(syscallAddr, {
                    onEnter: function(args) {
                        this.syscall = syscall;
                        
                        // 检查是否是敏感文件访问
                        if (syscall.includes("open")) {
                            var filename = args[0];
                            if (!filename.isNull()) {
                                try {
                                    var path = Memory.readUtf8String(filename);
                                    if (path) {
                                        // 检测 /proc/self/ 访问
                                        if (path.includes("/proc/self/")) {
                                            logDetection("syscall", syscall, "拦截 /proc 访问: " + path);
                                            this.shouldBlock = true;
                                        }
                                        // 检测 frida 相关文件
                                        if (path.includes("frida") || path.includes("gadget")) {
                                            logDetection("syscall", syscall, "拦截 Frida 文件访问: " + path);
                                            this.shouldBlock = true;
                                        }
                                    }
                                } catch(e) {}
                            }
                        }
                        
                        // ptrace 检测
                        if (syscall === "ptrace") {
                            var request = args[0].toInt32();
                            if (request === 0) { // PTRACE_TRACEME
                                logDetection("syscall", "ptrace", "拦截 PTRACE_TRACEME");
                                this.shouldBlock = true;
                            }
                        }
                    },
                    onLeave: function(retval) {
                        if (this.shouldBlock) {
                            // 返回错误或空指针
                            retval.replace(ptr(-1));
                            console.log("[Bypass] 阻止系统调用: " + this.syscall);
                        }
                    }
                });
                
                bypassState.nativeHooks[syscall] = { hooked: true };
            }
        });
        
        bypassState.layersApplied++;
        console.log("[Bangcle-Bypass] ✅ 第1层: Bangcle 专用 Hook 应用完成");
    }
    
    // ==================== 第2层: JAVA 层检测绕过 ====================
    
    function applyJavaLayerHooks() {
        console.log("[Bangcle-Bypass] ☕ 应用 Java 层检测绕过...");
        
        // 常见 Bangcle Java 类 (根据版本不同可能变化)
        var bangcleJavaClasses = [
            "com.bangcle.protect.NativeProtect",
            "com.bangcle.anti.AntiDebug",
            "com.secshell.ndk.NDKHelper",
            "com.secshell.secure.SecurityCheck",
            "com.bangcle.security.AntiDebugger",
            "com.bangcle.dex.DexProtect",
            "cn.bangcle.protect.ProtectionManager"
        ];
        
        // 通用检测方法模式
        var detectionMethods = [
            "isDebug", "checkDebug", "detectDebug", "antiDebug",
            "isRoot", "checkRoot", "detectRoot", "antiRoot",
            "isHook", "checkHook", "detectHook", "antiHook",
            "isTamper", "checkTamper", "detectTamper", "verifySignature",
            "isEmulator", "checkEmulator", "detectEmulator"
        ];
        
        bangcleJavaClasses.forEach(function(className) {
            try {
                var targetClass = Java.use(className);
                console.log("[+] 发现 Bangcle Java 类: " + className);
                
                // 获取所有方法
                var methods = targetClass.class.getDeclaredMethods();
                for (var i = 0; i < methods.length; i++) {
                    var method = methods[i];
                    var methodName = method.getName();
                    
                    // 检查是否检测方法
                    var isDetectionMethod = detectionMethods.some(function(pattern) {
                        return methodName.toLowerCase().includes(pattern.toLowerCase());
                    });
                    
                    if (isDetectionMethod) {
                        try {
                            // Hook 方法
                            targetClass[methodName].implementation = function() {
                                logDetection("Java", className + "." + methodName, "绕过检测");
                                
                                // 根据返回类型返回安全值
                                var returnType = method.getReturnType().getName();
                                
                                switch(returnType) {
                                    case "boolean":
                                        return false;
                                    case "int":
                                    case "long":
                                    case "short":
                                    case "byte":
                                        return 0;
                                    case "java.lang.String":
                                        return "safe";
                                    case "java.lang.Object":
                                        return null;
                                    default:
                                        return null;
                                }
                            };
                            
                            bypassState.javaHooks[className + "." + methodName] = {
                                hooked: true,
                                returnType: method.getReturnType().getName()
                            };
                            
                            console.log("[Hook] Java: " + className + "." + methodName);
                        } catch(e) {
                            console.log("[-] Hook 失败: " + className + "." + methodName + " - " + e);
                        }
                    }
                }
            } catch(e) {
                // 类不存在，继续
            }
        });
        
        // Hook 系统调试检查
        try {
            var Debug = Java.use('android.os.Debug');
            
            Debug.isDebuggerConnected.implementation = function() {
                logDetection("Java", "Debug.isDebuggerConnected", "返回 false");
                return false;
            };
            
            if (Debug.waitingForDebugger) {
                Debug.waitingForDebugger.implementation = function() {
                    logDetection("Java", "Debug.waitingForDebugger", "返回 false");
                    return false;
                };
            }
            
            bypassState.javaHooks["android.os.Debug"] = { hooked: true };
            console.log("[Hook] 系统调试检查已绕过");
        } catch(e) {
            console.log("[-] Hook android.os.Debug 失败: " + e);
        }
        
        // Hook 系统属性获取
        try {
            var System = Java.use('java.lang.System');
            var originalGetProperty = System.getProperty.overload('java.lang.String');
            
            originalGetProperty.implementation = function(key) {
                var sensitiveKeys = [
                    "ro.debuggable", "ro.secure", "ro.kernel.qemu",
                    "ro.build.tags", "ro.build.type", "service.adb.root",
                    "init.svc.adbd", "sys.oem_unlock_allowed",
                    "frida", "xposed", "magisk", "supersu"
                ];
                
                if (key) {
                    var keyLower = key.toLowerCase();
                    for (var i = 0; i < sensitiveKeys.length; i++) {
                        if (keyLower.includes(sensitiveKeys[i].toLowerCase())) {
                            logDetection("Java", "System.getProperty", "隐藏属性: " + key);
                            return null;
                        }
                    }
                }
                
                return originalGetProperty.call(this, key);
            };
            
            bypassState.javaHooks["System.getProperty"] = { hooked: true };
            console.log("[Hook] 系统属性检查已过滤");
        } catch(e) {
            console.log("[-] Hook System.getProperty 失败: " + e);
        }
        
        // Hook 应用退出
        try {
            var System = Java.use('java.lang.System');
            var Runtime = Java.use('java.lang.Runtime');
            
            System.exit.implementation = function(status) {
                logDetection("Java", "System.exit", "阻止退出: " + status);
                // 不执行退出
                console.log("[🚫] 阻止应用退出 (status=" + status + ")");
            };
            
            Runtime.exit.implementation = function(status) {
                logDetection("Java", "Runtime.exit", "阻止退出: " + status);
                // 不执行退出
                console.log("[🚫] 阻止运行时退出 (status=" + status + ")");
            };
            
            bypassState.javaHooks["exit"] = { hooked: true };
            console.log("[Hook] 退出函数已拦截");
        } catch(e) {
            console.log("[-] Hook 退出函数失败: " + e);
        }
        
        bypassState.layersApplied++;
        console.log("[Bangcle-Bypass] ✅ 第2层: Java 层检测绕过完成");
    }
    
    // ==================== 第3层: 内存与进程隐藏 ====================
    
    function applyMemoryAndProcessHiding() {
        console.log("[Bangcle-Bypass] 🕵️ 应用内存与进程隐藏...");
        
        // 隐藏 Frida 字符串特征
        var fridaKeywords = [
            "frida", "gadget", "agent", "libfrida", "frida-gadget",
            "FRIDA", "GADGET", "re.frida", "frida_agent_main",
            "gum-js-loop", "gumjs", "frida-core", "linjector"
        ];
        
        // Hook 字符串搜索函数
        var searchFunctions = ["memmem", "strstr", "strcasestr", "strnstr"];
        
        searchFunctions.forEach(function(funcName) {
            try {
                var funcAddr = Module.findExportByName(null, funcName);
                if (funcAddr) {
                    Interceptor.attach(funcAddr, {
                        onEnter: function(args) {
                            var haystack = args[0];
                            var needle = args[1];
                            
                            if (!needle.isNull()) {
                                try {
                                    var needleStr = Memory.readUtf8String(needle, 50); // 读取前50字符
                                    if (needleStr) {
                                        for (var i = 0; i < fridaKeywords.length; i++) {
                                            if (needleStr.toLowerCase().includes(fridaKeywords[i].toLowerCase())) {
                                                logDetection("memory", funcName, "隐藏 Frida 关键词: " + needleStr);
                                                this.shouldHide = true;
                                                break;
                                            }
                                        }
                                    }
                                } catch(e) {}
                            }
                        },
                        onLeave: function(retval) {
                            if (this.shouldHide) {
                                // 返回未找到
                                retval.replace(ptr(0));
                                console.log("[Bypass] 隐藏 Frida 特征字符串");
                            }
                        }
                    });
                    
                    bypassState.nativeHooks[funcName] = { hooked: true };
                }
            } catch(e) {
                console.log("[-] Hook " + funcName + " 失败: " + e);
            }
        });
        
        // 修改 /proc/self/status 中的 TracerPid
        try {
            var readFunc = Module.findExportByName(null, "read");
            if (readFunc) {
                Interceptor.attach(readFunc, {
                    onEnter: function(args) {
                        var fd = args[0].toInt32();
                        var buf = args[1];
                        var count = args[2].toInt32();
                        
                        // 检查是否是读取 /proc/self/status
                        if (fd > 0 && count >= 100) {
                            this.monitorStatus = true;
                            this.readBuf = buf;
                            this.readCount = count;
                        }
                    },
                    onLeave: function(retval) {
                        if (this.monitorStatus && !retval.isNull()) {
                            var bytesRead = retval.toInt32();
                            if (bytesRead > 0) {
                                try {
                                    var content = Memory.readUtf8String(this.readBuf, bytesRead);
                                    if (content && content.includes("TracerPid:")) {
                                        // 修改 TracerPid 为 0
                                        var modified = content.replace(/TracerPid:\s*\d+/, "TracerPid:\t0");
                                        Memory.writeUtf8String(this.readBuf, modified);
                                        logDetection("memory", "read", "修改 TracerPid 为 0");
                                        console.log("[Bypass] 修改 TracerPid 为 0");
                                    }
                                } catch(e) {}
                            }
                        }
                    }
                });
                
                bypassState.nativeHooks["read_proc_status"] = { hooked: true };
            }
        } catch(e) {
            console.log("[-] Hook /proc/self/status 读取失败: " + e);
        }
        
        // 隐藏 maps 中的敏感映射
        try {
            var fopenFunc = Module.findExportByName(null, "fopen");
            if (fopenFunc) {
                Interceptor.attach(fopenFunc, {
                    onEnter: function(args) {
                        var filename = args[0];
                        if (!filename.isNull()) {
                            try {
                                var path = Memory.readUtf8String(filename);
                                if (path && path.includes("/proc/") && path.includes("/maps")) {
                                    logDetection("memory", "fopen", "拦截 maps 访问: " + path);
                                    this.shouldBlock = true;
                                }
                            } catch(e) {}
                        }
                    },
                    onLeave: function(retval) {
                        if (this.shouldBlock) {
                            // 返回空指针
                            retval.replace(ptr(0));
                            console.log("[Bypass] 阻止 /proc/*/maps 访问");
                        }
                    }
                });
            }
        } catch(e) {
            console.log("[-] Hook maps 访问失败: " + e);
        }
        
        // ==================== Frida特征深度隐藏 ====================
        console.log("[Bangcle-Bypass] 🎭 应用Frida特征深度隐藏...");
        
        // 1. 伪装进程名 - 不让别人知道我们是Frida
        try {
            var getprogname = Module.findExportByName(null, "getprogname");
            if (getprogname) {
                Interceptor.replace(getprogname, function() {
                    logDetection("process", "getprogname", "伪装为system_server");
                    return "system_server"; // 假装是系统进程
                });
                bypassState.nativeHooks["getprogname"] = { hooked: true };
                console.log("[Hook] 进程名伪装: getprogname -> system_server");
            }
        } catch(e) {
            console.log("[-] Hook getprogname 失败: " + e);
        }
        
        // 2. 增强文件访问拦截 - 隐藏Frida相关文件
        try {
            var openFunc = Module.findExportByName(null, "open");
            if (openFunc) {
                // 检查是否已经hook过open（第1层可能已经hook）
                if (!bypassState.nativeHooks["open_enhanced"]) {
                    Interceptor.attach(openFunc, {
                        onEnter: function(args) {
                            var filename = args[0];
                            if (!filename.isNull()) {
                                try {
                                    var path = Memory.readUtf8String(filename);
                                    if (path) {
                                        // 检测 frida/gadget 相关文件
                                        var fridaPatterns = ["frida", "gadget", "libfrida", "frida-gadget", "re.frida"];
                                        for (var i = 0; i < fridaPatterns.length; i++) {
                                            if (path.toLowerCase().includes(fridaPatterns[i].toLowerCase())) {
                                                logDetection("file", "open", "拦截Frida文件访问: " + path);
                                                this.shouldBlock = true;
                                                break;
                                            }
                                        }
                                    }
                                } catch(e) {}
                            }
                        },
                        onLeave: function(retval) {
                            if (this.shouldBlock) {
                                retval.replace(-1); // 返回-1表示"文件不存在"
                                console.log("[Bypass] 阻止Frida文件访问");
                            }
                        }
                    });
                    bypassState.nativeHooks["open_enhanced"] = { hooked: true };
                    console.log("[Hook] 增强文件访问拦截");
                }
            }
        } catch(e) {
            console.log("[-] 增强open拦截失败: " + e);
        }
        
        // 3. 拦截Frida网络相关查询
        try {
            var getaddrinfo = Module.findExportByName(null, "getaddrinfo");
            if (getaddrinfo) {
                Interceptor.attach(getaddrinfo, {
                    onEnter: function(args) {
                        var hostname = args[0];
                        if (!hostname.isNull()) {
                            try {
                                var host = Memory.readUtf8String(hostname);
                                if (host && host.includes("frida")) {
                                    logDetection("network", "getaddrinfo", "拦截Frida主机名查询: " + host);
                                    this.shouldBlock = true;
                                }
                            } catch(e) {}
                        }
                    },
                    onLeave: function(retval) {
                        if (this.shouldBlock) {
                            // 返回错误代码 EAI_NONAME
                            retval.replace(ptr(-2));
                            console.log("[Bypass] 阻止Frida网络查询");
                        }
                    }
                });
                bypassState.nativeHooks["getaddrinfo"] = { hooked: true };
                console.log("[Hook] Frida网络查询拦截");
            }
        } catch(e) {
            console.log("[-] Hook getaddrinfo 失败: " + e);
        }
        
        // 4. 隐藏Frida相关环境变量
        try {
            var getenv = Module.findExportByName(null, "getenv");
            if (getenv) {
                Interceptor.attach(getenv, {
                    onEnter: function(args) {
                        var envName = args[0];
                        if (!envName.isNull()) {
                            try {
                                var name = Memory.readUtf8String(envName);
                                if (name && (name.includes("FRIDA") || name.includes("GADGET"))) {
                                    logDetection("env", "getenv", "隐藏环境变量: " + name);
                                    this.shouldHide = true;
                                }
                            } catch(e) {}
                        }
                    },
                    onLeave: function(retval) {
                        if (this.shouldHide) {
                            // 返回空指针，表示环境变量不存在
                            retval.replace(ptr(0));
                            console.log("[Bypass] 隐藏Frida环境变量");
                        }
                    }
                });
                bypassState.nativeHooks["getenv"] = { hooked: true };
                console.log("[Hook] 环境变量隐藏");
            }
        } catch(e) {
            console.log("[-] Hook getenv 失败: " + e);
        }
        
        console.log("[Bangcle-Bypass] ✅ Frida特征深度隐藏完成");
        
        bypassState.layersApplied++;
        console.log("[Bangcle-Bypass] ✅ 第3层: 内存与进程隐藏完成");
    }
    
    // ==================== 第4层: 主动防御与监控 ====================
    
    function applyActiveDefense() {
        console.log("[Bangcle-Bypass] 🛡️ 应用主动防御与监控...");
        
        // 线程监控 - 检测可能的反调试线程
        var monitoredThreads = {};
        
        // Hook 线程创建
        try {
            var pthreadCreate = Module.findExportByName(null, "pthread_create");
            if (pthreadCreate) {
                Interceptor.attach(pthreadCreate, {
                    onEnter: function(args) {
                        this.threadStart = args[2]; // 线程函数
                        this.threadArg = args[3];   // 线程参数
                    },
                    onLeave: function(retval) {
                        if (!retval.isNull() && this.threadStart) {
                            var threadId = retval.toInt32();
                            // 可以记录线程信息，用于监控
                            monitoredThreads[threadId] = {
                                start: this.threadStart,
                                arg: this.threadArg,
                                created: Date.now()
                            };
                        }
                    }
                });
            }
        } catch(e) {
            console.log("[-] Hook pthread_create 失败: " + e);
        }
        
        // 定时状态报告
        var heartbeatCount = 0;
        var heartbeatInterval = setInterval(function() {
            heartbeatCount++;
            
            var status = {
                heartbeat: heartbeatCount,
                uptime: Math.floor((Date.now() - bypassState.startTime) / 1000),
                detectionsBlocked: bypassState.detectionsBlocked,
                layersActive: bypassState.layersApplied,
                libsFound: bypassState.libsFound.length,
                nativeHooks: Object.keys(bypassState.nativeHooks).length,
                javaHooks: Object.keys(bypassState.javaHooks).length,
                timestamp: new Date().toISOString()
            };
            
            // 每5次心跳发送一次详细报告
            if (heartbeatCount % 5 === 0) {
                sendUpdate("心跳状态报告", status);
                console.log("[Bangcle-Bypass] 💓 心跳 #" + heartbeatCount + 
                          " | 运行: " + status.uptime + "s | 拦截: " + status.detectionsBlocked);
            }
            
            // 检查进程是否仍在运行
            try {
                var currentActivity = Java.use("android.app.ActivityThread").currentActivity();
                if (currentActivity) {
                    bypassState.currentActivity = currentActivity.toString();
                }
            } catch(e) {}
            
        }, 10000); // 每10秒一次
        
        // 记录心跳间隔，用于清理
        bypassState.heartbeatInterval = heartbeatInterval;
        
        // 异常处理 - 防止脚本被卸载
        Process.setExceptionHandler(function(exception) {
            console.log("[⚠️] 异常捕获: " + exception);
            console.log("[⚠️] 上下文: " + JSON.stringify(exception.context));
            
            // 尝试恢复执行
            return true;
        });
        
        bypassState.layersApplied++;
        console.log("[Bangcle-Bypass] ✅ 第4层: 主动防御与监控完成");
    }
    
    // ==================== 主执行流程 ====================
    
    console.log("[Bangcle-Bypass] 🚀 开始加载多层绕过策略...");
    
    // 获取包名信息
    try {
        var ActivityThread = Java.use("android.app.ActivityThread");
        var currentPackage = ActivityThread.currentPackageName();
        if (currentPackage) {
            bypassState.packageName = currentPackage.toString();
            console.log("[Bangcle-Bypass] 📦 当前应用: " + bypassState.packageName);
        }
    } catch(e) {
        console.log("[-] 无法获取包名: " + e);
    }
    
    // 顺序应用各层防护
    setTimeout(function() {
        try { applyBangcleSpecificHooks(); } catch(e) { console.log("[❌] 第1层失败: " + e); }
    }, 500);
    
    setTimeout(function() {
        try { applyJavaLayerHooks(); } catch(e) { console.log("[❌] 第2层失败: " + e); }
    }, 1500);
    
    setTimeout(function() {
        try { applyMemoryAndProcessHiding(); } catch(e) { console.log("[❌] 第3层失败: " + e); }
    }, 2500);
    
    setTimeout(function() {
        try { applyActiveDefense(); } catch(e) { console.log("[❌] 第4层失败: " + e); }
    }, 3500);
    
    // 完成初始化
    setTimeout(function() {
        bypassState.initialized = true;
        bypassState.initTime = Date.now() - bypassState.startTime;
        
        console.log("[Bangcle-Bypass] 🎉 多层绕过策略加载完成!");
        console.log("[Bangcle-Bypass] ⏱️  初始化耗时: " + bypassState.initTime + "ms");
        console.log("[Bangcle-Bypass] 🛡️  应用层数: " + bypassState.layersApplied + "/4");
        console.log("[Bangcle-Bypass] 🚫 已拦截检测: " + bypassState.detectionsBlocked);
        console.log("[Bangcle-Bypass] 📚 发现的库: " + bypassState.libsFound.join(", "));
        
        sendUpdate("初始化完成", {
            success: true,
            layers: bypassState.layersApplied,
            detectionsBlocked: bypassState.detectionsBlocked,
            libsFound: bypassState.libsFound
        });
        
        // 发送就绪信号
        send({ type: "bangcle_bypass_ready", state: bypassState });
        
    }, 5000);
    
    console.log("[Bangcle-Bypass] 🔄 初始化进行中...");
});

// Native 层初始化（移动到 Java.perform 内部以避免时机问题）
console.log("[Bangcle-Bypass] 🚀 脚本开始执行...");