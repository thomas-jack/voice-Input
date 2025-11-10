"""配置默认值定义 - 单一职责：提供默认配置"""

from typing import Dict, Any


def get_default_config() -> Dict[str, Any]:
    """获取默认配置

    Returns:
        默认配置字典
    """
    return {
        "hotkeys": {
            "keys": ["ctrl+shift+v"],
            "backend": "auto",  # "auto", "win32", or "pynput"
        },
        "transcription": {
            "provider": "local",
            "local": {
                "model": "paraformer",  # sherpa-onnx 模型 (paraformer | zipformer-small)
                "language": "zh",  # 语言 (zh | en)
                "auto_load": True,
                "streaming_mode": "chunked",  # 流式模式 (chunked | realtime)
            },
            "groq": {
                "api_key": "",
                "model": "whisper-large-v3-turbo",
                "base_url": "https://api.groq.com/openai/v1",
                "timeout": 30,
                "max_retries": 3,
            },
            "siliconflow": {
                "api_key": "",
                "model": "FunAudioLLM/SenseVoiceSmall",
                "base_url": "https://api.siliconflow.cn/v1",
                "timeout": 30,
                "max_retries": 3,
            },
            "qwen": {
                "api_key": "",
                "model": "qwen3-asr-flash",
                "base_url": "https://dashscope.aliyuncs.com",
                "timeout": 30,
                "max_retries": 3,
                "enable_itn": True,
            },
        },
        # Legacy whisper config removed - now using sherpa-onnx under transcription.local
        "ai": {
            "provider": "openrouter",
            "enabled": True,
            "filter_thinking": True,
            "prompt": "You are a professional transcription refinement specialist. Your task is to correct and improve text that has been transcribed by an automatic speech recognition (ASR) system.\n\nYour responsibilities:\n1. Remove filler words (um, uh, like, you know, etc.) and disfluencies\n2. Correct homophones and misrecognized words to their contextually appropriate forms\n3. Fix grammatical errors and improve sentence structure\n4. Preserve the original meaning and intent of the speaker\n5. Maintain natural language flow\n\nImportant constraints:\n- Output ONLY the corrected text, nothing else\n- Do NOT add explanations, comments, or metadata\n- Do NOT change the core message or add information not present in the original\n- Maintain the speaker's tone and style",
            "timeout": 30,
            "retries": 3,
            "openrouter": {"api_key": "", "model_id": "anthropic/claude-3-sonnet"},
            "groq": {"api_key": "", "model_id": "llama-3.3-70b-versatile"},
            "nvidia": {"api_key": "", "model_id": "meta/llama-3.1-8b-instruct"},
            "openai_compatible": {
                "api_key": "",
                "base_url": "http://localhost:1234/v1",
                "model_id": "local-model",
            },
        },
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "device_id": None,
            "chunk_size": 1024,
        },
        "ui": {
            "show_overlay": True,
            "overlay_position": {
                "mode": "preset",
                "preset": "center",
                "custom": {"x": 0, "y": 0},
                "last_screen": {
                    "index": 0,
                    "name": "",
                    "geometry": "",
                    "device_pixel_ratio": 1.0,
                },
                "auto_save": True,
            },
            "overlay_always_on_top": True,
            "tray_notifications": False,
            "start_minimized": True,
            "theme_color": "cyan",
        },
        "input": {
            "preferred_method": "clipboard",
            "fallback_enabled": True,
            "auto_detect_terminal": True,
            "clipboard_restore_delay": 2.0,
            "typing_delay": 0.01,
        },
        "history": {
            "storage_path": "auto",
            "max_records": 1000,
            "auto_cleanup_days": 0,
        },
        "logging": {
            "level": "INFO",
            "console_output": True,
            "max_log_size_mb": 10,
            "keep_logs_days": 7,
            "enabled_categories": [
                "audio",
                "api",
                "ui",
                "model",
                "hotkey",
                "gpu",
                "startup",
                "error",
                "performance",
            ],
        },
        "advanced": {
            "gpu_memory_fraction": 0.8,
            "audio_processing": {
                "normalize_audio": True,
                "remove_silence": True,
                "noise_reduction": True,
            },
            "performance": {
                "preload_model": True,
                "cache_audio": False,
                "parallel_processing": False,
            },
        },
    }
