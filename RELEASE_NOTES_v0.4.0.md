# v0.4.0 - 架构简化升级

## 中文

v0.4.0 - 架构简化升级

### 主要改进

**架构简化**
- 简化内部架构设计,提升代码可维护性
- 优化配置热重载机制,更快响应设置变更
- 精简依赖管理,降低开发复杂度

**性能优化**
- 启动速度提升(2秒快速启动)
- 配置变更即时生效
- 内存使用优化

**稳定性增强**
- 修复配置保存前验证,防止无效配置
- 改进模型下载进度显示
- 优化资源管理,防止内存泄漏

### 破坏性变更

**开发者相关**
- 内部架构重构,插件开发者需参考新架构文档
- 简化生命周期管理(3状态设计)
- 配置热重载机制变更

**普通用户无影响**
- 所有用户功能完全兼容
- 配置文件格式不变
- 使用体验不变

### 主要功能

**本地转录引擎**
- sherpa-onnx 轻量级引擎(安装包 <250MB)
- 双模式流式转录(chunked/realtime)
- 纯 CPU 推理,无需 GPU

**云端转录服务**
- Groq: whisper-large-v3-turbo,快速准确
- SiliconFlow: FunAudioLLM/SenseVoiceSmall
- Qwen ASR: qwen3-asr-flash,极速转录

**智能输入系统**
- 多种输入方式支持
- 增量式文本替换
- 剪贴板智能恢复

### 升级步骤

**推荐所有用户升级**
1. 性能优化,启动更快
2. 稳定性增强,使用更可靠
3. 完全向后兼容,无需修改配置

**升级方式**
1. 下载 SonicInput-v0.4.0-win64.exe
2. 关闭旧版本,替换可执行文件
3. 启动应用(配置自动生效)

**注意事项**
- 完全兼容所有旧版本配置
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
- 配置: `%AppData%\SonicInput\config.json`
- 日志: `%AppData%\SonicInput\logs\app.log`
- 模型: `%AppData%\SonicInput\models/`

**问题反馈**
- GitHub Issues: [提交 Issue](https://github.com/Oxidane-bot/SonicInput/issues)

---

## English

v0.4.0 - Architecture Simplification

### Key Improvements

**Architecture Simplification**
- Simplified internal architecture for better maintainability
- Optimized configuration hot-reload mechanism for faster response
- Streamlined dependency management to reduce complexity

**Performance Optimization**
- Faster startup time (2-second quick start)
- Instant configuration changes
- Optimized memory usage

**Stability Enhancements**
- Added pre-save validation to prevent invalid configurations
- Improved model download progress display
- Optimized resource management to prevent memory leaks

### Breaking Changes

**Developer-Related**
- Internal architecture refactored, plugin developers should refer to new architecture docs
- Simplified lifecycle management (3-state design)
- Configuration hot-reload mechanism changed

**No Impact on Regular Users**
- All user features fully compatible
- Configuration file format unchanged
- User experience unchanged

### Key Features

**Local Transcription Engine**
- sherpa-onnx lightweight engine (installer <250MB)
- Dual-mode streaming transcription (chunked/realtime)
- Pure CPU inference, no GPU required

**Cloud Transcription Services**
- Groq: whisper-large-v3-turbo, fast and accurate
- SiliconFlow: FunAudioLLM/SenseVoiceSmall
- Qwen ASR: qwen3-asr-flash, ultra-fast transcription

**Smart Input System**
- Multiple input method support
- Incremental text replacement
- Smart clipboard recovery

### Upgrade Steps

**Recommended for All Users**
1. Performance optimization, faster startup
2. Enhanced stability, more reliable
3. Fully backward compatible, no config changes needed

**Upgrade Process**
1. Download SonicInput-v0.4.0-win64.exe
2. Close old version, replace executable
3. Launch app (config auto-applied)

**Notes**
- Fully compatible with all previous version configs
- No manual settings adjustment needed
- Direct replacement ready to use

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

**核心改进总结**: v0.4.0 通过架构简化优化系统性能和稳定性,启动更快(2秒),配置变更即时生效,完全向后兼容。

**Core Improvements**: v0.4.0 optimizes system performance and stability through architecture simplification, faster startup (2s), instant configuration changes, fully backward compatible.
