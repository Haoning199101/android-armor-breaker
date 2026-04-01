// Frida 内存扫描器 - 针对快速崩溃的 Bangcle 加固应用
// 在应用崩溃前立即扫描内存并提取 DEX 数据

console.log("[💥] Frida 内存扫描器启动 - 针对快速崩溃应用");
console.log("[📅] 时间: " + new Date().toISOString());

// 全局状态
var scannerState = {
    startTime: Date.now(),
    regionsScanned: 0,
    dexFound: 0,
    bytesRead: 0,
    errors: 0,
    savedFiles: []
};

// 发送状态更新
function sendUpdate(message, data) {
    var update = {
        type: "memory_scanner_update",
        timestamp: new Date().toISOString(),
        message: message,
        data: data || {},
        state: scannerState
    };
    send(update);
}

// 工具函数：将字节数组保存为文件（通过 base64 发送）
function saveBytesToFile(filename, bytes) {
    try {
        // 将字节数组转换为 base64
        var base64 = bytes.reduce(function(acc, byte) {
            return acc + String.fromCharCode(byte);
        }, '');
        base64 = btoa(base64);
        
        var fileData = {
            filename: filename,
            data: base64,
            size: bytes.length,
            timestamp: new Date().toISOString()
        };
        
        send({type: "memory_dump_file", file: fileData});
        scannerState.savedFiles.push(filename);
        
        console.log("[💾] 保存文件: " + filename + " (" + bytes.length + " bytes)");
        return true;
    } catch(e) {
        console.log("[❌] 保存文件失败: " + e);
        scannerState.errors++;
        return false;
    }
}

// 快速内存扫描 - 在 Native 层立即执行
function quickMemoryScan() {
    console.log("[🔍] 开始快速内存扫描...");
    
    try {
        // 获取当前进程的内存映射
        var ranges = Process.enumerateRanges({
            protection: 'r--',  // 只读区域
            coalesce: true
        });
        
        console.log("[📊] 找到 " + ranges.length + " 个可读内存区域");
        scannerState.regionsScanned = ranges.length;
        
        var dexSignatures = [
            new Uint8Array([0x64, 0x65, 0x78, 0x0A, 0x30, 0x33, 0x35, 0x00]),  // dex\n035\0
            new Uint8Array([0x64, 0x65, 0x78, 0x0A, 0x30, 0x33, 0x36, 0x00]),  // dex\n036\0
            new Uint8Array([0x64, 0x65, 0x78, 0x0A, 0x30, 0x33, 0x37, 0x00]),  // dex\n037\0
            new Uint8Array([0x64, 0x65, 0x78, 0x0A, 0x30, 0x33, 0x38, 0x00]),  // dex\n038\0
            new Uint8Array([0x64, 0x65, 0x78, 0x0A, 0x30, 0x33, 0x39, 0x00]),  // dex\n039\0
        ];
        
        var foundDexCount = 0;
        
        // 扫描每个区域的前 1MB 数据
        for (var i = 0; i < ranges.length; i++) {
            var range = ranges[i];
            var regionSize = range.size;
            
            // 跳过太大的区域（扫描前1MB即可）
            var scanSize = Math.min(regionSize, 1024 * 1024);  // 最多扫描1MB
            
            if (scanSize < 1024) continue;  // 跳过太小的区域
            
            console.log("[🔎] 扫描区域 " + (i+1) + "/" + ranges.length + 
                       ": 0x" + range.base.toString(16) + 
                       " (" + (scanSize / 1024).toFixed(1) + " KB)");
            
            try {
                // 读取内存数据
                var memoryData = Memory.readByteArray(range.base, scanSize);
                scannerState.bytesRead += scanSize;
                
                // 转换为 Uint8Array 以便搜索
                var bytes = new Uint8Array(memoryData);
                
                // 搜索 DEX 签名
                for (var sigIndex = 0; sigIndex < dexSignatures.length; sigIndex++) {
                    var signature = dexSignatures[sigIndex];
                    
                    // 简单线性搜索（速度足够，因为只扫描1MB）
                    for (var pos = 0; pos < bytes.length - signature.length; pos++) {
                        var match = true;
                        for (var j = 0; j < signature.length; j++) {
                            if (bytes[pos + j] !== signature[j]) {
                                match = false;
                                break;
                            }
                        }
                        
                        if (match) {
                            console.log("[🎯] 找到 DEX 签名 #" + sigIndex + 
                                       " 在地址 0x" + (range.base.add(pos)).toString(16));
                            
                            // 尝试读取完整的 DEX 文件
                            // DEX 文件大小通常在头部偏移 0x20 处
                            try {
                                var dexSizeOffset = pos + 0x20;
                                if (dexSizeOffset + 4 <= bytes.length) {
                                    // 读取 32 位小端整数
                                    var dexSize = (bytes[dexSizeOffset]) |
                                                  (bytes[dexSizeOffset + 1] << 8) |
                                                  (bytes[dexSizeOffset + 2] << 16) |
                                                  (bytes[dexSizeOffset + 3] << 24);
                                    
                                    console.log("[📏] 检测到的 DEX 大小: " + dexSize + " bytes");
                                    
                                    // 确保大小合理
                                    if (dexSize >= 1024 && dexSize <= 10 * 1024 * 1024) {
                                        // 读取完整的 DEX 文件
                                        var actualReadSize = Math.min(dexSize, regionSize - pos);
                                        var fullDexData = Memory.readByteArray(range.base.add(pos), actualReadSize);
                                        
                                        // 保存文件
                                        var filename = "dex_" + foundDexCount + "_0x" + range.base.add(pos).toString(16) + ".dex";
                                        if (saveBytesToFile(filename, new Uint8Array(fullDexData))) {
                                            foundDexCount++;
                                            scannerState.dexFound++;
                                            console.log("[✅] DEX 文件保存成功: " + filename);
                                        }
                                    }
                                }
                            } catch(e) {
                                console.log("[⚠️] 读取 DEX 大小失败: " + e);
                            }
                            
                            break;  // 找到一个签名后停止搜索此区域
                        }
                    }
                }
                
                // 额外检查：搜索 "classes.dex" 字符串（某些加固壳可能保留）
                var classesDexPattern = [0x63, 0x6C, 0x61, 0x73, 0x73, 0x65, 0x73, 0x2E, 0x64, 0x65, 0x78];  // "classes.dex"
                for (var pos = 0; pos < bytes.length - classesDexPattern.length; pos++) {
                    var match = true;
                    for (var j = 0; j < classesDexPattern.length; j++) {
                        if (bytes[pos + j] !== classesDexPattern[j]) {
                            match = false;
                            break;
                        }
                    }
                    
                    if (match) {
                        console.log("[🔍] 找到 'classes.dex' 字符串在 0x" + (range.base.add(pos)).toString(16));
                        // 可以进一步分析
                        break;
                    }
                }
                
            } catch(e) {
                console.log("[❌] 扫描区域失败: " + e);
                scannerState.errors++;
            }
            
            // 每扫描几个区域发送一次更新
            if (i % 5 === 0) {
                sendUpdate("扫描进度: " + (i+1) + "/" + ranges.length + " 区域", {
                    regionsScanned: i+1,
                    dexFound: foundDexCount,
                    bytesRead: scannerState.bytesRead
                });
            }
        }
        
        console.log("[📊] 扫描完成: 找到 " + foundDexCount + " 个 DEX 文件");
        console.log("[📊] 总计: 扫描 " + scannerState.regionsScanned + " 个区域, " + 
                   (scannerState.bytesRead / 1024 / 1024).toFixed(2) + " MB 数据");
        
        sendUpdate("扫描完成", {
            totalRegions: scannerState.regionsScanned,
            totalDexFound: foundDexCount,
            totalBytesRead: scannerState.bytesRead,
            errors: scannerState.errors
        });
        
        return foundDexCount > 0;
        
    } catch(e) {
        console.log("[💥] 内存扫描崩溃: " + e);
        sendUpdate("扫描崩溃", {error: e.toString()});
        return false;
    }
}

