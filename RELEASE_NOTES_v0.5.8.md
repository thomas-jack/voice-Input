# v0.5.8 - 本地引擎依赖修复与启动兜底

## 中文

v0.5.8 - 本地依赖补全 & 启动不阻塞

### 亮点

**稳定性**
- onefile 构建现在会打包 `onnxruntime.dll`，避免本地引擎被误判为“未安装”
- 当本地运行环境缺失时自动切换到云端（有 API key），否则启用空实现服务让 UI 正常启动
- 启动阶段跳过不可用的本地模型自动加载，避免初始化回滚

**诊断**
- 本地引擎不可用时记录详细诊断（DLL 缺失、加载错误、VC++ 运行库状态）

### 升级步骤

**从 v0.5.7 升级**
1. 下载 `SonicInput-v0.5.8-win64.exe`
2. 关闭旧版本并替换可执行文件
3. 重新启动（配置与历史记录保持不变）

**说明**
- 如需本地引擎，请确保 sherpa-onnx 依赖完整；失败原因会写入日志
- 如已配置云端 API key，缺失本地依赖时会自动切换到云端

### 系统需求

**最低**
- Windows 10 64-bit
- 4GB 内存
- 500MB 可用磁盘

**推荐**
- Windows 11 64-bit
- 8GB 内存
- 1GB 可用磁盘

### 支持

**配置与日志**
- 配置：`%AppData%/SonicInput/config.json`
- 日志：`%AppData%/SonicInput/logs/app.log`

**问题反馈**
- GitHub Issues: https://github.com/Oxidane-bot/SonicInput/issues

---

## English

v0.5.8 - Local Runtime Fixes & Startup Fallbacks

### Highlights

**Stability**
- Onefile builds now bundle `onnxruntime.dll`, preventing false “sherpa-onnx not installed” errors
- When local runtime is missing, auto-switch to a configured cloud provider; otherwise use a stub service so the UI still launches
- Skip auto-loading local models when the service is unavailable to avoid startup rollbacks

**Diagnostics**
- Detailed local runtime diagnostics (missing DLLs, load errors, VC++ runtime presence) are logged when local ASR is unavailable

### Upgrade Steps

**From v0.5.7**
1. Download `SonicInput-v0.5.8-win64.exe`
2. Close the old build and replace the executable
3. Relaunch (config & history stay intact)

**Notes**
- If you want local ASR, ensure sherpa-onnx dependencies are present; failures are recorded in logs
- If a cloud API key is set, the app will switch to cloud automatically when local runtime is missing

### System Requirements

**Minimum**
- Windows 10 64-bit
- 4GB RAM
- 500MB disk

**Recommended**
- Windows 11 64-bit
- 8GB RAM
- 1GB disk

### Support

**Config & Logs**
- Config: `%AppData%/SonicInput/config.json`
- Logs: `%AppData%/SonicInput/logs/app.log`

**Issues**
- GitHub Issues: https://github.com/Oxidane-bot/SonicInput/issues

---

**核心改进**: v0.5.8 解决本地引擎依赖缺失导致的启动失败，并提供自动回退与诊断信息。  
**Core Improvements**: v0.5.8 bundles local runtime dependencies, adds safe fallbacks, and improves diagnostics.
