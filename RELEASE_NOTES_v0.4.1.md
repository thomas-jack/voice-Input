# v0.4.1 - 配置热重载升级

## 中文

v0.4.1 - 配置热重载升级

### 主要改进

**配置热重载**
- 支持转录服务商无重启切换（本地/Groq/SiliconFlow/Qwen）
- 批量配置更新机制，防止重复模型加载
- 热重载后自动加载本地模型
- 配置变更即时生效，无需重启应用

**性能优化**
- 消除重复模型实例化（节省 226MB 内存）
- 配置批量更新减少 IO 操作
- 事件监听器生命周期优化

**稳定性增强**
- 修复变量命名冲突导致的热键失效问题
- 改进事件监听器生命周期管理
- 优化控制器启动和停止流程

### 技术细节

**架构改进**
- BaseController 变量重命名：`_state` → `_state_manager`（避免与 LifecycleComponent 冲突）
- 事件监听器现在在 `_do_start()` 注册，在 `_do_stop()` 清理
- 新增 `ConfigService.set_settings_batch()` 批量配置 API
- 统一参数命名：`whisper_engine_factory` → `speech_service_factory`

**修复的问题**
- 修复热重载后热键失效（变量命名冲突）
- 修复热重载后事件监听器丢失
- 修复配置切换时重复实例化模型
- 修复本地提供商切换后模型未加载

### 使用方法

**切换转录服务商**
1. 打开设置窗口
2. 选择"转录设置"标签
3. 切换"转录提供商"（本地/Groq/SiliconFlow/Qwen）
4. 点击"应用"按钮
5. 立即生效，无需重启

**支持的服务商**
- 本地：sherpa-onnx（Paraformer/Zipformer）
- Groq：whisper-large-v3-turbo
- SiliconFlow：FunAudioLLM/SenseVoiceSmall
- Qwen：qwen3-asr-flash

### 升级步骤

**从 v0.4.0 升级**
1. 下载 SonicInput-v0.4.1-win64.exe
2. 关闭旧版本，替换可执行文件
3. 启动应用（配置自动生效）

**注意事项**
- 完全兼容 v0.4.0 配置
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

v0.4.1 - Configuration Hot Reload Upgrade

### Key Improvements

**Configuration Hot Reload**
- Support switching transcription providers without restart (Local/Groq/SiliconFlow/Qwen)
- Batch configuration update mechanism to prevent duplicate model loading
- Auto-load local model after hot reload
- Instant configuration changes without app restart

**Performance Optimization**
- Eliminate duplicate model instantiation (save 226MB memory)
- Batch configuration updates reduce IO operations
- Event listener lifecycle optimization

**Stability Enhancements**
- Fix hotkey failure caused by variable naming conflict
- Improve event listener lifecycle management
- Optimize controller startup and shutdown flow

### Technical Details

**Architecture Improvements**
- BaseController variable rename: `_state` → `_state_manager` (avoid conflict with LifecycleComponent)
- Event listeners now register in `_do_start()`, cleanup in `_do_stop()`
- New `ConfigService.set_settings_batch()` batch configuration API
- Unified parameter naming: `whisper_engine_factory` → `speech_service_factory`

**Fixed Issues**
- Fix hotkey failure after hot reload (variable naming conflict)
- Fix event listener loss after hot reload
- Fix duplicate model instantiation during config switch
- Fix model not loaded after switching to local provider

### Usage

**Switch Transcription Provider**
1. Open Settings window
2. Select "Transcription Settings" tab
3. Switch "Transcription Provider" (Local/Groq/SiliconFlow/Qwen)
4. Click "Apply" button
5. Takes effect immediately, no restart needed

**Supported Providers**
- Local: sherpa-onnx (Paraformer/Zipformer)
- Groq: whisper-large-v3-turbo
- SiliconFlow: FunAudioLLM/SenseVoiceSmall
- Qwen: qwen3-asr-flash

### Upgrade Steps

**From v0.4.0**
1. Download SonicInput-v0.4.1-win64.exe
2. Close old version, replace executable
3. Launch app (config auto-applied)

**Notes**
- Fully compatible with v0.4.0 config
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

**核心改进总结**: v0.4.1 实现配置热重载功能，支持转录服务商无重启切换，节省内存，提升用户体验。

**Core Improvements**: v0.4.1 implements configuration hot reload, supports switching transcription providers without restart, saves memory, improves user experience.
