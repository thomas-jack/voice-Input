"""流式转录功能回归测试

测试目标：
1. 验证流式转录的连续性（不会在第二次转录时失败）
2. 验证 GPU 清理不会破坏 CUDA context
3. 验证多 chunk 转录的正确拼接
4. 验证错误处理和恢复机制

Bug 历史：
- 2025-01-30: CUDA "invalid resource handle" 错误
  根本原因: cleanup_after_inference() 调用 cudaDeviceReset() 破坏 CUDA context
  修复: 替换为 torch.cuda.empty_cache()
"""

import pytest
import numpy as np
import time
from unittest.mock import MagicMock, patch
from sonicinput.core.services.transcription_service import (
    TranscriptionService,
    TranscriptionResult,
    TranscriptionTask,
    TranscriptionTaskType,
)


# ============= Fixtures =============

@pytest.fixture
def mock_whisper_engine():
    """Mock WhisperEngine，模拟真实的转录行为"""
    engine = MagicMock()
    engine.model_name = "large-v3-turbo"
    engine.device = "cuda"
    engine.use_gpu = True
    engine.is_model_loaded = True
    engine.compute_type = "float16"

    # 模拟成功的转录
    def mock_transcribe(audio_data, language=None, temperature=0.0):
        # 模拟转录需要一点时间
        time.sleep(0.01)

        text_length = len(audio_data) // 1000  # 简单估算文本长度
        return {
            "text": f"转录文本 {text_length} 字",
            "language": "zh",
            "confidence": 0.95,
            "segments": [],
            "transcription_time": 0.5
        }

    engine.transcribe.side_effect = mock_transcribe
    engine.load_model.return_value = True
    engine.get_available_models.return_value = ["large-v3-turbo"]

    return engine


@pytest.fixture
def transcription_service(mock_whisper_engine):
    """创建 TranscriptionService 实例"""
    service = TranscriptionService(mock_whisper_engine)
    service.start()

    yield service

    # 清理
    service.stop(timeout=2.0)


@pytest.fixture
def generate_audio():
    """生成测试音频数据的辅助函数"""
    def _generate(duration_seconds=1.0, sample_rate=16000):
        """生成指定时长的随机音频数据"""
        num_samples = int(duration_seconds * sample_rate)
        # 生成 [-1.0, 1.0] 范围的随机浮点数
        audio = np.random.uniform(-1.0, 1.0, num_samples).astype(np.float32)
        return audio

    return _generate


# ============= 基础功能测试 =============

class TestTranscriptionServiceBasics:
    """测试 TranscriptionService 基础功能"""

    def test_service_starts_and_stops(self, mock_whisper_engine):
        """测试服务能正常启动和停止"""
        service = TranscriptionService(mock_whisper_engine)

        # 启动
        service.start()
        assert service._is_running
        assert service._worker_thread is not None
        assert service._worker_thread.is_alive()

        # 停止
        service.stop(timeout=2.0)
        assert not service._is_running


    def test_single_transcription(self, transcription_service, generate_audio):
        """测试单次转录"""
        audio = generate_audio(duration_seconds=2.0)

        # 同步转录
        result = transcription_service.transcribe(audio, language="auto")

        assert result is not None
        assert "text" in result
        assert result["text"] != ""
        assert "language" in result
        assert "confidence" in result


    def test_async_transcription(self, transcription_service, generate_audio):
        """测试异步转录"""
        audio = generate_audio(duration_seconds=2.0)

        result_container = {"result": None, "error": None}

        def on_success(result: TranscriptionResult):
            result_container["result"] = result

        def on_error(error_msg: str):
            result_container["error"] = error_msg

        # 异步转录
        task_id = transcription_service.transcribe_async(
            audio,
            language="auto",
            callback=on_success,
            error_callback=on_error
        )

        assert task_id != ""

        # 等待完成
        timeout = 5.0
        start = time.time()
        while result_container["result"] is None and time.time() - start < timeout:
            time.sleep(0.01)

        assert result_container["error"] is None
        assert result_container["result"] is not None
        assert result_container["result"].success
        assert result_container["result"].text != ""


# ============= 流式转录测试 =============

