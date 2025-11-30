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

### Option 0: Direct Download Executable (Easiest)

**Recommended for beginners** - No Python environment required, ready to use.

1. **Download Latest Version**
   Visit [Releases page](https://github.com/Oxidane-bot/SonicInput/releases) and download `SonicInput-vX.X.X-win64.exe`

2. **Run the Program**
   Double-click the exe file to start, configuration file will be created automatically on first run

3. **Configure Groq API** (Required)
   - Register for free account: https://console.groq.com/keys
   - Double-click tray icon to open settings window
   - Switch to **"Transcription Settings"** tab
   - Select `groq` in **Transcription Provider** dropdown
   - Enter API Key and click **"Apply"** button

4. **Start Using**
   Press `F12` or `Alt+H` to start recording, release to transcribe and input automatically

**Important Notes**:
- **Hotkey Backend Selection**:
  - Default uses `pynput` backend, but **requires administrator privileges**
  - If not running as administrator, switch to `win32` in **"Hotkey Settings"** tab
  - Win32 backend doesn't require admin privileges, but some key combinations may not work

- **Streaming Mode Selection** (Local transcription only):
  - Find **"Streaming Mode"** option in **"Transcription Settings"** tab
  - `realtime`: Real-time input, low latency (recommended for daily use)
  - `chunked`: Supports AI text optimization, but waits for complete transcription

**Features**:
- ✅ 65MB single file, no installation required
- ✅ Pure cloud mode, no GPU required
- ✅ Supports Windows 10/11 (64-bit)
- ✅ Internet connection required

---

### Deployment Mode Selection (Developer Mode)

SonicInput provides two deployment modes:

| Mode | Advantages | Use Cases |
|------|-----------|-----------|
| **☁️ Cloud Transcription Mode** | Easy installation, no model download, small size (~100MB) | First-time experience, lightweight usage, stable network |
| **💻 Local Transcription Mode** | Offline available, privacy protection, no API limits, CPU-efficient | Long-term use, high privacy requirements, offline environments |

---

### Option 1: Cloud Transcription Mode (Recommended for Beginners)

Lightweight deployment using Groq API for cloud speech recognition, no need to download large models and CUDA dependencies.

#### 1. Install UV Package Manager

```powershell
# Windows (using Chocolatey)
choco install uv

# Or use official installation script
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. Clone Project and Install Core Dependencies

```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput
uv sync  # Install core dependencies only (~200MB)
```

#### 3. Configure Groq API

1. Visit [Groq Console](https://console.groq.com/keys) to get free API Key
2. Start application:
   ```bash
   uv run python app.py --gui
   ```
3. Double-click tray icon to open settings window
4. Switch to **"Transcription Settings"** tab
5. Select `groq` in **Transcription Provider** dropdown
6. Enter API Key and click **"Apply"** button

#### 4. Start Using

Press F12 to start recording, press again to stop and transcribe automatically.

---

### Option 2: Local Transcription Mode (Offline Available)

Use local sherpa-onnx models for offline speech recognition with CPU-efficient inference.

#### 1. Install UV Package Manager

```powershell
# Windows (using Chocolatey)
choco install uv

# Or use official installation script
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. Clone Project and Install Full Dependencies

```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput
uv sync --extra local --extra dev  # Install local transcription and dev dependencies (~250MB)
```

#### 3. First Launch (Automatic Model Download)

```bash
uv run python app.py --test
```

First launch will automatically download Paraformer model (226MB) to `%APPDATA%/SonicInput/models/`.

Confirm output includes:
```
Model download completed
Model loaded successfully
Transcription Time: ~0.1s (for 2s audio)
RTF (Real-Time Factor): ~0.06-0.21
```

Performance metrics: sherpa-onnx CPU inference RTF typically 0.06-0.21 (5-16x faster than real-time)

#### 4. Start Application

```bash
uv run python app.py --gui
```

In settings window's **"Transcription Settings"** tab, change **Transcription Provider** to `local` to use local sherpa-onnx transcription.

#### 5. (Optional) Configure AI Text Optimization

1. Double-click tray icon to open settings window
2. Switch to **"AI Settings"** tab
3. Enable **"Enable AI Optimization"** toggle
4. Select AI provider (Groq/OpenRouter/NVIDIA)
5. Enter corresponding API Key
6. Click **"Apply"** to save

**Recommended AI Services** (all have free tiers):
- **Groq**: https://console.groq.com/keys
- **NVIDIA**: https://build.nvidia.com
- **OpenRouter**: https://openrouter.ai

---

### Mode Comparison

| Feature | Cloud Transcription Mode | Local Transcription Mode |
|---------|-------------------------|-------------------------|
| Installation Size | ~100MB | ~250MB |
| GPU Requirement | None | None (CPU-efficient) |
| Network Requirement | Internet required | Offline available |
| API Cost | Groq free tier | None |
| Transcription Speed | Network dependent | CPU 5-16x faster |
| Privacy | Audio uploaded | Fully local processing |
| Use Cases | First-time experience, lightweight usage | Long-term use, high privacy requirements |

**Switching Modes**:
- Cloud → Local: Run `uv sync --extra local` and select `local` in settings
- Local → Cloud: Change Provider to `groq` in settings and configure API Key

---

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

**Symptoms**: F12 or Alt+H has no response

**Troubleshooting Steps**:

1. **Check Hotkey Backend and Administrator Privileges** (Most common cause)
   - Open settings window (double-click tray icon)
   - Switch to **"Hotkey Settings"** tab
   - Check current **"Hotkey Backend"** setting:
     - If `pynput` and not running as administrator → Switch to `win32`
     - If `win32` and still not working → Try running app as administrator
   - Click **"Apply"** to save changes

2. **Check Hotkey Conflicts**
   - View current hotkeys in **"Hotkey Settings"** tab
   - Try changing to different combination (e.g., `Ctrl+Shift+V`)
   - Ensure no other apps are using the same hotkey

3. **Restart Application**
   - Right-click tray icon → **"Exit"**
   - Restart application

### Cannot Record

**Symptoms**: No recording overlay or no sound after pressing hotkey

**Troubleshooting Steps**:

1. **Check Microphone Permissions**
   - Windows Settings → Privacy → Microphone
   - Ensure "Allow apps to access microphone" is enabled
   - Ensure Python/SonicInput has microphone permission

2. **Check Microphone Device**
   - Right-click volume icon in taskbar → Sound settings
   - Select correct microphone as input device
   - Test if microphone works (volume bar should fluctuate when speaking)

3. **Check Audio Device Configuration** (Advanced)
   - Open settings window → **"Audio Settings"** tab
   - Click **"Refresh Device List"**
   - Select correct input device
   - Click **"Apply"** to save

### Groq API Error

**Symptoms**: Transcription fails with API error

**Troubleshooting Steps**:

1. **Check API Key**
   - Open settings window → **"Transcription Settings"** tab
   - Confirm **Transcription Provider** is `groq`
   - Check API Key is correct (no extra spaces)
   - Visit [Groq Console](https://console.groq.com/keys) to regenerate

2. **Check Network Connection**
   - Ensure computer can access groq.com
   - Check if firewall is blocking the application

3. **Check Free Quota**
   - Login to Groq Console to check API usage
   - Free accounts have rate limits

### Transcription Inaccurate

**Symptoms**: Recognition errors or incomplete output

**Solutions**:

1. **Improve Recording Quality**
   - Speak clearly close to microphone
   - Reduce ambient noise

2. **Enable AI Text Optimization** (Local transcription mode)
   - Settings window → **"AI Settings"** tab
   - Enable AI optimization and configure API Key
   - In **"Transcription Settings"** change streaming mode to `chunked`

3. **Switch Transcription Provider**
   - Local mode: `local` (sherpa-onnx)
   - Cloud mode: `groq` / `siliconflow` / `qwen`
   - Switch in **"Transcription Settings"** tab

### More Issues

Check [GitHub Issues](https://github.com/Oxidane-bot/SonicInput/issues)

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