// 深度内存扫描 - 更彻底的搜索
function deepMemoryScan() {
    console.log("[🔍] 开始深度内存扫描...");
    
    try {
        // 扫描所有内存区域，包括可写和可执行区域
        var allRanges = Process.enumerateRanges({coalesce: true});
        console.log("[📊] 深度扫描: " + allRanges.length + " 个内存区域");
        
        var interestingRegions = [];
        
        // 分类区域
        for (var i = 0; i < allRanges.length; i++) {
            var range = allRanges[i];
            var protection = range.protection || '';
            
            // 记录感兴趣的区域
            if (range.size >= 1024 && range.size <= 50 * 1024 * 1024) {
                interestingRegions.push({
                    base: range.base,
                    size: range.size,
                    protection: protection,
                    file: range.file || null
                });
            }
        }
        
        console.log("[📊] 有 " + interestingRegions.length + " 个感兴趣的区域");
        
        // 对感兴趣的区域进行启发式搜索
        var foundCount = 0;
        
        for (var i = 0; i < Math.min(interestingRegions.length, 20); i++) {  // 限制前20个
            var region = interestingRegions[i];
            
            console.log("[🔎] 深度扫描区域 " + (i+1) + ": 0x" + region.base.toString(16) + 
                       " (" + (region.size / 1024).toFixed(1) + " KB, " + region.protection + ")");
            
            try {
                // 读取前8KB进行快速分析
                var sampleSize = Math.min(region.size, 8192);
                var sampleData = Memory.readByteArray(region.base, sampleSize);
                var bytes = new Uint8Array(sampleData);
                
                // 检查常见模式
                var patterns = [
                    [0x64, 0x65, 0x78, 0x0A],  // "dex\n"
                    [0x70, 0x6B, 0x67, 0x0A],  // "pkg\n" (某些加固特征)
                    [0x63, 0x6C, 0x61, 0x73, 0x73, 0x65, 0x73],  // "classes"
                ];
                
                for (var p = 0; p < patterns.length; p++) {
                    var pattern = patterns[p];
                    
                    for (var pos = 0; pos < bytes.length - pattern.length; pos++) {
                        var match = true;
                        for (var j = 0; j < pattern.length; j++) {
                            if (bytes[pos + j] !== pattern[j]) {
                                match = false;
                                break;
                            }
                        }
                        
                        if (match) {
                            console.log("[🎯] 找到模式 #" + p + " 在 0x" + region.base.add(pos).toString(16));
                            
                            // 尝试读取更多数据
                            var readSize = Math.min(region.size - pos, 1024 * 1024);  // 最多1MB
                            if (readSize > 1024) {
                                var fullData = Memory.readByteArray(region.base.add(pos), readSize);
                                
                                var filename = "deep_scan_" + foundCount + "_0x" + region.base.add(pos).toString(16) + ".bin";
                                if (saveBytesToFile(filename, new Uint8Array(fullData))) {
                                    foundCount++;
                                    console.log("[✅] 保存深度扫描数据: " + filename);
                                }
                            }
                            
                            break;
                        }
                    }
                }
                
            } catch(e) {
                // 忽略读取错误
            }
        }
        
        console.log("[📊] 深度扫描完成: 保存 " + foundCount + " 个文件");
        return foundCount > 0;
        
    } catch(e) {
        console.log("[❌] 深度扫描失败: " + e);
        return false;
    }
}