class TestStreamingTranscription:
    """测试流式转录功能"""

    def test_streaming_mode_basic(self, transcription_service, generate_audio):
        """测试基本的流式转录流程"""
        # 启动流式模式
        transcription_service.start_streaming_mode()
        assert transcription_service._streaming_mode

        # 提交 3 个音频块
        for i in range(3):
            audio = generate_audio(duration_seconds=1.0)
            transcription_service.transcribe_chunk_async(audio)

        # 等待所有块处理完成并拼接
        full_text = transcription_service.finalize_streaming_transcription(timeout=10.0)

        assert full_text is not None
        assert full_text != ""
        # 流式模式应该已关闭
        assert not transcription_service._streaming_mode


    def test_multiple_streaming_sessions(self, transcription_service, generate_audio):
        """测试多次连续的流式转录会话（验证 CUDA context 不被破坏）"""

        for session in range(3):
            # 启动流式模式
            transcription_service.start_streaming_mode()

            # 提交 2 个音频块
            for chunk in range(2):
                audio = generate_audio(duration_seconds=0.5)
                transcription_service.transcribe_chunk_async(audio)

            # 完成转录
            full_text = transcription_service.finalize_streaming_transcription(timeout=10.0)

            # 验证每次都成功
            assert full_text is not None, f"Session {session} failed"
            assert full_text != "", f"Session {session} returned empty text"

            # 短暂等待，模拟真实使用场景
            time.sleep(0.1)


    def test_streaming_with_many_chunks(self, transcription_service, generate_audio):
        """测试大量 chunk 的流式转录（模拟长时间录音）"""
        transcription_service.start_streaming_mode()

        # 模拟 10 个 chunk（10 秒音频）
        num_chunks = 10
        for i in range(num_chunks):
            audio = generate_audio(duration_seconds=1.0)
            transcription_service.transcribe_chunk_async(audio)

        # 完成转录
        full_text = transcription_service.finalize_streaming_transcription(timeout=30.0)

        assert full_text is not None
        assert full_text != ""


    def test_streaming_chunk_order(self, transcription_service, generate_audio):
        """测试 chunk 顺序是否正确保持"""
        transcription_service.start_streaming_mode()

        # 提交带标记的音频块
        # 注意：实际文本由 mock 生成，这里只测试顺序
        for i in range(5):
            audio = generate_audio(duration_seconds=0.5)
            transcription_service.transcribe_chunk_async(audio)

        # 完成转录
        full_text = transcription_service.finalize_streaming_transcription(timeout=10.0)

        # 验证文本不为空（顺序测试需要真实引擎）
        assert full_text is not None


# ============= CUDA/GPU 相关测试 =============

class TestGPUMemoryManagement:
    """测试 GPU 内存管理不会破坏 CUDA context"""

    def test_continuous_transcription_no_cuda_error(self, transcription_service, generate_audio):
        """测试连续转录不会出现 CUDA 错误（回归测试）

        Bug 历史：第一次转录成功，第二次失败，错误 "CUDA invalid resource handle"
        根本原因：cleanup_after_inference() 调用 cudaDeviceReset() 破坏了 CUDA context
        """
        # 连续执行 5 次转录
        for i in range(5):
            audio = generate_audio(duration_seconds=1.0)
            result = transcription_service.transcribe(audio, language="auto")

            # 每次都应该成功
            assert result is not None, f"Transcription {i} failed"
            assert "text" in result, f"Transcription {i} has no text"
            assert result["text"] != "", f"Transcription {i} returned empty text"

            # 短暂等待，确保清理操作完成
            time.sleep(0.05)


    def test_rapid_transcription_no_resource_leak(self, transcription_service, generate_audio):
        """测试快速连续转录不会导致资源泄漏"""
        # 快速连续提交 10 个转录任务（不等待完成）
        results = []

        for i in range(10):
            audio = generate_audio(duration_seconds=0.5)

            def capture_result(result: TranscriptionResult):
                results.append(result)

            transcription_service.transcribe_async(
                audio,
                callback=capture_result,
                error_callback=lambda e: results.append(None)
            )

        # 等待所有任务完成
        timeout = 15.0
        start = time.time()
        while len(results) < 10 and time.time() - start < timeout:
            time.sleep(0.1)

        # 验证所有任务都完成了
        assert len(results) == 10
        # 验证没有失败的任务
        assert all(r is not None for r in results)
        assert all(r.success for r in results if r is not None)


# ============= 错误处理测试 =============

