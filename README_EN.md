<div align="center">
  <img src="assets/icon.png" alt="SonicInput Icon" width="128" height="128">
  <h1>SonicInput</h1>
  <p>Ultra-lightweight Windows voice-to-text input tool based on sherpa-onnx, supporting dual-mode streaming transcription and AI optimization.</p>

  <p>
    <strong>Languages:</strong>
    <a href="README.md">中文</a> |
    <a href="README_EN.md">English</a>
  </p>
</div>

## ✨ Key Features

- 🎤 **Real-time Voice Input**: Live text input while speaking, for meetings and quick notes
- 🔄 **Smart Clipboard Recovery**: Auto-backup before recording, auto-restore after completion
- 🚀 **Dual-Mode Transcription**:
  - **realtime**: Real-time text input
  - **chunked**: AI text optimization support
- 🪶 **Lightweight**: Only 250MB installation, no GPU required
- 🤖 **AI Optimization**: Supports Groq/OpenRouter/NVIDIA/OpenAI platforms
- ⌨️ **Global Hotkeys**: F12 or Alt+H for quick access

## 📋 System Requirements

- Windows 10/11 64-bit
- 4GB+ RAM recommended
- 500MB disk space
- No GPU required

---

## 🚀 Quick Start

### Beginners (Recommended)

1. **Download Executable**
   - Visit [Releases page](https://github.com/Oxidane-bot/SonicInput/releases)
   - Download `SonicInput-vX.X.X-win64.exe` (65MB single file)

2. **Configure Groq API**
   - Register free account: https://console.groq.com/keys
   - Double-click tray icon to open settings → **"Transcription Settings"** tab
   - Select `groq` provider and enter API Key → Click **"Apply"**

3. **Start Using**
   Press `F12` or `Alt+H` to start recording, release to transcribe and input automatically

<details>
<summary><b>Important Notes</b> (click to expand)</summary>

**Hotkey Backend Selection**:
- Default `pynput` **requires administrator privileges**
- If not running as admin, switch to `win32` in **"Hotkey Settings"** tab

**Streaming Mode** (Local transcription only):
- `realtime`: Real-time input, low latency (recommended)
- `chunked`: Supports AI optimization, waits for complete transcription
- Switch in **"Transcription Settings"** tab

</details>

---

### Developer Mode

**Prerequisites**: Python 3.10+, UV package manager

```powershell
# Install UV (Chocolatey)
choco install uv

# Or use official script
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Installation**:
```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput

# Cloud mode (lightweight, ~100MB)
uv sync

# Local mode (offline, ~250MB)
uv sync --extra local
```

**Configuration**: Refer to "Beginners" steps 2-3 above

**Launch**:
```bash
# Test model download (local mode first time only)
uv run python app.py --test

# Start GUI
uv run python app.py --gui
```

<details>
<summary><b>Mode Comparison</b> (click to expand)</summary>

| Feature | Cloud Mode | Local Mode |
|---------|-----------|------------|
| Installation Size | ~100MB | ~250MB |
| Network Requirement | Internet required | Offline available |
| API Cost | Groq free tier | None |
| Transcription Speed | Network dependent | CPU 5-16x faster |
| Privacy | Audio uploaded | Fully local |

**Switching**: Cloud→Local run `uv sync --extra local` and select `local` in settings

</details>

<details>
<summary><b>AI Text Optimization</b> (optional, click to expand)</summary>

Settings window → **"AI Settings"** tab → Enable optimization → Select provider (Groq/NVIDIA/OpenRouter) → Enter API Key

**Free services**:
- Groq: https://console.groq.com/keys
- NVIDIA: https://build.nvidia.com
- OpenRouter: https://openrouter.ai

</details>

## 📖 Usage

1. **Start**: Runs minimized to system tray
2. **Record**: Press hotkey (default F12) to start/stop
3. **View**: Floating window shows real-time waveform and volume
4. **Auto-input**: Automatically transcribes and inputs to active window after stopping

### Hotkeys

- **Record Toggle**: F12 or Alt+H (customizable)
- **Settings**: Double-click tray icon
- **Exit**: Right-click tray icon → Exit

---
## 🔧 Common Issues

### Hotkey Not Working

1. **Check backend privileges**: Settings → **"Hotkey Settings"** → If using `pynput` without admin, switch to `win32`
2. **Check conflicts**: Try different hotkey combination (e.g., `Ctrl+Shift+V`), ensure no other apps using the same key

### Cannot Record

1. **Check permissions**: Windows Settings → Privacy → Microphone → Allow apps to access
2. **Check device**: Right-click taskbar volume → Sound settings → Select correct microphone and test

### API Error

1. **Check Key**: Settings → **"Transcription Settings"** → Confirm provider is `groq` and API Key is correct
2. **Check network**: Ensure groq.com is accessible, check firewall and free quota

<details>
<summary><b>More Troubleshooting</b> (click to expand)</summary>

**Transcription Inaccurate**:
- Improve recording quality (speak close to mic, reduce noise)
- Enable AI optimization (Settings → **"AI Settings"**)
- Switch transcription provider (local/cloud mode)

**Full documentation**: [GitHub Issues](https://github.com/Oxidane-bot/SonicInput/issues)

</details>

---

## 📁 Configuration

Configuration and logs location: `%APPDATA%\SonicInput\`

- `config.json` - Application settings
- `logs/app.log` - Runtime logs
- `history/` - Transcription history and recordings

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) - Lightweight ONNX speech recognition engine
- [Paraformer](https://github.com/modelscope/FunASR) - High-accuracy bilingual Chinese-English ASR model
- [k2-fsa](https://github.com/k2-fsa) - Open-source speech recognition framework
- [PySide6](https://doc.qt.io/qtforpython-6/) - GUI framework (Qt for Python)
- [Groq](https://groq.com/) - Cloud speech recognition API
- [pynput](https://github.com/moses-palmer/pynput) - Global hotkeys
