# v0.5.6 - Win32 热键可靠性与构建时间可视化

## 中文

v0.5.6 - Win32 热键与构建可视化

### 主要改进

**稳定性**
- 修复 Win32 RegisterHotKey 注销与注册线程不一致，F12 等热键可重复注册
- 消息循环就绪检测更可靠，避免 “message loop not ready” 超时

**开发体验**
- 构建脚本新增阶段耗时输出（资源预处理/编译/总耗时），便于排查打包时长

### 升级步骤

**从 v0.5.5 升级**
1. 下载 `SonicInput-v0.5.6-win64.exe`
2. 关闭旧版本并替换可执行文件
3. 双击托盘或按热键启动（配置沿用）

**注意**
- 若 F12 被占用，可改用 Alt+H 或自定义组合
- 默认热键后端为 win32，无需管理员

### 系统要求

**最低**
- Windows 10 64-bit
- 4GB RAM
- 500MB 磁盘

**推荐**
- Windows 11 64-bit
- 8GB RAM
- 1GB 磁盘

### 技术支持

**配置与日志**
- 配置：`%AppData%/SonicInput/config.json`
- 日志：`%AppData%/SonicInput/logs/app.log`

**反馈**
- GitHub Issues: https://github.com/Oxidane-bot/SonicInput/issues

---

## English

v0.5.6 - Win32 Hotkey Reliability & Build Timing

### Key Improvements

**Stability**
- Fixed thread mismatch between RegisterHotKey register/unregister so F12 can be re-registered reliably
- More robust message-loop readiness detection (no more “message loop not ready” timeouts)

**DX**
- Build script prints stage timings (asset staging / compile / total) to debug long builds

### Upgrade Steps

**From v0.5.5**
1. Download `SonicInput-v0.5.6-win64.exe`
2. Close the old version and replace the executable
3. Launch from tray or hotkey (existing config is kept)

**Notes**
- If F12 conflicts, switch to Alt+H or any custom combo
- Default backend is win32 (no admin required)

### System Requirements

**Minimum**
- Windows 10 64-bit
- 4GB RAM
- 500MB disk

**Recommended**
- Windows 11 64-bit
- 8GB RAM
- 1GB disk

### Technical Support

**Config & Logs**
- Config: `%AppData%/SonicInput/config.json`
- Logs: `%AppData%/SonicInput/logs/app.log`

**Issues**
- GitHub Issues: https://github.com/Oxidane-bot/SonicInput/issues

---

**核心改进**: v0.5.6 提升 Win32 热键可靠性并提供构建耗时可视化。  
**Core Improvements**: v0.5.6 improves Win32 hotkey reliability and surfaces build timings.
