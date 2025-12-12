<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# 🎙️ SonicInput - 企业级语音输入系统

基于 sherpa-onnx 的超轻量级 Windows 语音输入工具，采用企业级分层架构设计。

**核心功能**: 实时语音识别 | 双模式流式转录 | CPU 高效推理 | AI 文本优化 | 智能输入 | 全局热键

---

## 快速开始

```bash
# 安装依赖
uv sync

# 启动 GUI 应用
uv run python app.py --gui

# 测试和诊断
uv run python app.py --test
uv run python app.py --diagnostics
```

**配置**: `C:\Users\<用户>\AppData\Roaming\SonicInput\config.json`
**日志**: `C:\Users\<用户>\AppData\Roaming\SonicInput\logs\app.log`

---

## 架构设计

### 分层架构模式
- **控制器层**: 处理用户交互和业务流程
- **服务层**: 核心业务逻辑和数据处理
- **接口层**: Protocol 接口定义组件契约
- **基础层**: 生命周期管理和通用组件

### 关键特性

**简化生命周期管理** (v0.4.0 重构)
- 所有有状态组件继承自 `LifecycleComponent` 基类
- **3 种状态**: STOPPED → RUNNING → ERROR (vs 原 8 种状态)
- **2 个抽象方法**: `_do_start()` / `_do_stop()` (vs 原 4 个方法)
- 约 80 行核心代码 (vs 原 367 行)
- 移除线程锁、健康检查等过度设计特性

**轻量级依赖注入容器** (v0.4.0 重构)
- EnhancedDIContainer 简化到约 150 行 (vs 原 1151 行)
- **3 个核心职责**:
  1. 服务注册 (`register()`)
  2. 单例管理 (`_singletons`)
  3. 依赖解析 (`_create()`)
- 移除作用域管理、装饰器系统、生命周期管理、循环依赖检测

**回调式配置热重载** (v0.4.0 重构)
- HotReloadManager 约 50 行 (vs 原 594 行 ConfigReloadCoordinator)
- 简单回调模式代替拓扑排序和两阶段提交
- 硬编码服务重载顺序 (5 行代码)
- 失败时提示重启应用 (2 秒启动时间)
- 保存前验证关键配置项 (音频设备 ID、热键格式)
- 模型下载进度对话框 (QProgressDialog)

**插件化架构**
- 支持多种转录提供商（本地 sherpa-onnx/Groq/SiliconFlow/Qwen）
- 可扩展的 AI 客户端系统
- 模块化的输入方法支持
- **接口系统简化**: 保留 3 个多实现接口 (ISpeechService, IAIClient, IInputService)

**双模式流式转录系统**
- **chunked 模式**:
  - 本地提供商（sherpa-onnx）：30秒分块处理，支持 AI 文本优化
  - 云提供商（Groq/SiliconFlow/Qwen）：15秒分块发送，避免 API rate limit
  - 配置项：`audio.streaming.chunk_duration`（默认15秒）
  - 后台异步转录，结果按ID顺序拼接
- **realtime 模式**:
  - 仅本地提供商支持
  - 边到边流式转录，最低延迟（利用 sherpa-onnx 流式 API）
- 减少 70-90% 等待时间
- 上下文管理器确保 sherpa-onnx 会话正确清理

---

## 项目结构

