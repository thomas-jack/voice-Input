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

- 🎤 **实时语音输入**: 边说边输入，支持会议记录、快速笔记
- 🔄 **智能剪贴板恢复**: 录音前自动备份，完成后恢复原内容
- 🚀 **双模式转录**:
  - **realtime**: 实时输入文字
  - **chunked**: 支持 AI 文本优化
- 🪶 **轻量级**: 安装包仅 70MB，无需 GPU
- 🤖 **AI 优化**: 支持 Groq/OpenRouter/NVIDIA/OpenAI 等平台
- ⌨️ **全局快捷键**: F12 或 Alt+H 快速启动

## 📋 系统要求

- Windows 10/11 64位
- 推荐 4GB+ 内存
- 500MB 磁盘空间
- 无需 GPU

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
   - 双击托盘图标打开设置窗口
   - 切换到 **"转录设置"** 标签页
   - 在 **转录提供商** 下拉菜单选择 `groq`
   - 填入 API Key 并点击 **"应用"** 按钮

4. **开始使用**
   按 `F12` 或 `Alt+H` 开始录音，松开自动转录并输入

**重要提示**：
- **热键后端选择**：
  - 默认使用 `pynput` 后端，但**需要管理员权限**
  - 如果未以管理员身份运行，请在 **"热键设置"** 标签页将后端切换为 `win32`
  - Win32 后端无需管理员权限，但部分按键组合可能不可用

- **流式模式选择**（仅本地转录）：
  - 在 **"转录设置"** 标签页找到 **"流式模式"** 选项
  - `realtime`：实时输入，低延迟（推荐日常使用）
  - `chunked`：支持 AI 文本优化，但会等待全部转录完成

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
3. 双击托盘图标打开设置窗口
4. 切换到 **"转录设置"** 标签页
5. 在 **转录提供商** 下拉菜单选择 `groq`
6. 填入 API Key 并点击 **"应用"** 按钮

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

在设置窗口的 **"转录设置"** 标签页，将 **转录提供商** 改为 `local`，即可使用本地 sherpa-onnx 转录。

#### 5. （可选）配置 AI 文本优化

1. 双击托盘图标打开设置窗口
2. 切换到 **"AI 设置"** 标签页
3. 启用 **"启用 AI 优化"** 开关
4. 选择 AI 提供商（Groq/OpenRouter/NVIDIA）
5. 填入对应的 API Key
6. 点击 **"应用"** 保存

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

## 🔧 常见问题

### 快捷键不工作

**症状**：按 F12 或 Alt+H 没有反应

**排查步骤**：

1. **检查热键后端和管理员权限**（最常见原因）
   - 打开设置窗口（双击托盘图标）
   - 切换到 **"热键设置"** 标签页
   - 查看当前 **"热键后端"** 设置：
     - 如果是 `pynput` 且未以管理员身份运行 → 切换为 `win32`
     - 如果是 `win32` 且仍不工作 → 尝试管理员权限运行应用
   - 点击 **"应用"** 保存更改

2. **检查快捷键冲突**
   - 在 **"热键设置"** 标签页查看当前快捷键
   - 尝试更换为其他组合（如 `Ctrl+Shift+V`）
   - 确保没有其他应用占用相同快捷键

3. **重启应用**
   - 右键托盘图标 → **"退出"**
   - 重新启动应用

### 无法录音

**症状**：按快捷键后无录音悬浮窗或无声音

**排查步骤**：

1. **检查麦克风权限**
   - Windows 设置 → 隐私 → 麦克风
   - 确保"允许应用访问麦克风"已开启
   - 确保 Python/SonicInput 有麦克风权限

2. **检查麦克风设备**
   - 右键任务栏音量图标 → 声音设置
   - 输入设备选择正确的麦克风
   - 测试麦克风是否工作（说话时应有音���条波动）

3. **检查音频设备配置**（高级）
   - 打开设置窗口 → **"音频设置"** 标签页
   - 点击 **"刷新设备列表"**
   - 选择正确的输入设备
   - 点击 **"应用"** 保存

### Groq API 错误

**症状**：转录失败，显示 API 错误

**排查步骤**：

1. **检查 API Key**
   - 打开设置窗口 → **"转录设置"** 标签页
   - 确认 **转录提供商** 为 `groq`
   - 检查 API Key 是否正确（无多余空格）
   - 访问 [Groq Console](https://console.groq.com/keys) 重新生成

2. **检查网络连接**
   - 确保电脑可以访问 groq.com
   - 检查防火墙是否拦截应用

3. **检查免费额度**
   - 登录 Groq Console 查看 API 用量
   - 免费账号有请求速率限制

### 转录文本不准确

**症状**：识别错误或输出不完整

**解决方案**：

1. **提高录音质量**
   - 靠近麦克风清晰说话
   - 减少环境噪音

2. **启用 AI 文本优化**（本地转录模式）
   - 设置窗口 → **"AI 设置"** 标签页
   - 启用 AI 优化并配置 API Key
   - 在 **"转录设置"** 将流式模式改为 `chunked`

3. **切换转录提供商**
   - 本地模式：`local` (sherpa-onnx)
   - 云模式：`groq` / `siliconflow` / `qwen`
   - 在 **"转录设置"** 标签页切换

### 更多问题

查看 [GitHub Issues](https://github.com/Oxidane-bot/SonicInput/issues)

---

## 📁 配置文件

配置和日志位置: `%APPDATA%\SonicInput\`

- `config.json` - 应用配置
- `logs/app.log` - 运行日志
- `history/` - 转录历史和录音文件

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

