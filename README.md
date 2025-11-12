<div align="center">
  <img src="assets/icon.png" alt="SonicInput Icon" width="128" height="128">
  <h1>SonicInput</h1>
  <p>基于 sherpa-onnx 的超轻量级 Windows 语音转文字输入工具，支持双模式流式转录和 AI 优化。</p>

  <p>
    <strong>Languages:</strong>
    <a href="README.md">中文</a> |
    <a href="README_EN.md">English</a>
  </p>
</div>

## ✨ 核心功能

- 🎤 **语音识别**: 支持本地 sherpa-onnx（CPU 高效）或云端 Groq/SiliconFlow/Qwen API 转录
- 🚀 **双模式流式转录**:
  - **chunked 模式**: 30秒分块处理，支持 AI 优化（推荐）
  - **realtime 模式**: 边到边流式转录，最低延迟
- ⚡ **CPU 高效推理**: sherpa-onnx RTF 0.06-0.21，性能提升 30-300 倍
- 🪶 **超轻量级**: 安装体积仅 250MB（比 Faster Whisper 减少 90%）
- 🤖 **AI 文本优化**: 集成 Groq/OpenRouter/NVIDIA/OpenAI 多种模型
- 🧠 **思考过滤**: 自动过滤 AI 思考过程标签（`<think>...</think>`），只保留优化结果
- ⌨️ **全局快捷键**: 支持自定义快捷键（默认 F12 或 Alt+H）
- ☁️ **轻量云模式**: 无需 GPU，使用云端 API 进行语音识别

## 📋 系统要求

**基础要求**:
- Windows 10/11
- Python 3.10+
- 2GB+ RAM

**本地模式（sherpa-onnx）**:
- CPU 高效推理（RTF 0.06-0.21，比 GPU 方案更快）
- 推荐 4GB+ RAM（8GB+ 更佳）
- 安装体积约 250MB（比 GPU 方案减少 90%）
- 支持 Paraformer（226MB）和 Zipformer（112MB）模型

---

## 🚀 快速开始

### 方式零：直接下载可执行文件（最简单）

**推荐新手** - 无需安装 Python 环境，下载即用。