```
src/sonicinput/
├── core/                           # 核心系统架构
│   ├── base/                       # 基础组件
│   │   └── lifecycle_component.py  # 简化生命周期基类 (80行)
│   ├── controllers/                # 控制器层
│   │   ├── recording_controller.py         # 录音控制 (100行)
│   │   ├── streaming_mode_manager.py       # 流式模式管理 (80行)
│   │   ├── audio_callback_router.py        # 音频回调路由 (60行)
│   │   ├── transcription_controller.py
│   │   ├── ai_processing_controller.py
│   │   └── input_controller.py
│   ├── interfaces/                 # 接口定义 (仅保留3个多实现接口)
│   │   ├── speech.py               # ISpeechService (4实现)
│   │   ├── ai.py                   # IAIClient (4实现)
│   │   └── input.py                # IInputService (2实现)
│   ├── services/                   # 服务层
│   │   ├── config/                 # 配置管理系统
│   │   │   ├── config_service_refactored.py
│   │   │   └── config_keys.py      # 类型安全配置常量
│   │   ├── hot_reload_manager.py   # 回调式热重载 (50行)
│   │   ├── state_manager.py
│   │   ├── streaming_coordinator.py # 带资源管理
│   │   └── transcription_service_refactored.py
│   ├── di_container.py             # 轻量级DI容器 (150行)
│   └── processing/                 # 处理逻辑
├── ui/                             # 用户界面系统
│   ├── components/                 # UI 组件
│   │   ├── dialogs/                # 对话框
│   │   └── system_tray/            # 系统托盘
│   ├── controllers/                # UI 控制器
│   ├── managers/                   # UI 管理器
│   ├── overlay/                    # 录音覆盖层
│   ├── overlay_components/         # 覆盖层组件
│   ├── recording_overlay_utils/    # 覆盖层工具
│   └── settings_tabs/              # 设置标签
├── audio/                          # 音频处理 (4个文件)
│   ├── recorder.py                 # 音频录制
│   ├── processor.py                # 音频处理
│   └── visualizer.py               # 音频可视化
├── speech/                         # 语音引擎 (sherpa-onnx + cloud)
│   ├── sherpa_engine.py            # sherpa-onnx 引擎
│   ├── sherpa_models.py            # 模型下载和管理
│   ├── sherpa_streaming.py         # 流式转录会话
│   ├── cloud_base.py               # 云提供商基类
│   ├── cloud_chunk_accumulator.py  # 云分块流式转录（避免rate limit）
│   ├── speech_service_factory.py   # 服务工厂
│   └── provider_info.py            # 提供商注册
├── ai/                             # AI 客户端 (8个文件)
│   ├── factory.py                  # AI 工厂
│   ├── groq.py                     # Groq 客户端
│   ├── nvidia.py                   # NVIDIA 客户端
│   ├── openrouter.py               # OpenRouter 客户端
│   └── openai_compatible.py        # OpenAI 兼容客户端
├── input/                          # 输入系统 (3个文件)
│   ├── smart_input.py              # 智能输入
│   ├── clipboard_input.py          # 剪贴板输入
│   └── sendinput.py                # SendInput API
└── utils/                          # 工具类
```

---

## 核心配置

```json
{
  "hotkeys": ["f12", "alt+h"],
  "transcription": {
    "provider": "local",
    "local": {
      "model": "paraformer",
      "language": "zh",
      "auto_load": true,
      "streaming_mode": "chunked"
    },
    "groq": {
      "api_key": "YOUR_GROQ_API_KEY_HERE",
      "model": "whisper-large-v3-turbo"
    },
    "siliconflow": {
      "api_key": "",
      "model": "FunAudioLLM/SenseVoiceSmall"
    },
    "qwen": {
      "api_key": "",
      "model": "qwen3-asr-flash"
    }
  },
  "ai": {
    "enabled": true,
    "provider": "openrouter",
    "openrouter": {
      "api_key": "",
      "model_id": "anthropic/claude-3-sonnet"
    }
  },
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "auto_stop_enabled": true,
    "max_recording_duration": 120
  },
  "logging": {
    "level": "WARNING",
    "console_output": false
  }
}
```

---

## 开发工作流

### 添加新组件

**v0.4.0 简化模式** (仅多实现服务需要接口)

```python
# 1. 有状态服务：继承 LifecycleComponent
from ..base.lifecycle_component import LifecycleComponent

class MyService(LifecycleComponent):
    """有状态服务示例"""

    def __init__(self):
        super().__init__("MyService")

    def _do_start(self) -> bool:
        """启动逻辑"""
        self._connection = create_connection()
        return True

    def _do_stop(self) -> bool:
        """停止逻辑"""
        self._connection.close()
        return True

# 2. 无状态服务：普通类（不需要继承）
class MyUtility:
    """无状态工具类示例"""

    def do_work(self, data: str) -> str:
        return f"Processed: {data}"

# 3. 多实现服务：定义Protocol接口（仅当有2+个实现时）
from typing import Protocol

class IMyPlugin(Protocol):
    """多实现插件接口（如 ISpeechService 有4个实现）"""
    def process(self, input: str) -> str: ...

# 4. 注册到DI容器
container.register("my_service", MyService)
container.register("my_utility", MyUtility)

# 5. 注册热重载回调（如果需要）
hot_reload_manager.register_callback(
    service_name="my_service",
    callback=lambda config: my_service.reload(config),
    description="Reload my service"
)
```

