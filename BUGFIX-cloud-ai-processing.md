# Bug Fix: Cloud Transcription AI Processing

**Date:** 2025-11-23
**Issue:** Cloud transcription providers (Groq, SiliconFlow, Qwen) were not triggering AI optimization even when AI was enabled.

## Root Cause

In `AIProcessingController._on_transcription_completed()` (lines 105-125):

```python
should_use_ai = False  # Initialized to False

if streaming_mode == "realtime":
    should_use_ai = False
elif streaming_mode == "chunked":
    should_use_ai = self.is_ai_enabled()
# BUG: streaming_mode == "disabled" did not enter any branch
# should_use_ai remained False, AI was never triggered!
```

Cloud providers set `streaming_mode = "disabled"` (because they don't use streaming sessions), but this mode had **no explicit handling** in the AI processing logic. The variable `should_use_ai` stayed `False`, causing AI optimization to be skipped regardless of user settings.

## Fix Applied

**File:** `src/sonicinput/core/controllers/ai_processing_controller.py`

Added explicit handling for `streaming_mode == "disabled"` after line 125:

```python
elif streaming_mode == "disabled":
    # Disabled 模式（云提供商）：尊重 AI 开关
    should_use_ai = self.is_ai_enabled()
    if should_use_ai:
        app_logger.log_audio_event(
            "Disabled streaming mode (cloud provider): AI enabled, will optimize",
            {"text_length": len(text)},
        )
    else:
        app_logger.log_audio_event(
            "Disabled streaming mode (cloud provider): AI disabled, skipping",
            {"text_length": len(text)}
        )
else:
    # 未知模式：默认尊重 AI 开关（防御性编程）
    should_use_ai = self.is_ai_enabled()
    app_logger.log_audio_event(
        f"Unknown streaming_mode '{streaming_mode}': defaulting to respect AI switch",
        {"ai_enabled": should_use_ai, "text_length": len(text)}
    )
```

## Behavior After Fix

### Expected Behavior (All Providers)

| Provider    | Streaming Mode | AI Enabled | Expected Result                      |
|-------------|----------------|------------|--------------------------------------|
| local       | chunked        | ✓          | AI optimization runs                 |
| local       | chunked        | ✗          | AI optimization skipped              |
| local       | realtime       | ✓          | AI optimization **skipped** (speed priority) |
| groq        | disabled       | ✓          | AI optimization runs ✅ **FIXED**   |
| groq        | disabled       | ✗          | AI optimization skipped              |
| siliconflow | disabled       | ✓          | AI optimization runs ✅ **FIXED**   |
| siliconflow | disabled       | ✗          | AI optimization skipped              |
| qwen        | disabled       | ✓          | AI optimization runs ✅ **FIXED**   |
| qwen        | disabled       | ✗          | AI optimization skipped              |

### Logging Improvements

**Before:** No logs for cloud providers' AI processing decisions
**After:** Clear logs showing AI decision path for all modes:
- `"Disabled streaming mode (cloud provider): AI enabled, will optimize"`
- `"Disabled streaming mode (cloud provider): AI disabled, skipping"`

## Testing

✅ **Code Quality:**
- Ruff linting: All checks passed
- Smoke test: All tests passed

⏳ **Manual Testing Required:**
1. Test Groq provider with AI enabled → verify AI runs
2. Test SiliconFlow provider with AI enabled → verify AI runs
3. Test Qwen provider with AI enabled → verify AI runs
4. Check history records show `ai_status="success"` for cloud providers

## Key Clarifications

1. **Streaming Chunk Duration** setting applies to **local transcription only**, not cloud providers
2. Cloud providers **do not use streaming audio chunks** during recording (see RecordingController line 327: "Skipping streaming audio for cloud provider")
3. Cloud providers **transcribe the complete audio file** after recording ends
4. The `streaming_mode = "disabled"` name is semantically correct: it means "streaming is disabled" (not "AI is disabled")

## Impact

- **Scope:** Minimal - single file, 15 lines added
- **Risk:** Very low - only affects AI processing decision logic
- **Backwards Compatibility:** ✅ No breaking changes
- **User Impact:** 🎉 Cloud providers now respect AI settings as expected
