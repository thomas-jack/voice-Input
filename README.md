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

### 新手用户（推荐）

1. **下载可执行文件**
   - 访问 [Releases 页面](https://github.com/Oxidane-bot/SonicInput/releases)
   - 下载 `SonicInput-vX.X.X-win64.exe`（65MB 单文件）

2. **配置 Groq API**
   - 注册免费账号：https://console.groq.com/keys
   - 双击托盘图标打开设置 → **"转录设置"** 标签页
   - 选择 `groq` 提供商并填入 API Key → 点击 **"应用"**

3. **开始使用**
   按 `F12` 或 `Alt+H` 开始录音，松开自动转录并输入

<details>
<summary><b>重要提示</b>（点击展开）</summary>

**热键后端选择**：
- 默认 `pynput` 需要**管理员权限**
- 非管理员运行时，在 **"热键设置"** 标签页切换为 `win32`

**流式模式**（仅本地转录）：
- `realtime`：实时输入，低延迟（推荐）
- `chunked`：支持 AI 优化，等待完整转录
- 在 **"转录设置"** 标签页切换

</details>

---

### 开发者模式

**前置要求**：Python 3.10+, UV 包管理器

```powershell
# 安装 UV (Chocolatey)
choco install uv

# 或使用官方脚本
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**安装**：
```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput

# 云模式（轻量，~100MB）
uv sync

# 本地模式（离线，~250MB）
uv sync --extra local
```

**配置**：参考上方"新手用户"步骤 2-3

**启动**：
```bash
# 测试模型下载（仅本地模式首次）
uv run python app.py --test

# 启动 GUI
uv run python app.py --gui
```

<details>
<summary><b>模式对比</b>（点击展开）</summary>

| 特性 | 云模式 | 本地模式 |
|------|-------|---------|
| 安装体积 | ~100MB | ~250MB |
| 网络要求 | 需要联网 | 可离线 |
| API 费用 | Groq 免费额度 | 无 |
| 转录速度 | 取决于网络 | CPU 快 5-16 倍 |
| 隐私性 | 需上传音频 | 完全本地 |

**切换**：云→本地运行 `uv sync --extra local` 并在设置中选 `local`

</details>

<details>
<summary><b>AI 文本优化</b>（可选，点击展开）</summary>

设置窗口 → **"AI 设置"** 标签页 → 启用优化 → 选择提供商（Groq/NVIDIA/OpenRouter） → 填入 API Key

**免费服务**：
- Groq: https://console.groq.com/keys
- NVIDIA: https://build.nvidia.com
- OpenRouter: https://openrouter.ai

</details>

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

1. **检查后端权限**：设置 → **"热键设置"** → 如果是 `pynput` 且非管理员运行，切换为 `win32`
2. **检查冲突**：尝试更换快捷键组合（如 `Ctrl+Shift+V`），确保无其他应用占用

### 无法录音

1. **检查权限**：Windows 设置 → 隐私 → 麦克风 → 允许应用访问
2. **检查设备**：右键任务栏音量 → 声音设置 → 选择正确麦克风并测试

### API 错误

1. **检查 Key**：设置 → **"转录设置"** → 确认提供商为 `groq` 且 API Key 正确
2. **检查网络**：确保可访问 groq.com，检查防火墙和免费额度

<details>
<summary><b>更多问题排查</b>（点击展开）</summary>

**转录不准确**：
- 提高录音质量（靠近麦克风，减少噪音）
- 启用 AI 优化（设置 → **"AI 设置"**）
- 切换转录提供商（本地/云模式）

**完整文档**：[GitHub Issues](https://github.com/Oxidane-bot/SonicInput/issues)

</details>

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