**设计原则** (v0.4.0):
- 有状态服务 → 继承 LifecycleComponent
- 无状态工具类 → 普通类，不需要继承
- 单一实现 → 不需要接口 (YAGNI)
- 多实现 → 定义 Protocol 接口
- 简单配置热重载 → 注册回调函数

### 代码质量检查

```bash
uv run ruff check src/      # Linting
uv run ruff check src/ --fix  # 自动修复
uv run mypy src/            # 类型检查
uv run bandit -r src/       # 安全扫描
```

**CI/CD**: GitHub Actions 运行代码质量检查，本地 Windows 环境进行功能测试。

### 调试技巧

1. **启用详细日志**: 设置中 "Log Level: DEBUG"
2. **性能监控**: 启用 "console_output" 查看 RTF 指标
3. **组件状态**: 检查生命周期管理器日志
4. **配置验证**: 使用 `--diagnostics` 检查配置

---

## 常见问题

**首次使用模型自动下载**
→ Paraformer 模型 226MB，Zipformer 模型 112MB
→ 自动从 GitHub releases 下载到 `%APPDATA%/SonicInput/models/`
→ 下载失败可手动下载后放置到对应目录

**模型加载快速**
→ sherpa-onnx CPU 推理速度快（RTF 0.06-0.21）
→ 首次加载 <1s，无需 GPU 依赖

**快捷键误触发**
→ 已实现修饰键状态清理
→ 支持多快捷键配置

**流式转录模式选择**
→ **chunked**: 支持 AI 优化（推荐）
  - 本地提供商：30秒分块
  - 云提供商：15秒分块（可配置）
→ **realtime**: 边到边流式，最低延迟（仅本地）
→ 设置中可切换：`transcription.local.streaming_mode`

**云提供商 API Rate Limit 问题**
→ **症状**: 长录音（>1分钟）转录失败，错误信息包含"rate limit"
→ **原因**: 单次请求音频过长，超过API限制
→ **解决方案**:
  1. 确认 `transcription.local.streaming_mode` 设置为 `"chunked"`
  2. 调整分块时长：`audio.streaming.chunk_duration`（默认15秒）
  3. 检查日志确认分块正确发送（每15秒一个分块）
→ **原理**: chunked模式将录音分成15秒小块，录音过程中异步发送，避免停止后一次性发送大文件

---

## 版本信息

**当前版本**: 0.5.0
**依赖管理**: uv + pyproject.toml
**GUI 框架**: PySide6 6.10.0 (LGPL)
**Python 要求**: >=3.10

### 安装选项

```bash
# 基础安装（云转录）
uv sync

# 本地转录支持
uv sync --extra local

# 完整开发环境
uv sync --extra full
```

---

**最后更新**: 2025-12-12
**状态**: 生产就绪
**架构**: 简化分层架构 (v0.4.0)

## 更新日志

### v0.5.1 (2025-12-12) - Bug 修复
**重点**: 修复 UI 渲染和流式转录问题

**Bug 修复**:
- 修复录音悬浮窗首次显示时灰色背景条渲染不完整
- 修复本地 chunked 模式文本顺序错乱问题
- 修复流式转录共享超时导致后续块等待时间不足

**改进**:
- 按 chunk_id 排序提取文本，确保顺序正确
- 每个块使用独立动态超时（基于音频长度，最少 30 秒）
- 改进超时跟踪和日志记录

### v0.5.0 (2025-12-07) - Phase 1 代码清��
**重点**: 删除死代码和未使用接口，遵循 YAGNI 原则

