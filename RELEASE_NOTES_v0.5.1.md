# v0.5.1 - Bug 修复

## 中文

v0.5.1 - Bug 修复

### 主要改进

**UI 渲染修复**
- 修复录音悬浮窗首次显示时灰色背景条渲染不完整
- 音频电平指示器背景条现在能够正确显示
- 解决单例模式导致的样式初始化问题

**流式转录改进**
- 修复本地 chunked 模式文本顺序错乱问题
- 修复流式转录共享超时导致后续块等待时间不足
- 按 chunk_id 排序提取文本，确保顺序正确
- 每个块使用独立动态超时（基于音频长度，最少 30 秒）

**日志和可观测性**
- 改进超时跟踪和日志记录
- 明确记录超时的 chunk_id，提升调试体验

### 技术细节

**UI 修复原理**
- 在 QLabel 创建时添加初始 background-color 样式
- 避免首次显示时样式未应用导致的渲染问题

**Chunked 模式修复原理**
- 问题根因：chunks 完成顺序不一致（如 0,1,3,2,4,5,7,6）
- 解决方案：文本提取时按 chunk_id 排序，确保顺序正确
- 超时优化：从共享 30 秒改为独立动态超时（2x 音频时长）

### 升级步骤

**从 v0.5.0 升级**
1. 下载 SonicInput-v0.5.1-win64.exe
2. 关闭旧版本，替换可执行文件
3. 启动应用（配置自动生效）

**注意事项**
- 完全兼容 v0.5.0 配置
- 无需手动调整任何设置
- 直接替换即可使用

### 系统要求

**最低配置**
- Windows 10 64-bit
- Intel Core i3 或同等 CPU
- 4GB RAM
- 500MB 磁盘空间

**推荐配置**
- Windows 11 64-bit
- Intel Core i5 或 AMD Ryzen 5
- 8GB RAM
- 1GB 磁盘空间

### 技术支持

**配置和日志**
- 配置：`%AppData%\SonicInput\config.json`
- 日志：`%AppData%\SonicInput\logs\app.log`
- 模型：`%AppData%\SonicInput\models/`

**问题反馈**
- GitHub Issues: [提交 Issue](https://github.com/Oxidane-bot/SonicInput/issues)

---

## English

v0.5.1 - Bug Fixes

### Key Improvements

**UI Rendering Fix**
- Fixed incomplete gray background bars on first recording overlay display
- Audio level indicator background bars now render correctly
- Resolved style initialization issue caused by singleton pattern

**Streaming Transcription Improvements**
- Fixed text ordering issue in local chunked mode
- Fixed insufficient wait time for subsequent chunks due to shared timeout
- Sort text extraction by chunk_id to ensure correct order
- Independent dynamic timeout per chunk (based on audio length, minimum 30s)

**Logging and Observability**
- Improved timeout tracking and logging
- Explicitly log timed-out chunk_ids for better debugging

### Technical Details

**UI Fix Approach**
- Add initial background-color style during QLabel creation
- Avoid rendering issues when style is not applied on first show

**Chunked Mode Fix Approach**
- Root cause: Chunks complete out of order (e.g., 0,1,3,2,4,5,7,6)
- Solution: Sort by chunk_id during text extraction to ensure correct order
- Timeout optimization: From shared 30s to independent dynamic timeout (2x audio duration)

### Upgrade Steps

**From v0.5.0**
1. Download SonicInput-v0.5.1-win64.exe
2. Close old version, replace executable
3. Launch app (config auto-applied)

**Notes**
- Fully compatible with v0.5.0 config
- No manual settings adjustment needed
- Direct replacement works

### System Requirements

**Minimum**
- Windows 10 64-bit
- Intel Core i3 or equivalent CPU
- 4GB RAM
- 500MB disk space

**Recommended**
- Windows 11 64-bit
- Intel Core i5 or AMD Ryzen 5
- 8GB RAM
- 1GB disk space

### Technical Support

**Configuration and Logs**
- Config: `%AppData%\SonicInput\config.json`
- Logs: `%AppData%\SonicInput\logs\app.log`
- Models: `%AppData%\SonicInput\models/`

**Issue Reporting**
- GitHub Issues: [Submit Issue](https://github.com/Oxidane-bot/SonicInput/issues)

---

**核心改进总结**: v0.5.1 修复录音悬浮窗 UI 渲染和 chunked 模式文本顺序问题，提升稳定性。

**Core Improvements**: v0.5.1 fixes recording overlay UI rendering and chunked mode text ordering issues for improved stability.