1. **下载最新版本**
   访问 [Releases 页面](https://github.com/Oxidane-bot/SonicInput/releases) 下载 `SonicInput-vX.X.X-win64.exe`

2. **运行程序**
   双击 exe 文件即可启动，首次运行会自动创建配置文件

3. **配置 Groq API**（必需）
   - 注册免费账号：https://console.groq.com/keys
   - 双击托盘图标打开设置
   - 在 **Speech Recognition** → **Provider** 选择 `groq`
   - 填入 API Key 并保存

4. **开始使用**
   按 `F12` 或 `Alt+H` 开始录音，松开自动转录并输入

**特点**：
- ✅ 65MB 单文件，无需安装
- ✅ 纯云模式，无需 GPU
- ✅ 支持 Windows 10/11 (64-bit)
- ✅ 需要网络连接

---

### 部署方式选择（开发者模式）

SonicInput 提供两种部署模式：

| 模式 | 优势 | 适用场景 |
|------|------|---------|
| **☁️ 云转录模式** | 安装简单、无需下载模型、体积小（~100MB） | 初次体验、轻量使用、网络稳定 |
| **💻 本地转录模式** | 离线可用、隐私保护、无API限制、CPU高效 | 长期使用、隐私要求高、离线环境 |

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

### 方式二：本地转录模式（离线可用）

使用本地 sherpa-onnx 模型进行离线语音识别，CPU 高效推理。

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
uv sync --extra local --extra dev  # 安装本地转录和开发依赖（约250MB）
```

#### 3. 首次启动（自动下载模型）

```bash
uv run python app.py --test
```

首次启动会自动下载 Paraformer 模型（226MB）到 `%APPDATA%/SonicInput/models/`。

确认输出包含：
```
Model download completed
Model loaded successfully
Transcription Time: ~0.1s (for 2s audio)
RTF (Real-Time Factor): ~0.06-0.21
```

性能指标：sherpa-onnx CPU 推理 RTF 通常在 0.06-0.21（比实时快 5-16 倍）

#### 4. 启动应用

```bash
uv run python app.py --gui
```

在设置中选择 **Provider** 为 `local`，即可使用本地 sherpa-onnx 转录。

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
| 安装体积 | ~100MB | ~250MB |
| GPU 要求 | 无 | 无（CPU 高效） |
| 网络要求 | 需要联网 | 可离线使用 |
| API 费用 | Groq 免费额度 | 无 |
| 转录速度 | 取决于网络 | CPU 快 5-16 倍 |
| 隐私性 | 需上传音频 | 完全本地处理 |
| 适合场景 | 初次体验、轻量使用 | 长期使用、隐私要求高 |

**切换模式**：
- 云模式 → 本地模式：运行 `uv sync --extra local` 并在设置中选择 `local`
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
| **sherpa-onnx** | ≥ 1.10.0 | 轻量级 ONNX Runtime 语音识别引擎 |

**sherpa-onnx 优势**：
- ⚡ **CPU 高效推理**: RTF 0.06-0.21（比实时快 5-16 倍）
- 🚫 **无 GPU 依赖**: 无需 CUDA/cuDNN，纯 CPU 运行
- 🪶 **安装体积小**: 约 250MB（比传统 GPU 方案减少 90%）
- 📡 **流式转录**: 支持 chunked 和 realtime 双模式

**支持的模型**：
- **Paraformer**: 中英双语高精度（226MB，推荐用于准确性）
- **Zipformer**: 超轻量级英文模型（112MB，推荐用于低内存环境）

**安装方式**：
- 云模式：`uv sync`（仅核心依赖，约 100MB）
- 本地模式：`uv sync --extra local`（包含 sherpa-onnx，约 250MB）

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

**无法录音**:
- 检查麦克风权限（Windows 设置 → 隐私 → 麦克风）
- 确认麦克风设备已启用并设为默认设备

**快捷键不工作**:
- 尝试管理员权限运行应用
- 更换快捷键（避免与其他软件冲突）
- 检查键盘布局和输入法状态

**模型下载失败**（仅本地模式）:
1. **检查网络连接**，确认能访问 GitHub
2. **手动下载模型**：
   - 访问 [sherpa-onnx releases](https://github.com/k2-fsa/sherpa-onnx/releases)
   - 下载对应模型文件（Paraformer 或 Zipformer）
   - 解压到 `%APPDATA%\SonicInput\models\` 目录
3. **使用代理**: 如需代理访问，设置环境变量：
   ```bash
   set HTTP_PROXY=http://your-proxy:port
   set HTTPS_PROXY=http://your-proxy:port
   ```
4. **检查磁盘空间**: 确保至少有 500MB 可用空间

**转录慢/内存不足**:
- **本地模式**:
  - 切换到更小的 Zipformer 模型（112MB vs 226MB）
  - 关闭其他占用内存的应用
  - 升级到 8GB+ RAM
- **云模式**:
  - 检查网络连接速度和稳定性
  - 尝试切换到其他 API 提供商

**Groq API 错误**（仅云模式）:
- **API Key 无效**: 检查 API Key 是否正确，访问 [Groq Console](https://console.groq.com/keys) 重新生成
- **配额用完**: Groq 免费额度有限，检查控制台使用情况
- **网络错误**: 检查网络连接，确认能访问 api.groq.com
- **速率限制**: 等待几分钟后重试，或升级 API 套餐

**sherpa-onnx 初始化失败**（仅本地模式）:
- 确认已安装本地依赖：`uv sync --extra local`
- 运行诊断测试：`uv run python app.py --test`
- 检查日志文件中的详细错误信息
- 尝试重新下载模型文件

### 查看日志

```
C:\Users\<用户名>\AppData\Roaming\SonicInput\logs\app.log
```

启用详细日志: 设置 → General → Log Level: DEBUG

---

## 📁 数据存储位置

SonicInput 会在用户目录下创建数据文件夹，所有配置和录音历史都存储在这里。**用户对这些文件拥有完全控制权**，可以自由备份、迁移或删除。

### Windows 默认路径

```
C:\Users\<用户名>\AppData\Roaming\SonicInput\
```

### 目录结构

```
SonicInput/
├── config.json              # 应用配置文件（设置、API密钥等）
├── logs/                     # 日志文件夹
│   └── app.log              # 应用日志（可调整日志级别）
└── history/                  # 历史记录文件夹
    ├── history.db           # SQLite数据库（转录历史、元数据）
    └── recordings/          # 录音文件存储
        └── *.wav            # WAV格式录音文件
```

### 文件说明

| 文件/文件夹 | 内容 | 可否删除 | 说明 |
|------------|------|---------|------|
| `config.json` | 应用配置 | ⚠️ 谨慎 | 删除后配置重置为默认值 |
| `logs/app.log` | 运行日志 | ✅ 可以 | 自动轮转，可定期清理 |
| `history/history.db` | 历史记录元数据 | ⚠️ 谨慎 | 删除后丢失所有历史记录 |
| `history/recordings/*.wav` | 录音文件 | ✅ 可以 | 按需保留，可手动清理旧文件 |

### 打开数据文件夹

**方法 1**: 使用Windows资源管理器
```
Win+R → 输入：%APPDATA%\SonicInput → 回车
```

**方法 2**: 使用命令行
```bash
explorer %APPDATA%\SonicInput
```

### 数据管理建议

**备份配置**：
```bash
# 复制配置文件到安全位置
copy "%APPDATA%\SonicInput\config.json" "D:\Backup\SonicInput_config_backup.json"
```

**清理历史记录**：
- 通过应用内"History"标签页删除单条记录
- 或直接删除 `history/recordings/` 下的旧WAV文件（数据库会自动清理无效引用）

**完全卸载**：
1. 卸载/删除应用程序
2. 手动删除数据文件夹：
   ```bash
   rmdir /s "%APPDATA%\SonicInput"
   ```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) - 轻量级 ONNX 语音识别引擎
- [Paraformer](https://github.com/modelscope/FunASR) - 高精度中英双语 ASR 模型
- [k2-fsa](https://github.com/k2-fsa) - 开源语音识别框架
- [PySide6](https://doc.qt.io/qtforpython-6/) - GUI 框架（Qt for Python）
- [Groq](https://groq.com/) - 云端语音识别 API
- [pynput](https://github.com/moses-palmer/pynput) - 全局快捷键