**代码删除** (1,323 行):
- 删除未使用接口文件:
  - `config_reload.py`: IConfigReloadable 接口及相关实现 (395 行)
  - `ui_main_service.py`: 5 个 UI 服务接口 (232 行)
- 清理服务死代码:
  - `ai_service.py`: 删除 12 个未使用方法 (~250 行)
  - `transcription_service_refactored.py`: 删除 12 个未使用方法 (~320 行)
- DI 容器简化:
  - 移除接口类型，直接使用具体类注册和解析
  - 更新 `app.py` 服务解析逻辑

**Bug 修复**:
- 配置验证: 添加 "auto" 到 hotkey backend 有效值列表
- 测试修复: UTF-8 编码支持，ConfigService 加载逻辑

**质量保证**:
- 所有自动化测试通过 (64 passed)
- GUI 手动测试验证核心功能正常
- 录音、转录、配置热重载全部正常运行

### v0.4.0 (2025-11-22) - 架构简化重构
**BREAKING CHANGES**: 统一生命周期架构重构

**代码删除** (总计 5,800+ 行, 12.3%代码库):
- 删除完全未使用代码 (~2,887行): LifecycleManager, ConfigurableContainerFactory, ConfigReloadCoordinator, 装饰器系统
- 简化过度设计代码 (~3,000行): DI容器 (1151→150行), 接口系统 (18→3个接口)

**核心架构简化**:
- **生命周期管理**: 367行→80行 (3状态, 2方法 vs 原8状态, 4方法)
- **依赖注入容器**: 1151行→150行 (保留3核心职责, 移除4非必需职责)
- **配置热重载**: 594行→50行 (回调模式代替拓扑排序和两阶段提交)
- **接口系统**: 18个接口→3个接口 (仅保留多实现接口: ISpeechService, IAIClient, IInputService)

**控制器拆分**:
- RecordingController (497行) 拆分为3个专职类 (录音控制100行 + 流式模式80行 + 回调路由60行)

**质量改进**:
- 添加配置保存前验证 (防止无效配置)
- 模型下载进度对话框 (QProgressDialog)
- StreamingCoordinator资源管理 (上下文管理器, 防止内存泄漏)
- 修复 HIGH 安全漏洞 (tarfile路径遍历)
- 替换 pkg_resources 为 importlib.metadata

**开发体验**:
- 新服务开发: 仅需实现2个方法 (vs 原4个)
- 配置热重载: 单个reload()方法 (vs 原6个方法两阶段提交)
- DI注册: 简单register()调用
- 架构复杂度: 降低80%
- 理解时间: <1天 (vs 原2-3周)

### v0.3.0 (2025-11-12)
- 完全替换 Faster Whisper 为 sherpa-onnx 轻量级引擎
- 安装体积减少 90%（250MB vs 2-3GB）
- CPU 推理性能提升 30-300 倍（RTF 0.06-0.21）
- 新增双模式流式转录支持（chunked/realtime）
- 移除所有 CUDA/GPU 依赖，纯 CPU 高效推理
- 支持 Paraformer（226MB）和 Zipformer（112MB）轻量级模型
- 新增 Qwen ASR 云服务支持
- 完成 6 阶段资源清理重构（修复内存泄漏）
- 代码净减少 1,650 行（-46%）

### v0.2.0 (2025-11-09)
- 品牌重塑为 "Sonic Input"
- 100% 品牌一致性（26 处更新覆盖 11 个文件）
- 优化 UI 界面和文档标准化

### v0.1.4 (2025-11-05)
- 修复 pynput 热键双重调用问题
- 热键系统稳定性改进

**开发提醒**: 每次修改代码到一定阶段后需要运行以下命令进行初步冒烟测试：

```bash
# 运行自动化测试（验证核心功能）
uv run python app.py --test

# 启动GUI界面（验证用户交互）
uv run python app.py --gui

# 完整诊断（可选，详细检查）
uv run python app.py --diagnostics
```

**冒烟测试流程**:
1. 代码修改完成后先运行 `--test` 确保基础功能正常
2. 然后运行 `--gui` 验证界面交互和用户体验
3. 如有问题立即修复，避免积累技术债务