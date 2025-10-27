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

- 🎤 **本地语音识别**: OpenAI Whisper 高精度转录
- 🚀 **流式转录**: 录音时自动分块处理，减少 70-90% 等待时间
- ⚡ **GPU 加速**: CUDA 支持，转录速度提升 5-10 倍
- 🤖 **AI 文本优化**: 集成 Groq/OpenRouter/NVIDIA/OpenAI 多种模型
- 🧠 **思考过滤**: 自动过滤 AI 思考过程标签（`<think>...</think>`），只保留优化结果
- ⌨️ **全局快捷键**: 支持自定义快捷键（默认 F12 或 Alt+H）

## 📋 系统要求

- Windows 10/11
- Python 3.10+
- 4GB+ RAM（推荐 8GB）
- NVIDIA GPU（可选，用于 GPU 加速）
  - 支持 CUDA 12.x+（推荐 CUDA 12.1 或更高）

---

## 🚀 快速开始

### 1. 安装 UV 包管理器

```powershell
# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 安装依赖

```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput
uv sync
```

### 3. （可选）配置 GPU 加速

如需 GPU 加速，需要完成以下步骤：

#### 步骤 1: 检查 NVIDIA GPU

```bash
nvidia-smi
```

确认输出显示 GPU 信息和驱动版本。

#### 步骤 2: 安装 CUDA Toolkit 12.x

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

#### 步骤 3: 安装 cuDNN 9.x

**重要**: CTranslate2 4.5.0+ 需要 cuDNN 9（不再兼容 cuDNN 8）

运行自动化安装脚本：
```powershell
.\setup_cudnn.ps1
```

**脚本会自动**：
1. 下载 cuDNN 9.5.1 完整压缩包（~750MB）
2. 解压并提取 8 个 DLL 文件
3. 复制到虚拟环境的 ctranslate2 目录
4. 验证安装成功

**安装的 DLL 文件**：
- cudnn64_9.dll
- cudnn_ops64_9.dll
- cudnn_adv64_9.dll
- cudnn_cnn64_9.dll
- cudnn_engines_precompiled64_9.dll
- cudnn_engines_runtime_compiled64_9.dll
- cudnn_graph64_9.dll
- cudnn_heuristic64_9.dll

**注意事项**：
- ctranslate2 预编译包不包含完整的 cuDNN 和 cuBLAS 库
- 必须同时安装 CUDA Toolkit（cuBLAS）和 cuDNN（深度学习加速）
- `app.py` 会自动添加 CUDA 路径到 PATH

#### 步骤 4: 验证安装

```bash
uv run python app.py --test
```

**确认输出包含**：
```
SUCCESS: GPU available
SUCCESS: Model loaded successfully
Transcription Time: ~0.6s (for 2s audio)
RTF (Real-Time Factor): ~0.3x
```

**性能指标**：GPU 加速下 RTF 通常在 0.3-0.5x（比实时快 2-3 倍）

### 4. 启动应用

```bash
uv run python app.py --gui
```

首次运行后，通过系统托盘图标打开设置，配置 AI API 密钥（可选）。

**推荐 AI 服务**（均有免费额度）:
- **Groq**: https://console.groq.com/keys
- **NVIDIA**: https://build.nvidia.com
- **OpenRouter**: https://openrouter.ai

---

## 📦 核心依赖版本

| 依赖库 | 版本 | 说明 |
|-------|------|------|
| **Python** | 3.10+ | 运行环境 |
| **faster-whisper** | ≥ 1.0.0 | Whisper 优化实现 |
| **ctranslate2** | 4.6.0 (≥4.5.0) | GPU 加速推理引擎 |
| **CUDA Toolkit** | 12.x (推荐 12.1+) | GPU 加速基础库 |
| **cuDNN** | 9.5.1 | 深度学习加速库 |
| **PyQt6** | ≥ 6.6.0 | GUI 框架 |
| **pynput** | ≥ 1.7.6 | 全局快捷键 |

**重要兼容性说明**：
- CTranslate2 4.5.0+ **必须**使用 cuDNN 9（不兼容 cuDNN 8）
- CTranslate2 4.4.0 及以下使用 cuDNN 8.9.7
- 当前项目锁定 CTranslate2 ≥ 4.5.0，自动安装 4.6.0

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

**GPU 不可用**:
1. 确认已安装 CUDA Toolkit 12.x：`nvidia-smi` 检查驱动，`nvcc --version` 检查 CUDA
2. 确认已安装 cuDNN 9：运行 `.\setup_cudnn.ps1`
3. 运行测试验证：`uv run python app.py --test`
4. 检查日志中的具体错误信息

**转录慢**:
- 启用 GPU 加速（CPU 模式慢 5-10 倍）
- 或使用较小模型（如 `small`，但准确率降低）

**cuDNN 错误** (`Could not locate cudnn_ops64_9.dll`):
- **原因**: CTranslate2 4.5.0+ 需要 cuDNN 9（不再支持 cuDNN 8）
- **解决**: 运行安装脚本：
  ```powershell
  .\setup_cudnn.ps1
  ```
- **验证**: 检查虚拟环境中是否有 8 个 `cudnn*_9.dll` 文件

**cuBLAS 错误** (`Could not locate cublas64_12.dll`):
- **原因**: 缺少 CUDA Toolkit 或路径未配置
- **解决步骤**:
  1. 安装 CUDA Toolkit 12.x（https://developer.nvidia.com/cuda-downloads）
  2. 验证安装：`nvcc --version`
  3. 检查 CUDA 路径：`echo $env:CUDA_PATH`
  4. 检查 DLL：`dir "$env:CUDA_PATH\bin\cublas*.dll"`
  5. 重启应用（`app.py` 会自动添加 CUDA 路径）

**版本兼容性问题**:
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
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
- [pynput](https://github.com/moses-palmer/pynput) - 全局快捷键