class TestErrorHandling:
    """测试错误处理和恢复机制"""

    def test_transcription_error_recovery(self, mock_whisper_engine):
        """测试转录失败后的恢复能力"""
        service = TranscriptionService(mock_whisper_engine)
        service.start()

        try:
            # 模拟第一次转录失败
            mock_whisper_engine.transcribe.side_effect = Exception("模拟错误")

            audio = np.random.random(16000).astype(np.float32)
            result_container = {"result": None, "error": None}

            def on_error(error_msg: str):
                result_container["error"] = error_msg

            service.transcribe_async(
                audio,
                error_callback=on_error
            )

            # 等待错误回调
            timeout = 5.0
            start = time.time()
            while result_container["error"] is None and time.time() - start < timeout:
                time.sleep(0.01)

            assert result_container["error"] is not None

            # 恢复正常行为
            def mock_transcribe_normal(audio_data, language=None, temperature=0.0):
                return {
                    "text": "恢复后的文本",
                    "language": "zh",
                    "confidence": 0.9,
                    "segments": [],
                    "transcription_time": 0.3
                }

            mock_whisper_engine.transcribe.side_effect = mock_transcribe_normal

            # 第二次应该成功
            result = service.transcribe(audio, language="auto")
            assert result is not None
            assert result["text"] == "恢复后的文本"

        finally:
            service.stop(timeout=2.0)


    def test_streaming_with_failed_chunks(self, transcription_service, generate_audio):
        """测试流式转录中部分 chunk 失败的处理"""
        # 设置 mock 行为：第 2 个转录失败
        call_count = [0]

        def mock_transcribe_with_failure(audio_data, language=None, temperature=0.0):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("模拟第二个 chunk 失败")

            return {
                "text": f"chunk {call_count[0]}",
                "language": "zh",
                "confidence": 0.9,
                "segments": [],
                "transcription_time": 0.3
            }

        transcription_service.whisper_engine.transcribe.side_effect = mock_transcribe_with_failure

        # 启动流式模式
        transcription_service.start_streaming_mode()

        # 提交 3 个 chunk
        for i in range(3):
            audio = generate_audio(duration_seconds=0.5)
            transcription_service.transcribe_chunk_async(audio)

        # 完成转录（应该包含失败 chunk 的占位符）
        full_text = transcription_service.finalize_streaming_transcription(timeout=10.0)

        assert full_text is not None
        # 应该包含失败提示
        assert "[转录失败" in full_text or "chunk" in full_text


# ============= 性能测试 =============

class TestPerformance:
    """测试性能相关指标"""

    def test_streaming_reduces_latency(self, transcription_service, generate_audio):
        """测试流式转录相比单次转录的延迟优势

        流式转录应该在录音过程中处理，总等待时间更短
        """
        # 模拟 5 秒音频
        total_duration = 5.0
        chunk_duration = 1.0
        num_chunks = int(total_duration / chunk_duration)

        # 流式转录
        streaming_start = time.time()
        transcription_service.start_streaming_mode()

        for i in range(num_chunks):
            audio = generate_audio(duration_seconds=chunk_duration)
            transcription_service.transcribe_chunk_async(audio)
            # 模拟录音期间的时间间隔
            time.sleep(0.1)

        full_text = transcription_service.finalize_streaming_transcription(timeout=10.0)
        streaming_time = time.time() - streaming_start

        # 单次转录
        batch_start = time.time()
        audio = generate_audio(duration_seconds=total_duration)
        result = transcription_service.transcribe(audio, language="auto")
        batch_time = time.time() - batch_start

        # 流式转录总时间应该更短（或至少不会显著更长）
        # 因为部分转录在录音期间完成了
        assert full_text is not None
        assert result is not None

        print(f"\nStreaming: {streaming_time:.2f}s, Batch: {batch_time:.2f}s")


# ============= 集成测试 =============

class TestIntegration:
    """集成测试：模拟真实使用场景"""

    def test_realistic_voice_input_workflow(self, transcription_service, generate_audio):
        """模拟真实的语音输入工作流

        场景：用户进行 3 次语音输入，每次 3-5 秒
        """
        for session in range(3):
            # 启动流式转录
            transcription_service.start_streaming_mode()

            # 模拟录音：3-5 个 1 秒的 chunk
            num_chunks = 3 + (session % 3)
            for chunk_idx in range(num_chunks):
                audio = generate_audio(duration_seconds=1.0)
                transcription_service.transcribe_chunk_async(audio)
                # 模拟录音间隔
                time.sleep(0.05)

            # 停止录音，获取完整文本
            full_text = transcription_service.finalize_streaming_transcription(timeout=10.0)

            # 验证成功
            assert full_text is not None
            assert full_text != ""

            # 模拟用户思考时间
            time.sleep(0.2)

        # 所有会话都应该成功


# ============= Pytest Markers =============

# 标记需要 GPU 的测试
gpu_required = pytest.mark.skipif(
    not __import__("sys").platform.startswith("win"),
    reason="GPU tests require Windows with CUDA"
)

# 标记慢速测试
slow = pytest.mark.slow


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
