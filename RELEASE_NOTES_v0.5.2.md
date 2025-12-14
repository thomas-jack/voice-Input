# v0.5.2 - 流式转录改进

## 中文

v0.5.2 - 流式转录改进

### 主要改进

**云转录超时优化**
- 修复云提供商（Groq/SiliconFlow/Qwen）固定 30 秒超时问题
- 每个块使用独立动态超时（基于音频长度，最少 30 秒）
- 与本地 chunked 模式保持一致的超时策略

**Chunked 模式数据完整性**
- 修复 stop_recording 时可能丢失最后一个音频块的 race condition
- 确保所有录制的音频都能被正确处理和转录
- 新增单元测试覆盖边界场景

### 升级步骤

**从 v0.5.1 升级**
1. 下载 SonicInput-v0.5.2-win64.exe
2. 关闭旧版本，替换可执行文件
3. 启动应用（配置自动生效）

**注意事项**
- 完全兼容 v0.5.1 配置
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

v0.5.2 - Streaming Transcription Improvements

### Key Improvements

**Cloud Transcription Timeout Optimization**
- Fixed cloud providers (Groq/SiliconFlow/Qwen) using fixed 30-second timeout
- Independent dynamic timeout per chunk (based on audio length, minimum 30s)
- Consistent timeout strategy with local chunked mode

**Chunked Mode Data Integrity**
- Fixed race condition causing last audio chunk loss on stop_recording
- Ensure all recorded audio is properly processed and transcribed
- Added unit tests covering edge cases

### Upgrade Steps

**From v0.5.1**
1. Download SonicInput-v0.5.2-win64.exe
2. Close old version, replace executable
3. Launch app (config auto-applied)

**Notes**
- Fully compatible with v0.5.1 config
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

**核心改进总结**: v0.5.2 优化云转录超时策略，修复 chunked 模式数据完整性问题。

**Core Improvements**: v0.5.2 optimizes cloud transcription timeout strategy and fixes chunked mode data integrity issues.
