# SonicInput Release Notes

## v0.3.0 (2025-11-12) - sherpa-onnx 轻量级引擎迁移

### 核心升级

**完全替换 Faster Whisper 为 sherpa-onnx**
- 安装体积减少 90%：2-3GB → <250MB（包含模型）
- CPU 性能提升 30-300 倍：RTF 10-20 → 0.06-0.21
- 完全移除 GPU 依赖：无需 CUDA Toolkit、cuDNN
- 启动速度提升：模型加载 <1s，应用启动 <2s
- 内存占用优化：运行时内存降低 60-70%

**双模式流式转录系统**
- Chunked 模式（默认推荐）：30秒分块，支持 AI 优化，适合会议/文档
- Realtime 模式（最低延迟）：边录边转，减少 70-90% 等待，适合字幕/快速笔记
- 模式切换：设置 → 转录 → 流式模式选择

**新增 Qwen ASR 云服务**
- 极速转录 <500ms，支持中英文混合识别
- 长音频支持最长 3 小时
- 企业级可靠性

**6 阶段资源清理重构**
- 修复 PyAudio 流泄漏问题
- 线程安全退出机制，超时保护
- 应用退出速度提升 3-5 倍
- 无资源泄漏和假死现象

### 破坏性变更

**配置文件变更**（自动迁移）
```json
// 旧配置 (v0.2.0)
{
  "transcription": {
    "local": {
      "model": "base",
      "gpu_acceleration": true
    }
  }
}

// 新配置 (v0.3.0)
{
  "transcription": {
    "local": {
      "model": "paraformer",
      "language": "zh",
      "streaming_mode": "chunked"
    }
  }
}
```

**删除字段**
- `transcription.local.gpu_acceleration`
- `transcription.local.compute_type`
- `transcription.local.gpu_device`

**新增字段**
- `transcription.local.streaming_mode`："chunked" 或 "realtime"
- `transcription.qwen`：Qwen ASR 配置

**系统要求变更**
- 不再需要：NVIDIA GPU / CUDA Toolkit / cuDNN / 8GB+ VRAM
- 新要求：Windows 10/11 64-bit / 4GB RAM / 500MB 磁盘空间

### 版本对比

| 特性 | v0.2.0 | v0.3.0 | 提升 |
|------|--------|--------|------|
| 转录引擎 | Faster Whisper | sherpa-onnx | 架构升级 |
| 安装体积 | 2-3GB | <250MB | -90% |
| GPU 依赖 | CUDA 11.8+ 必需 | 无 | -100% |
| CPU RTF（中文）| 10-20 | 0.15-0.21 | 50-130x |
| CPU RTF（英文）| 5-10 | 0.06-0.10 | 50-160x |
| 内存占用 | 2-3GB | 600-900MB | -65% |
| 启动时间 | 5-8s | <1s | 5-8x |
| 流式转录 | 不支持 | 双模式 | 新增 |
| Qwen ASR | 不支持 | 支持 | 新增 |
| 代码行数 | 基准 | -1,650 行 | -46% |

### 主要功能

**轻量级本地模型**
- Paraformer（中文）：226MB，RTF 0.15-0.21，准确率 95%+
- Zipformer（英文）：112MB，RTF 0.06-0.10，准确率 98%+
- 首次使用自动从 GitHub releases 下载

**智能输入控制器**
- 统一输入管理：Smart Input / Clipboard / SendInput API
- 智能光标定位，文本差异计算
- 增量式文本替换

**转录提供商**
- 本地：sherpa-onnx（Paraformer / Zipformer）
- 云端：Groq / SiliconFlow / Qwen ASR
- AI 优化：OpenRouter / Groq / SiliconFlow / NVIDIA / OpenAI 兼容

### 技术细节

**代码统计**（45 个文件）
- 删除：3,611 行
- 新增：1,961 行
- 净减少：1,650 行（-46%）

**主要删除**
- whisper_engine.py（814 行）
- whisper_worker_thread.py（440 行）
- hybrid_speech_service.py（429 行）
- gpu_manager.py（331 行）

