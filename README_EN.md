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

- 🎤 **Speech Recognition**: Supports local sherpa-onnx (CPU-efficient) or cloud Groq/SiliconFlow/Qwen API transcription
- 🚀 **Dual-Mode Streaming Transcription**:
  - **chunked mode**: 30-second chunk processing with AI optimization (recommended)
  - **realtime mode**: End-to-end streaming transcription with minimal latency
- ⚡ **CPU-Efficient Inference**: sherpa-onnx RTF 0.06-0.21, 30-300x performance boost
- 🪶 **Ultra-Lightweight**: Installation size only 250MB (90% reduction vs Faster Whisper)
- 🤖 **AI Text Optimization**: Integrated Groq/OpenRouter/NVIDIA/OpenAI models
- 🧠 **Think Tag Filtering**: Automatically filters AI thinking process tags (`<think>...</think>`), keeping only optimized results
- ⌨️ **Global Hotkeys**: Customizable hotkeys (default F12 or Alt+H)
- ☁️ **Lightweight Cloud Mode**: No GPU required, uses cloud APIs for speech recognition

## 📋 System Requirements

**Basic Requirements**:
- Windows 10/11
- Python 3.10+
- 2GB+ RAM

**Local Mode (sherpa-onnx)**:
- CPU-efficient inference (RTF 0.06-0.21, faster than GPU solutions)
- Recommended 4GB+ RAM (8GB+ better)
- Installation size ~250MB (90% reduction vs GPU solutions)
- Supports Paraformer (226MB) and Zipformer (112MB) models

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
   - Double-click tray icon to open settings
   - In **Speech Recognition** → **Provider**, select `groq`
   - Enter API Key and save

4. **Start Using**
   Press `F12` or `Alt+H` to start recording, release to transcribe and input automatically

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
3. Double-click tray icon to open settings
4. In **Speech Recognition** → **Provider**, select `groq`
5. Enter API Key and save

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

In settings, select **Provider** as `local` to use local sherpa-onnx transcription.

#### 5. (Optional) Configure AI Text Optimization

Open settings via system tray icon to configure AI API keys for text optimization.

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

## 📦 Dependencies

### Core Dependencies (Both Modes)

| Dependency | Version | Description |
|-----------|---------|-------------|
| **Python** | 3.10+ | Runtime environment |
| **PySide6** | ≥ 6.6.0 | GUI framework (LGPL license) |
| **pynput** | ≥ 1.7.6 | Global hotkeys |
| **pyaudio** | ≥ 0.2.13 | Audio recording |
| **groq** | ≥ 0.4.1 | Groq API client (cloud mode) |

### Local Transcription Dependencies (Local Mode Only)

| Dependency | Version | Description |
|-----------|---------|-------------|
| **sherpa-onnx** | ≥ 1.10.0 | Lightweight ONNX Runtime speech recognition engine |

**sherpa-onnx Advantages**:
- ⚡ **CPU-Efficient Inference**: RTF 0.06-0.21 (5-16x faster than real-time)
- 🚫 **No GPU Dependencies**: No CUDA/cuDNN required, pure CPU operation
- 🪶 **Small Installation**: ~250MB (90% reduction vs traditional GPU solutions)
- 📡 **Streaming Transcription**: Supports chunked and realtime dual modes

**Supported Models**:
- **Paraformer**: Bilingual Chinese-English high accuracy (226MB, recommended for accuracy)
- **Zipformer**: Ultra-lightweight English model (112MB, recommended for low-memory environments)

**Installation Methods**:
- Cloud mode: `uv sync` (core dependencies only, ~100MB)
- Local mode: `uv sync --extra local` (includes sherpa-onnx, ~250MB)

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

## 🔧 Troubleshooting

### Common Issues

**Cannot Record**:
- Check microphone permissions (Windows Settings → Privacy → Microphone)
- Confirm microphone device is enabled and set as default

**Hotkey Not Working**:
- Try running as administrator
- Change hotkey (avoid conflicts with other software)
- Check keyboard layout and input method status

**Model Download Failed** (Local Mode Only):
1. **Check network connection**, ensure GitHub is accessible
2. **Manual model download**:
   - Visit [sherpa-onnx releases](https://github.com/k2-fsa/sherpa-onnx/releases)
   - Download corresponding model files (Paraformer or Zipformer)
   - Extract to `%APPDATA%\SonicInput\models\` directory
3. **Use proxy**: If proxy access needed, set environment variables:
   ```bash
   set HTTP_PROXY=http://your-proxy:port
   set HTTPS_PROXY=http://your-proxy:port
   ```
4. **Check disk space**: Ensure at least 500MB available space

**Slow Transcription / Out of Memory**:
- **Local Mode**:
  - Switch to smaller Zipformer model (112MB vs 226MB)
  - Close other memory-intensive applications
  - Upgrade to 8GB+ RAM
- **Cloud Mode**:
  - Check network connection speed and stability
  - Try switching to other API providers

**Groq API Error** (Cloud Mode Only):
- **Invalid API Key**: Check if API Key is correct, visit [Groq Console](https://console.groq.com/keys) to regenerate
- **Quota Exhausted**: Groq free tier has limits, check console for usage
- **Network Error**: Check network connection, ensure api.groq.com is accessible
- **Rate Limit**: Wait a few minutes and retry, or upgrade API plan

**sherpa-onnx Initialization Failed** (Local Mode Only):
- Confirm local dependencies installed: `uv sync --extra local`
- Run diagnostic test: `uv run python app.py --test`
- Check log files for detailed error information
- Try re-downloading model files

### View Logs

```
C:\Users\<username>\AppData\Roaming\SonicInput\logs\app.log
```

Enable detailed logging: Settings → General → Log Level: DEBUG

---

## 📁 Data Storage Location

SonicInput creates a data folder in the user directory where all configurations and recording history are stored. **Users have full control over these files** and can freely backup, migrate, or delete them.

### Windows Default Path

```
C:\Users\<username>\AppData\Roaming\SonicInput\
```

### Directory Structure

```
SonicInput/
├── config.json              # Application configuration file (settings, API keys, etc.)
├── logs/                     # Log folder
│   └── app.log              # Application logs (adjustable log level)
└── history/                  # History folder
    ├── history.db           # SQLite database (transcription history, metadata)
    └── recordings/          # Recording file storage
        └── *.wav            # WAV format recording files
```

### File Description

| File/Folder | Content | Deletable | Note |
|------------|---------|-----------|------|
| `config.json` | Application configuration | ⚠️ Caution | Configuration resets to default after deletion |
| `logs/app.log` | Runtime logs | ✅ Yes | Auto-rotated, can be cleaned periodically |
| `history/history.db` | History metadata | ⚠️ Caution | All history lost after deletion |
| `history/recordings/*.wav` | Recording files | ✅ Yes | Keep as needed, can manually clean old files |

### Open Data Folder

**Method 1**: Using Windows Explorer
```
Win+R → Enter: %APPDATA%\SonicInput → Press Enter
```

**Method 2**: Using Command Line
```bash
explorer %APPDATA%\SonicInput
```

### Data Management Suggestions

**Backup Configuration**:
```bash
# Copy configuration file to safe location
copy "%APPDATA%\SonicInput\config.json" "D:\Backup\SonicInput_config_backup.json"
```

**Clean History**:
- Delete individual records through the in-app "History" tab
- Or directly delete old WAV files in `history/recordings/` (database will auto-clean invalid references)

**Complete Uninstall**:
1. Uninstall/delete the application
2. Manually delete data folder:
   ```bash
   rmdir /s "%APPDATA%\SonicInput"
   ```

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
