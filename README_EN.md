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

- 🎤 **Local Speech Recognition**: OpenAI Whisper high-precision transcription
- 🚀 **Streaming Transcription**: Automatic chunk processing during recording, reducing wait time by 70-90%
- ⚡ **GPU Acceleration**: CUDA support, 5-10x faster transcription speed
- 🤖 **AI Text Optimization**: Integrated Groq/OpenRouter/NVIDIA/OpenAI models
- 🧠 **Think Tag Filtering**: Automatically filters AI thinking process tags (`<think>...</think>`), keeping only optimized results
- ⌨️ **Global Hotkeys**: Customizable hotkeys (default F12 or Alt+H)

## 📋 System Requirements

- Windows 10/11
- Python 3.10+
- 4GB+ RAM (8GB recommended)
- NVIDIA GPU (optional, for GPU acceleration)
  - Supports CUDA 12.x+ (CUDA 12.1 or higher recommended)

---

## 🚀 Quick Start

### 1. Install UV Package Manager

```powershell
# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Dependencies

```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput
uv sync
```

### 3. (Optional) Configure GPU Acceleration

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

**Note**: `uv sync` automatically installs cuDNN 9 and cuBLAS (via nvidia-cudnn-cu12 and nvidia-cublas-cu12 packages from PyPI)

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

### 4. Start Application

```bash
uv run python app.py --gui
```

After first run, open settings via system tray icon to configure AI API keys (optional).

**Recommended AI Services** (all have free tiers):
- **Groq**: https://console.groq.com/keys
- **NVIDIA**: https://build.nvidia.com
- **OpenRouter**: https://openrouter.ai

---

## 📦 Core Dependencies

| Dependency | Version | Description |
|-----------|---------|-------------|
| **Python** | 3.10+ | Runtime environment |
| **faster-whisper** | ≥ 1.0.0 | Optimized Whisper implementation |
| **ctranslate2** | 4.6.0 (≥4.5.0) | GPU-accelerated inference engine |
| **CUDA Toolkit** | 12.x (12.1+ recommended) | GPU acceleration base libraries |
| **cuDNN** | 9.5.1 | Deep learning acceleration library |
| **PyQt6** | ≥ 6.6.0 | GUI framework |
| **pynput** | ≥ 1.7.6 | Global hotkeys |

**Important Compatibility Notes**:
- CTranslate2 4.5.0+ **requires** cuDNN 9 (incompatible with cuDNN 8)
- CTranslate2 4.4.0 and below use cuDNN 8.9.7
- Current project locks CTranslate2 ≥ 4.5.0, auto-installs 4.6.0

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

**GPU Unavailable**:
1. Confirm CUDA Toolkit 12.x installed: Check driver with `nvidia-smi`, check CUDA with `nvcc --version`
2. Confirm dependencies installed: `uv sync` (automatically installs cuDNN 9 and cuBLAS)
3. Run test to verify: `uv run python app.py --test`
4. Check logs for specific error messages

**Slow Transcription**:
- Enable GPU acceleration (CPU mode is 5-10x slower)
- Or use smaller model (e.g., `small`, but lower accuracy)

**cuDNN Error** (`Could not locate cudnn_ops64_9.dll`):
- **Cause**: CTranslate2 4.5.0+ requires cuDNN 9
- **Solution**: Run `uv sync` to auto-install nvidia-cudnn-cu12 package
- **Verify**: Check if `.venv\Lib\site-packages\nvidia\cudnn\bin` directory exists

**cuBLAS Error** (`Could not locate cublas64_12.dll`):
- **Cause**: Missing CUDA Toolkit or path not configured
- **Solution Steps**:
  1. Install CUDA Toolkit 12.x (https://developer.nvidia.com/cuda-downloads)
  2. Verify installation: `nvcc --version`
  3. Check CUDA path: `echo $env:CUDA_PATH`
  4. Check DLL: `dir "$env:CUDA_PATH\bin\cublas*.dll"`
  5. Restart app (`app.py` will automatically add CUDA path)

**Version Compatibility**:
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
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [pynput](https://github.com/moses-palmer/pynput) - Global hotkeys
