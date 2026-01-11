<div align="center">
  <img src="assets/icon.png" alt="SonicInput Icon" width="128" height="128">
  <h1>SonicInput</h1>
  <p>Lightweight Windows voice input powered by sherpa-onnx, with local/cloud ASR and optional AI post-processing.</p>
  <p><strong>Languages:</strong> <a href="README.md">中文</a> | <a href="README_EN.md">English</a></p>
</div>

## Highlights
- Ready to use: clipboard / text / GUI entry points
- No admin needed: Win32 RegisterHotKey (default F12, customizable), conflict prompts
- Two recording modes: Realtime (low latency) / Chunked (higher quality with AI)
- Small footprint: onefile ~49 MB (v0.5.7)
- Cloud & local: Groq / OpenRouter / NVIDIA / OpenAI or local sherpa-onnx

## What’s New (v0.5.7)
- Log auto-rotation: cap main log at 10MB and keep 2 backups to prevent runaway growth
- Defaults + sample config include `logging.max_log_size_mb` / `logging.max_backup_files` so limits work out of the box

## Requirements
- Windows 10/11 64-bit
- 4GB RAM+, ~500MB disk

## Quick Start
1. Download `SonicInput-v0.5.7-win64.exe` from [Releases](https://github.com/Oxidane-bot/SonicInput/releases)
2. Run the exe; default hotkey is F12 (use Alt+H or customize if it conflicts)
3. Enter cloud API keys in settings (optional) or use the local model

> Tip: keep hotkey backend on `win32` (no admin needed, fewer conflicts). Switch to `pynput` only if you must suppress key events.

## Dev Setup
```bash
git clone https://github.com/Oxidane-bot/SonicInput.git
cd SonicInput
uv sync          # install runtime deps
uv run python app.py --gui
```

## Paths
- Config: `%AppData%/SonicInput/config.json`
+- Logs: `%AppData%/SonicInput/logs/app.log`

## License
MIT License. See [LICENSE](LICENSE).