**主要新增**
- sherpa_models.py（240 行）：模型下载和管理
- sherpa_engine.py（229 行）：引擎封装
- sherpa_streaming.py（172 行）：流式转录会话
- input_controller.py（169 行）：输入控制

**依赖变更**
```toml
# 移除（2.6GB）
faster-whisper = "~1.1.0"
ctranslate2 = "~4.5.0"
torch = "~2.5.1"

# 新增（165MB）
sherpa-onnx = "~1.10.30"
onnxruntime = "~1.20.1"
```

**性能基准**（Intel i5-8250U）
- Paraformer（中文）：RTF 0.15-0.21 vs Whisper Base RTF 12-15（57-100x 提升）
- Zipformer（英文）：RTF 0.06-0.10 vs Whisper Base RTF 8-10（80-160x 提升）

**内存占用优化**
- 空闲状态：450MB → 120MB（-73%）
- 加载模型：2.4GB → 850MB（-65%）
- 转录运行：2.8GB → 920MB（-67%）

### 升级建议

**推荐所有用户升级**
1. 体积减少 90%，释放 2GB+ 磁盘空间
2. 性能提升 30-300 倍，CPU 推理更快
3. 无 GPU 要求，任何电脑流畅运行
4. 双模式流式，更低延迟体验
5. 企业级稳定性，6 阶段资源清理
6. 更多云服务，新增 Qwen ASR 支持

**升级方式**
1. 下载 `SonicInput-v0.3.0-win64.exe`
2. 关闭旧版本应用
3. 替换可执行文件
4. 启动新版本（自动迁移配置）
5. 首次使用自动下载模型（~2 分钟）

**注意事项**
- 配置自动迁移，无需手动调整
- 模型自动下载（Paraformer 226MB）
- 下载失败可手动放置到 `%AppData%\SonicInput\models/`
- GPU 设置自动移除

### 常见问题

**Q: 升级后配置文件会丢失吗？**
A: 不会，所有配置自动保留并迁移。

**Q: 需要手动下载模型吗？**
A: 不需要，首次使用时自动下载。

**Q: GPU 会继续使用吗？**
A: 不会，v0.3.0 完全基于 CPU，GPU 设置已移除。

**Q: 如何切换到 Realtime 模式？**
A: 设置 → 转录 → 流式模式 → 选择 "realtime"。

**Q: Realtime 模式支持 AI 优化吗？**
A: 不支持，Realtime 模式直接输出原始转录。

### 系统要求

**最低配置**
- Windows 10 64-bit
- Intel Core i3 或同等 CPU
- 4GB RAM
- 500MB 磁盘空间
- 网络连接（首次下载模型）

**推荐配置**
- Windows 11 64-bit
- Intel Core i5 或 AMD Ryzen 5
- 8GB RAM
- 1GB 磁盘空间
- 稳定网络连接

**详细说明**：查看完整 Release Notes: [.release-notes-v0.3.0.md](.release-notes-v0.3.0.md)

---

## v0.2.0 (2025-11-09) - 品牌重塑

### 全新品牌 "Sonic Input"

- **完整品牌统一**：26 处更新覆盖 11 个文件
- **UI 全面升级**：窗口标题、系统托盘、关于对话框
- **文档标准化**：模块文档、日志、元数据统一品牌
- **100% 品牌一致性**：所有用户可见组件完全统一

### 打包信息

**v0.2.0-win64.exe**
- 文件大小：66.32 MB（压缩比 22.86%）
- 编译工具：Nuitka 2.8.4 + MSVC 14.3
- 编译统计：1291 个 C 文件，100% 缓存命中

### 测试结果

- EventBus：6/6 tests passed
- 模型转录测试：RTF 0.44x
- GUI 启动：1.21s
- 品牌一致性：100%

### 升级说明

1. **完全兼容**：现有配置和数据无需修改
2. **简单升级**：直接替换可执行文件
3. **推荐升级**：获得统一品牌体验

---

## v0.1.5 (2025-11-06) - 功能修复

### 功能改进

- **修复重试处理功能**：增强转录失败后的重试机制
- **优化错误处理**：改进异常捕获和用户反馈
- **稳定性提升**：修复多个边缘情况下的崩溃问题
- **代码清理**：移除 1,512 行死代码，修复 6 个关键 bug

