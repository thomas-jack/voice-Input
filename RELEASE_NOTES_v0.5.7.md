# v0.5.7 - 日志轮转与默认配置一致性

## 中文

v0.5.7 - 自动日志轮转 & 配置示例对齐

### 亮点

**稳定性**
- 日志文件超过 10MB 时自动轮转，最多保留 2 个备份，避免单个日志无限膨胀
- `logging.max_log_size_mb` / `logging.max_backup_files` 默认值与示例配置保持一致

**体验**
- 示例配置同步了日志轮转字段，开箱即可限制体积，无需手工修改

### 升级指南

**从 v0.5.6 升级**
1. 下载 `SonicInput-v0.5.7-win64.exe`
2. 关闭旧版本，替换可执行文件
3. 重新启动（现有配置与日志自动沿用）

**提示**
- 日志默认限制：10MB 主文件 + 2 个备份，可在 `%AppData%/SonicInput/config.json` 中调整
- 若需要完全禁用日志，可在配置中设置 `logging.console_output=false` 并调低 `logging.enabled_categories`

### 系统要求

**最低**
- Windows 10 64-bit
- 4GB 内存
- 500MB 可用空间

**推荐**
- Windows 11 64-bit
- 8GB 内存
- 1GB 可用空间

### 技术支持

**配置与日志**
- 配置：`%AppData%/SonicInput/config.json`
- 日志：`%AppData%/SonicInput/logs/app.log`

**问题反馈**
- GitHub Issues: https://github.com/Oxidane-bot/SonicInput/issues

---

## English

v0.5.7 - Log Rotation & Config Parity

### Highlights

**Stability**
- Auto-rotate logs when they exceed 10MB; keep up to 2 backups to prevent runaway log growth
- Default config now includes `logging.max_log_size_mb` / `logging.max_backup_files` to match the example file

**DX**
- Sample config ships with rotation fields, so size limits work out of the box

### Upgrade Steps

**From v0.5.6**
1. Download `SonicInput-v0.5.7-win64.exe`
2. Close the old build and replace the executable
3. Relaunch (existing config & logs stay intact)

**Notes**
- Default log cap: 10MB main file + 2 backups; tune in `%AppData%/SonicInput/config.json`
- To reduce noise further, set `logging.console_output=false` and trim `logging.enabled_categories`

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

**核心改进**: v0.5.7 解决日志体积失控风险，并让默认/示例配置保持一致。  
**Core Improvements**: v0.5.7 enforces log rotation and aligns defaults with the sample config.
