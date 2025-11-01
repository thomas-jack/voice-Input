<div align="center">
  <img src="assets/icon.png" alt="SonicInput Icon" width="128" height="128">
  <h1>SonicInput</h1>
  <p>基于 Whisper 和 AI 的 Windows 语音转文字输入工具，支持实时识别、GPU 加速。</p>

  <p>
    <strong>Languages:</strong>
    <a href="README.md">中文</a> |
    <a href="README_EN.md">English</a>
  </p>
</div>

## ✨ 核心功能

- 🎤 **语音识别**: 支持本地 Whisper 或云端 Groq API 转录
- 🚀 **流式转录**: 录音时自动分块处理，减少 70-90% 等待时间
- ⚡ **GPU 加速**: 本地模式支持 CUDA，转录速度提升 5-10 倍
- 🤖 **AI 文本优化**: 集成 Groq/OpenRouter/NVIDIA/OpenAI 多种模型
- 🧠 **思考过滤**: 自动过滤 AI 思考过程标签（`<think>...</think>`），只保留优化结果
- ⌨️ **全局快捷键**: 支持自定义快捷键（默认 F12 或 Alt+H）
- ☁️ **轻量云模式**: 无需 GPU，使用 Groq 云端 API 进行语音识别

## 📋 系统要求

**基础要求（云模式）**:
- Windows 10/11
- Python 3.10+
- 2GB+ RAM

**本地模式额外要求**:
- 4GB+ RAM（推荐 8GB）
- NVIDIA GPU（用于 GPU 加速）
- CUDA 12.x+（推荐 CUDA 12.1 或更高）

---

## 🚀 快速开始

### 部署方式选择

SonicInput 提供两种部署模式：

| 模式 | 优势 | 适用场景 |
|------|------|---------|
| **☁️ 云转录模式** | 安装简单、无需GPU、下载体积小（~200MB） | 初次体验、轻量使用、无GPU设备 |
| **💻 本地转录模式** | 离线可用、隐私保护、无API限制 | 长期使用、隐私要求高、有GPU设备 |

---

### 方式一：云转录模式（推荐新手）

轻量级部署，通过 Groq API 进行云端语音识别，无需下载大型模型和 CUDA 依赖。

#### 1. 安装 UV 包管理器

```powershell
# Windows (使用 Chocolatey)
choco install uv

# 或者使用官方安装脚本
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. 克隆项目并安装核心依赖

```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput
uv sync  # 仅安装核心依赖（约200MB）
```

#### 3. 配置 Groq API

1. 访问 [Groq Console](https://console.groq.com/keys) 获取免费 API Key
2. 启动应用：
   ```bash
   uv run python app.py --gui
   ```
3. 双击托盘图标打开设置
4. 在 **Speech Recognition** → **Provider** 选择 `groq`
5. 填入 API Key 并保存

#### 4. 开始使用

按 F12 开始录音，再次按下停止录音并自动转录输入。

---

### 方式二：本地转录模式（完整功能）

使用本地 Whisper 模型进行离线语音识别，支持 GPU 加速。

#### 1. 安装 UV 包管理器

```powershell
# Windows (使用 Chocolatey)
choco install uv

# 或者使用官方安装脚本
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. 克隆项目并安装完整依赖

```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput
uv sync --extra local --extra dev  # 安装本地转录和开发依赖（约2GB+）
```

#### 3. 配置 GPU 加速（可选）

**步骤 1: 检查 NVIDIA GPU**

```bash
nvidia-smi
```

确认输出显示 GPU 信息和驱动版本。

**步骤 2: 安装 CUDA Toolkit 12.x**

1. **下载 CUDA Toolkit**：https://developer.nvidia.com/cuda-downloads
   - **推荐版本**：CUDA 12.1 或更高
   - **作用**：提供 GPU 加速的基础库（cuBLAS、cuFFT 等）

2. **安装完成后验证**：
   ```bash
   nvcc --version
   ```

3. **确认 CUDA 路径**（通常自动设置）：
   ```powershell
   echo $env:CUDA_PATH
   # 输出示例: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9
   ```

**步骤 3: 验证 GPU 配置**

注意：`uv sync --extra local` 已自动安装 cuDNN 9 和 cuBLAS（通过 PyPI 的 nvidia-cudnn-cu12 和 nvidia-cublas-cu12 包）

验证 GPU 设置：

```bash
uv run python app.py --test
```

确认输出包含：
```
SUCCESS: GPU available
SUCCESS: Model loaded successfully
Transcription Time: ~0.6s (for 2s audio)
RTF (Real-Time Factor): ~0.3x
```

性能指标：GPU 加速下 RTF 通常在 0.3-0.5x（比实时快 2-3 倍）

#### 4. 启动应用

```bash
uv run python app.py --gui
```

#### 5. （可选）配置 AI 文本优化

通过系统托盘图标打开设置，配置 AI API 密钥以启用文本优化功能。

**推荐 AI 服务**（均有免费额度）:
- **Groq**: https://console.groq.com/keys
- **NVIDIA**: https://build.nvidia.com
- **OpenRouter**: https://openrouter.ai

---

### 模式对比

| 特性 | 云转录模式 | 本地转录模式 |
|------|-----------|-------------|
| 安装体积 | ~200MB | ~2GB+ |
| GPU 要求 | 无 | NVIDIA GPU + CUDA |
| 网络要求 | 需要联网 | 可离线使用 |
| API 费用 | Groq 免费额度 | 无 |
| 转录速度 | 取决于网络 | GPU加速快 2-3 倍 |
| 隐私性 | 需上传音频 | 完全本地处理 |
| 适合场景 | 初次体验、轻量使用 | 长期使用、隐私要求高 |

