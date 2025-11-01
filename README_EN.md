<div align="center">
  <img src="assets/icon.png" alt="SonicInput Icon" width="128" height="128">
  <h1>SonicInput</h1>
  <p>Windows voice-to-text input tool based on Whisper and AI, with real-time recognition and GPU acceleration.</p>

  <p>
    <strong>Languages:</strong>
    <a href="README.md">中文</a> |
    <a href="README_EN.md">English</a>
  </p>
</div>

## ✨ Key Features

- 🎤 **Speech Recognition**: Supports local Whisper or cloud Groq API transcription
- 🚀 **Streaming Transcription**: Automatic chunk processing during recording, reducing wait time by 70-90%
- ⚡ **GPU Acceleration**: Local mode supports CUDA, 5-10x faster transcription speed
- 🤖 **AI Text Optimization**: Integrated Groq/OpenRouter/NVIDIA/OpenAI models
- 🧠 **Think Tag Filtering**: Automatically filters AI thinking process tags (`<think>...</think>`), keeping only optimized results
- ⌨️ **Global Hotkeys**: Customizable hotkeys (default F12 or Alt+H)
- ☁️ **Lightweight Cloud Mode**: No GPU required, uses Groq cloud API for speech recognition

## 📋 System Requirements

**Basic Requirements (Cloud Mode)**:
- Windows 10/11
- Python 3.10+
- 2GB+ RAM

**Additional Requirements for Local Mode**:
- 4GB+ RAM (8GB recommended)
- NVIDIA GPU (for GPU acceleration)
- CUDA 12.x+ (CUDA 12.1 or higher recommended)

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
| **☁️ Cloud Transcription Mode** | Easy installation, no GPU required, small download size (~200MB) | First-time experience, lightweight usage, no GPU device |
| **💻 Local Transcription Mode** | Offline available, privacy protection, no API limits | Long-term use, high privacy requirements, GPU device available |

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

### Option 2: Local Transcription Mode (Full Features)