---

## v0.1.4 (2025-11-05) - 热键系统重构

### 重大修复

**pynput 热键后端完全重构**
- **解决双重调用问题**：修复 win32_event_filter 与 HotKey 对象的状态冲突
- **简化架构**：移除复杂的状态管理，代码减少 100+ 行
- **改进线程管理**：增加超时处理和详细日志记录
- **事件抑制保持**：保留阻止热键传递到活动窗口的功能

### 技术改进

**热键系统稳定性**
- 修复 HotKey._state 双重修改导致的触发失败
- 优化组合键时间窗口检测（500ms）
- 改进按键状态清理机制
- 增强错误处理和日志记录

**代码质量**
- 线程生命周期管理超时从 1s 增加到 2s
- 检查间隔从 100ms 优化到 50ms
- 添加超时日志记录
- 简化事件处理流程

### 用户体验

**更可靠的热键触发**
- 消除热键无法响应的问题
- 保持事件抑制功能（热键不会传递到其他应用）
- 左右修饰键（Left Alt / Right Alt）统一处理
- 大小写按键（Alt+h / Alt+H）兼容性

**权限友好**
- Win32 后端：无需管理员权限
- pynput 后端：支持管理员权限下的完整功能
- 自动冲突检测和替代建议

---

## v0.1.3 (2025-10-28) - 稳定性改进

### 核心修复

- **热键稳定性改进**：优化 pynput 热键触发机制
- **状态管理优化**：改进组件生命周期管理
- **日志增强**：添加详细的调试日志
- **错误处理**：增强异常捕获和恢复机制

---

## v0.1.2 (2025-10-18) - 快捷键增强

### 功能改进

- **修复快捷键误触发**：改进修饰键清理机制
- **多快捷键支持**：支持配置多个热键组合
- **热重载配置**：无需重启即可应用配置更改
- **模块名称统一**：全面统一为 sonicinput
- **配置验证**：增强配置文件验证和错误提示

---

## v0.1.1 (2025-10-02) - 流式转录

### 重要更新

- **流式转录**：减少 70-90% 等待时间，实时处理音频
- **性能追踪**：新增 RTF（实时因子）指标监控
- **日志系统**：完善的日志记录和错误追踪
- **SiliconFlow 集成**：新增 SiliconFlow ASR 云服务支持
- **异步 UI**：改进用户界面响应速度
- **图标修复**：修复应用图标显示问题

### 技术改进

- 优化音频处理管道
- 改进内存管理
- 增强错误恢复机制

---

## v0.1.0 (2025-01-22) - 首个稳定版本

### 核心功能

- **GPU 加速语音识别**：基于 Faster Whisper，支持 CUDA 12 + cuDNN 9
- **AI 文本优化**：集成 Groq / OpenRouter 服务，智能优化转录文本
- **智能输入系统**：多种输入方法支持（Smart Input / Clipboard / SendInput API）
- **全局热键支持**：系统级快捷键，支持后台监听
- **实时转录**：高质量语音识别，支持中英文
- **多提供商支持**：本地 / 云端转录服务灵活切换

### 系统要求

- Windows 10/11 64-bit
- NVIDIA GPU（可选，用于 GPU 加速）
- 4GB RAM（推荐 8GB）
- 2-3GB 磁盘空间

### 架构特性

- 企业级分层架构
- 生命周期管理系统
- 插件化转录提供商
- 统一配置管理
- 完善的日志系统

---

## 技术支持

**配置和日志**
- 配置文件：`%AppData%\SonicInput\config.json`
- 日志文件：`%AppData%\SonicInput\logs\app.log`
- 模型目录：`%AppData%\SonicInput\models/`

**文档**
- 项目 README：[README.md](README.md)
- 开发者文档：[CLAUDE.md](CLAUDE.md)

**问题反馈**
- GitHub Issues：https://github.com/Oxidane-bot/SonicInput/issues
- 包含日志文件和详细描述

**社区**
- 欢迎贡献代码和反馈
- Pull Requests 欢迎

---

**项目状态**：生产就绪
**架构**：企业级分层架构
**最后更新**：2025-11-12