**切换模式**：
- 云模式 → 本地模式：运行 `uv sync --extra local --extra dev` 并安装 CUDA
- 本地模式 → 云模式：在设置中将 Provider 改为 `groq` 并配置 API Key

---

## 📦 依赖说明

### 核心依赖（两种模式共用）

| 依赖库 | 版本 | 说明 |
|-------|------|------|
| **Python** | 3.10+ | 运行环境 |
| **PySide6** | ≥ 6.6.0 | GUI 框架（LGPL许可） |
| **pynput** | ≥ 1.7.6 | 全局快捷键 |
| **pyaudio** | ≥ 0.2.13 | 音频录制 |
| **groq** | ≥ 0.4.1 | Groq API 客户端（云模式） |

### 本地转录依赖（仅本地模式）

| 依赖库 | 版本 | 说明 |
|-------|------|------|
| **faster-whisper** | ≥ 1.0.0 | Whisper 优化实现 |
| **ctranslate2** | 4.6.0 (≥4.5.0) | GPU 加速推理引擎 |
| **CUDA Toolkit** | 12.x (推荐 12.1+) | GPU 加速基础库 |
| **cuDNN** | 9.5.1 | 深度学习加速库 |

**重要兼容性说明**（仅本地模式）：
- CTranslate2 4.5.0+ **必须**使用 cuDNN 9（不兼容 cuDNN 8）
- CTranslate2 4.4.0 及以下使用 cuDNN 8.9.7
- 当前项目锁定 CTranslate2 ≥ 4.5.0，自动安装 4.6.0

**安装方式**：
- 云模式：`uv sync`（仅核心依赖，约200MB）
- 本地模式：`uv sync --extra local --extra dev`（完整依赖，约2GB+）

---

## 📖 使用说明

1. **启动**: 运行后最小化到系统托盘
2. **录音**: 按快捷键（默认 F12）开始/停止
3. **查看**: 悬浮窗显示实时波形和音量
4. **自动输入**: 停止后自动转录并输入到活动窗口

### 快捷键

- **录音切换**: F12 或 Alt+H（可自定义）
- **设置**: 双击托盘图标
- **退出**: 右键托盘图标 → Exit

---

## 🔧 故障排除

### 常见问题

**无法录音**: 检查麦克风权限（Windows 设置 → 隐私 → 麦克风）

**快捷键不工作**: 尝试管理员权限运行，或更换快捷键

**GPU 不可用**（仅本地模式）:
1. 确认已安装 CUDA Toolkit 12.x：`nvidia-smi` 检查驱动，`nvcc --version` 检查 CUDA
2. 确认依赖已安装：`uv sync --extra local`（自动安装 cuDNN 9 和 cuBLAS）
3. 运行测试验证：`uv run python app.py --test`
4. 检查日志中的具体错误信息
5. 或者切换到云模式：设置中 Provider 选择 `groq` 并配置 API Key

**转录慢**:
- 本地模式：启用 GPU 加速（CPU 模式慢 5-10 倍）或使用较小模型（如 `small`）
- 云模式：检查网络连接速度

**cuDNN 错误** (`Could not locate cudnn_ops64_9.dll`) - 仅本地模式:
- **原因**: CTranslate2 4.5.0+ 需要 cuDNN 9
- **解决**: 运行 `uv sync --extra local` 自动安装 nvidia-cudnn-cu12 包
- **验证**: 检查 `.venv\Lib\site-packages\nvidia\cudnn\bin` 目录是否存在

**cuBLAS 错误** (`Could not locate cublas64_12.dll`) - 仅本地模式:
- **原因**: 缺少 CUDA Toolkit 或路径未配置
- **解决步骤**:
  1. 安装 CUDA Toolkit 12.x（https://developer.nvidia.com/cuda-downloads）
  2. 验证安装：`nvcc --version`
  3. 检查 CUDA 路径：`echo $env:CUDA_PATH`
  4. 检查 DLL：`dir "$env:CUDA_PATH\bin\cublas*.dll"`
  5. 重启应用（`app.py` 会自动添加 CUDA 路径）

**Groq API 错误** - 仅云模式:
- **API Key 无效**: 检查 API Key 是否正确，访问 [Groq Console](https://console.groq.com/keys) 重新生成
- **配额用完**: Groq 免费额度有限，检查控制台使用情况
- **网络错误**: 检查网络连接，确认能访问 api.groq.com

**版本兼容性问题**（仅本地模式）:
| CTranslate2 版本 | CUDA 版本 | cuDNN 版本 |
|-----------------|----------|-----------|
| 4.4.0 及以下     | 12.0-12.2 | 8.9.7     |
| 4.5.0 及以上     | 12.0+     | 9.5.1     |

当前项目使用：**CTranslate2 4.6.0 + CUDA 12.x + cuDNN 9.5.1**

### 查看日志

```
C:\Users\<用户名>\AppData\Roaming\SonicInput\logs\app.log
```

启用详细日志: 设置 → General → Log Level: DEBUG

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - 优化实现
- [PySide6](https://doc.qt.io/qtforpython-6/) - GUI 框架（Qt for Python）
- [pynput](https://github.com/moses-palmer/pynput) - 全局快捷键