// 崩溃处理器 - 尝试在应用崩溃前捕获更多数据
function setupCrashHandler() {
    console.log("[🛡️] 设置崩溃处理器...");
    
    // 拦截常见崩溃信号
    var signals = ['SIGSEGV', 'SIGABRT', 'SIGILL', 'SIGBUS'];
    
    signals.forEach(function(sigName) {
        try {
            Process.setExceptionHandler(function(exception) {
                console.log("[💥] 捕获到异常信号: " + sigName);
                console.log("[💥] 上下文: " + JSON.stringify(exception.context));
                
                // 在崩溃前尝试最后的快速扫描
                console.log("[🚨] 应用即将崩溃，执行紧急内存扫描...");
                quickMemoryScan();
                
                // 返回 true 表示已处理异常（可能阻止崩溃）
                return true;
            });
        } catch(e) {
            console.log("[⚠️] 设置 " + sigName + " 处理器失败: " + e);
        }
    });
    
    console.log("[✅] 崩溃处理器设置完成");
}

// 主执行流程
function main() {
    console.log("[🚀] 开始内存扫描流程...");
    sendUpdate("流程开始");
    
    // 设置崩溃处理器（尽可能早）
    setupCrashHandler();
    
    // 立即执行快速扫描（应用可能随时崩溃）
    var quickResult = quickMemoryScan();
    
    if (quickResult) {
        console.log("[✅] 快速扫描成功找到 DEX 文件");
    } else {
        console.log("[⚠️] 快速扫描未找到 DEX，尝试深度扫描");
        
        // 如果应用还在运行，尝试深度扫描
        try {
            deepMemoryScan();
        } catch(e) {
            console.log("[❌] 深度扫描异常: " + e);
        }
    }
    
    // 最终状态报告
    scannerState.endTime = Date.now();
    scannerState.duration = scannerState.endTime - scannerState.startTime;
    
    console.log("[📊] 最终统计:");
    console.log("[📊]   持续时间: " + scannerState.duration + " ms");
    console.log("[📊]   扫描区域: " + scannerState.regionsScanned);
    console.log("[📊]   找到 DEX: " + scannerState.dexFound);
    console.log("[📊]   读取数据: " + (scannerState.bytesRead / 1024 / 1024).toFixed(2) + " MB");
    console.log("[📊]   保存文件: " + scannerState.savedFiles.length);
    console.log("[📊]   错误数: " + scannerState.errors);
    
    sendUpdate("流程完成", {
        success: scannerState.dexFound > 0,
        duration: scannerState.duration,
        filesSaved: scannerState.savedFiles.length,
        finalState: scannerState
    });
    
    console.log("[🎉] 内存扫描流程完成");
    
    // 返回成功状态
    return scannerState.dexFound > 0;
}

// 立即执行主函数（不等待 Java 环境）
try {
    var success = main();
    send({type: "memory_scan_complete", success: success, state: scannerState});
} catch(e) {
    console.log("[💥] 主函数异常: " + e);
    send({type: "memory_scan_error", error: e.toString(), state: scannerState});
}

// 保持脚本运行（如果应用还在）
console.log("[⏳] 内存扫描器保持运行状态...");