Use local Whisper model for offline speech recognition with GPU acceleration support.

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
uv sync --extra local --extra dev  # Install local transcription and dev dependencies (~2GB+)
```

#### 3. Configure GPU Acceleration (Optional)

For GPU acceleration, complete the following steps:

#### Step 1: Check NVIDIA GPU

```bash
nvidia-smi
```

Confirm output shows GPU information and driver version.

#### Step 2: Install CUDA Toolkit 12.x

1. **Download CUDA Toolkit**: https://developer.nvidia.com/cuda-downloads
   - **Recommended Version**: CUDA 12.1 or higher
   - **Purpose**: Provides GPU acceleration base libraries (cuBLAS, cuFFT, etc.)

2. **Verify after installation**:
   ```bash
   nvcc --version
   ```

3. **Confirm CUDA path** (usually set automatically):
   ```powershell
   echo $env:CUDA_PATH
   # Example output: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9
   ```

#### Step 3: Verify GPU Configuration

**Note**: `uv sync --extra local` automatically installs cuDNN 9 and cuBLAS (via nvidia-cudnn-cu12 and nvidia-cublas-cu12 packages from PyPI)

**Verify GPU setup**:

```bash
uv run python app.py --test
```

**Confirm output includes**:
```
SUCCESS: GPU available
SUCCESS: Model loaded successfully
Transcription Time: ~0.6s (for 2s audio)
RTF (Real-Time Factor): ~0.3x
```

**Performance Metrics**: With GPU acceleration, RTF is typically 0.3-0.5x (2-3x faster than real-time)

#### 4. Start Application

```bash
uv run python app.py --gui
```

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
| Installation Size | ~200MB | ~2GB+ |
| GPU Requirement | None | NVIDIA GPU + CUDA |
| Network Requirement | Internet required | Offline available |
| API Cost | Groq free tier | None |
| Transcription Speed | Network dependent | GPU accelerated 2-3x faster |
| Privacy | Audio uploaded | Fully local processing |
| Use Cases | First-time experience, lightweight usage | Long-term use, high privacy requirements |

**Switching Modes**:
- Cloud → Local: Run `uv sync --extra local --extra dev` and install CUDA
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
| **faster-whisper** | ≥ 1.0.0 | Optimized Whisper implementation |
| **ctranslate2** | 4.6.0 (≥4.5.0) | GPU-accelerated inference engine |
| **CUDA Toolkit** | 12.x (12.1+ recommended) | GPU acceleration base libraries |
| **cuDNN** | 9.5.1 | Deep learning acceleration library |

**Important Compatibility Notes** (Local Mode Only):
- CTranslate2 4.5.0+ **requires** cuDNN 9 (incompatible with cuDNN 8)
- CTranslate2 4.4.0 and below use cuDNN 8.9.7
- Current project locks CTranslate2 ≥ 4.5.0, auto-installs 4.6.0

**Installation Methods**:
- Cloud mode: `uv sync` (core dependencies only, ~200MB)
- Local mode: `uv sync --extra local --extra dev` (full dependencies, ~2GB+)

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

**Cannot Record**: Check microphone permissions (Windows Settings → Privacy → Microphone)

**Hotkey Not Working**: Try running as administrator, or change hotkey

**GPU Unavailable** (Local Mode Only):
1. Confirm CUDA Toolkit 12.x installed: Check driver with `nvidia-smi`, check CUDA with `nvcc --version`
2. Confirm dependencies installed: `uv sync --extra local` (automatically installs cuDNN 9 and cuBLAS)
3. Run test to verify: `uv run python app.py --test`
4. Check logs for specific error messages
5. Or switch to cloud mode: Change Provider to `groq` in settings and configure API Key

**Slow Transcription**:
- Local mode: Enable GPU acceleration (CPU mode is 5-10x slower) or use smaller model (e.g., `small`)
- Cloud mode: Check network connection speed

**cuDNN Error** (`Could not locate cudnn_ops64_9.dll`) - Local Mode Only:
- **Cause**: CTranslate2 4.5.0+ requires cuDNN 9
- **Solution**: Run `uv sync --extra local` to auto-install nvidia-cudnn-cu12 package
- **Verify**: Check if `.venv\Lib\site-packages\nvidia\cudnn\bin` directory exists

**cuBLAS Error** (`Could not locate cublas64_12.dll`) - Local Mode Only:
- **Cause**: Missing CUDA Toolkit or path not configured
- **Solution Steps**:
  1. Install CUDA Toolkit 12.x (https://developer.nvidia.com/cuda-downloads)
  2. Verify installation: `nvcc --version`
  3. Check CUDA path: `echo $env:CUDA_PATH`
  4. Check DLL: `dir "$env:CUDA_PATH\bin\cublas*.dll"`
  5. Restart app (`app.py` will automatically add CUDA path)

**Groq API Error** - Cloud Mode Only:
- **Invalid API Key**: Check if API Key is correct, visit [Groq Console](https://console.groq.com/keys) to regenerate
- **Quota Exhausted**: Groq free tier has limits, check console for usage
- **Network Error**: Check network connection, ensure api.groq.com is accessible

**Version Compatibility** (Local Mode Only):
| CTranslate2 Version | CUDA Version | cuDNN Version |
|--------------------|--------------|---------------|
| 4.4.0 and below    | 12.0-12.2    | 8.9.7         |
| 4.5.0 and above    | 12.0+        | 9.5.1         |

Current project uses: **CTranslate2 4.6.0 + CUDA 12.x + cuDNN 9.5.1**

### View Logs

```
C:\Users\<username>\AppData\Roaming\SonicInput\logs\app.log
```

Enable detailed logging: Settings → General → Log Level: DEBUG

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Optimized implementation
- [PySide6](https://doc.qt.io/qtforpython-6/) - GUI framework (Qt for Python)
- [pynput](https://github.com/moses-palmer/pynput) - Global hotkeys
