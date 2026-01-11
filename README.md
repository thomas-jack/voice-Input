<div align="center">
  <img src="assets/icon.png" alt="SonicInput Icon" width="128" height="128">
  <h1>SonicInput</h1>
  <p>基于 sherpa-onnx 的 Windows 语音输入工具，支持本地/云端 ASR 与 AI 后处理</p>
  <p><strong>Languages:</strong> <a href="README.md">中文</a> | <a href="README_EN.md">English</a></p>
</div>

## 核心特性
- 即开即用：剪贴板 / 文本 / GUI 多入口
- 热键无管理员：Win32 RegisterHotKey（默认 F12，可自定义），冲突时会提示
- 双模式录制：Realtime 低延迟；Chunked 精度高（AI 后处理）
- 体积小：onefile 约 49 MB（v0.5.6）
- 云端/本地切换：Groq / OpenRouter / NVIDIA / OpenAI / 本地 sherpa-onnx

## v0.5.6 更新
- 修复 Win32 热键注销/注册线程不一致导致 F12 偶发注册失败的问题
- 消息循环就绪检测更可靠，消除 “message loop not ready” 超时
- 构建脚本输出阶段耗时，便于排查打包性能
- 同步更新版本号与中英文 README

## 系统需求
- Windows 10/11 64 位
- 内存 4GB+，磁盘 500MB（onefile 体积 ~49MB）

## 快速开始
1. 下载 [Releases](https://github.com/Oxidane-bot/SonicInput/releases) 中的 `SonicInput-v0.5.6-win64.exe`
2. 双击运行，默认热键 F12（若冲突可改用 Alt+H 或自定义）
3. 在设置中填写需要的云端 API Key（可选），或直接使用本地模型

> 热键后端建议保持 `win32`（无需管理员，冲突率低）；需要按键抑制时再切换 `pynput`。

## 开发环境
```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput
uv sync          # 安装运行依赖
uv run python app.py --gui
```

## 路径
- 配置：`%AppData%/SonicInput/config.json`
- 日志：`%AppData%/SonicInput/logs/app.log`

## 许可
MIT License，详见 [LICENSE](LICENSE)。
