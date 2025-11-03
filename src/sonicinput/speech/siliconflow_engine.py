"""硅基流动音频转录引擎

基于 SiliconFlow API 的云端语音识别服务。
支持 SenseVoiceSmall 和 TeleSpeechASR 模型，具有超低延迟和方言识别能力。
"""

import numpy as np
import time
import threading
import requests
import wave
import io
from typing import Optional, Dict, Any, List
from ..utils import app_logger
from ..core.interfaces import ISpeechService


class SiliconFlowEngine(ISpeechService):
    """硅基流动音频转录引擎

    特性:
    - 超低延迟：70ms 响应时间
    - 方言支持：40+ 中文方言
    - 情感识别：内置情感检测功能
    - 零GPU依赖：纯云端服务
    """

    # 硅基流动API端点
    BASE_URL = "https://api.siliconflow.cn/v1"
    TRANSCRIBE_ENDPOINT = "/audio/transcriptions"

    # 支持的模型列表
    AVAILABLE_MODELS = [
        "FunAudioLLM/SenseVoiceSmall",  # 50+语言，超低延迟
        "TeleAI/TeleSpeechASR",  # 40种中文方言+英语
    ]

    def __init__(
        self,
        api_key: str,
        model_name: str = "FunAudioLLM/SenseVoiceSmall",
        base_url: Optional[str] = None,
    ):
        """初始化硅基流动引擎

        Args:
            api_key: 硅基流动API密钥
            model_name: 模型名称，默认使用 SenseVoiceSmall
            base_url: 可选的自定义API端点 (例如用于代理或兼容服务)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url if base_url else self.BASE_URL
        self._is_model_loaded = False
        self.device = "cloud"  # 云端服务，标识为 "cloud"

        # 请求会话，复用连接
        self._session = None
        self._session_lock = threading.RLock()

        # 性能统计
        self._request_count = 0
        self._total_request_time = 0.0
        self._error_count = 0

        # 验证模型名称
        if model_name not in self.AVAILABLE_MODELS:
            app_logger.log_audio_event(
                "Invalid model name, using default",
                {
                    "requested_model": model_name,
                    "default_model": self.AVAILABLE_MODELS[0],
                },
            )
            self.model_name = self.AVAILABLE_MODELS[0]

        app_logger.log_audio_event(
            "SiliconFlow engine initialized",
            {
                "model_name": self.model_name,
                "api_endpoint": f"{self.base_url}{self.TRANSCRIBE_ENDPOINT}",
                "custom_base_url": base_url is not None,
            },
        )

    def _get_session(self) -> requests.Session:
        """获取或创建HTTP会话"""
        with self._session_lock:
            if self._session is None:
                self._session = requests.Session()
                self._session.headers.update(
                    {
                        "Authorization": f"Bearer {self.api_key}",
                        "User-Agent": "SonicInput/1.4",
                    }
                )
            return self._session

    def _numpy_to_wav_bytes(
        self, audio_data: np.ndarray, sample_rate: int = 16000
    ) -> bytes:
        """将numpy音频数据转换为WAV格式字节

        Args:
            audio_data: 音频数据 (numpy数组)
            sample_rate: 采样率，默认16000Hz

        Returns:
            WAV格式的字节数据
        """
        # 确保音频数据是float32格式
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # 转换为16位整数
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # 创建内存中的WAV文件
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())

            return wav_buffer.getvalue()

    def _handle_api_error(self, response: requests.Response) -> Dict[str, Any]:
        """处理API错误响应

        Args:
            response: HTTP响应对象

        Returns:
            包含错误信息的字典
        """
        self._error_count += 1

        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
        except:
            error_message = f"HTTP {response.status_code}: {response.text}"

        # 根据状态码提供具体建议
        suggestions = []
        if response.status_code == 401:
            suggestions = ["检查API密钥是否正确", "确认账户余额充足"]
        elif response.status_code == 429:
            suggestions = ["请求频率过高，请稍后重试", "考虑升级到更高层级"]
        elif response.status_code in [503, 504]:
            suggestions = ["服务暂时不可用，请稍后重试", "检查网络连接"]

        app_logger.log_error(
            Exception(f"SiliconFlow API error: {error_message}"), "siliconflow_api"
        )
        app_logger.log_audio_event(
            "API error suggestions",
            {"status_code": response.status_code, "suggestions": suggestions},
        )

        return {
            "text": "",
            "error": error_message,
            "error_code": response.status_code,
            "suggestions": suggestions,
            "provider": "siliconflow",
        }

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """转录音频数据，支持自动重试

        Args:
            audio_data: 音频数据 (numpy数组)
            language: 语言代码，None表示自动检测
            temperature: 采样温度（云端API不使用，仅为接口兼容）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            转录结果字典，包含文本、语言等信息
        """
        start_time = time.time()

        # 数据验证
        if audio_data is None or len(audio_data) == 0:
            app_logger.log_audio_event("Empty audio data provided")
            return {
                "text": "",
                "language": "unknown",
                "confidence": 0.0,
                "provider": "siliconflow",
                "error": "Empty audio data",
            }

        last_error = None
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # 转换音频格式
                wav_bytes = self._numpy_to_wav_bytes(audio_data)

                # 准备请求数据（按照官方 API 规范）
                files = {
                    "file": ("audio.wav", wav_bytes, "audio/wav")
                }

                data = {
                    "model": self.model_name
                }

                # 添加语言参数（如果指定）
                if language and language != "auto":
                    data["language"] = language

                # 发送请求
                session = self._get_session()
                url = f"{self.base_url}{self.TRANSCRIBE_ENDPOINT}"

                app_logger.log_audio_event(
                    "Sending transcription request",
                    {
                        "model": self.model_name,
                        "audio_length": len(audio_data),
                        "language": language or "auto",
                        "retry_count": retry_count,
                    },
                )

                response = session.post(url, data=data, files=files, timeout=30)

                # 更新统计信息
                request_time = time.time() - start_time
                self._request_count += 1
                self._total_request_time += request_time

                # 处理响应
                if response.status_code == 200:
                    result = response.json()
                    transcribed_text = result.get("text", "").strip()

                    # 计算性能指标
                    audio_duration = len(audio_data) / 16000  # 假设16kHz采样率
                    real_time_factor = (
                        request_time / audio_duration if audio_duration > 0 else 0
                    )

                    app_logger.log_transcription(
                        audio_length=audio_duration,
                        text=transcribed_text,
                        confidence=0.9,  # 硅基流动不提供置信度，使用默认值
                    )

                    app_logger.log_audio_event(
                        "Transcription completed",
                        {
                            "provider": "siliconflow",
                            "model": self.model_name,
                            "request_time": request_time,
                            "audio_duration": audio_duration,
                            "real_time_factor": real_time_factor,
                            "text_length": len(transcribed_text),
                            "retry_count": retry_count,
                        },
                    )

                    return {
                        "text": transcribed_text,
                        "language": language or "auto",
                        "confidence": 0.9,
                        "transcription_time": request_time,
                        "real_time_factor": real_time_factor,
                        "provider": "siliconflow",
                        "model": self.model_name,
                        "retry_count": retry_count,
                    }
                else:
                    error_result = self._handle_api_error(response)
                    last_error = error_result.get("error", "API error")

                    # 检查是否应该重试
                    if self._should_retry(
                        response.status_code, retry_count, max_retries
                    ):
                        retry_count += 1
                        app_logger.log_audio_event(
                            "Retrying transcription",
                            {
                                "status_code": response.status_code,
                                "retry_count": retry_count,
                                "max_retries": max_retries,
                                "delay": retry_delay,
                            },
                        )
                        time.sleep(retry_delay * (2 ** (retry_count - 1)))  # 指数退避
                        continue
                    else:
                        return error_result

            except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
                last_error = f"Request timeout (30s): {str(e)}"
                app_logger.log_error(e, "siliconflow_timeout")

                if retry_count < max_retries:
                    retry_count += 1
                    app_logger.log_audio_event(
                        "Retrying after timeout",
                        {
                            "retry_count": retry_count,
                            "max_retries": max_retries,
                            "delay": retry_delay * (2 ** (retry_count - 1)),
                        },
                    )
                    time.sleep(retry_delay * (2 ** (retry_count - 1)))
                    continue
                else:
                    app_logger.log_audio_event(
                        "API request failed after all retries",
                        {
                            "error": last_error,
                            "error_code": "TIMEOUT",
                            "retry_count": retry_count,
                            "max_retries": max_retries,
                        },
                    )
                    return {
                        "text": "",
                        "error": last_error,
                        "error_code": "TIMEOUT",
                        "provider": "siliconflow",
                        "retry_count": retry_count,
                    }

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                app_logger.log_error(e, "siliconflow_connection")

                if retry_count < max_retries:
                    retry_count += 1
                    app_logger.log_audio_event(
                        "Retrying after connection error",
                        {
                            "retry_count": retry_count,
                            "max_retries": max_retries,
                            "delay": retry_delay * (2 ** (retry_count - 1)),
                        },
                    )
                    time.sleep(retry_delay * (2 ** (retry_count - 1)))
                    continue
                else:
                    app_logger.log_audio_event(
                        "Connection failed after all retries",
                        {
                            "error": last_error,
                            "error_code": "CONNECTION_ERROR",
                            "retry_count": retry_count,
                            "max_retries": max_retries,
                        },
                    )
                    return {
                        "text": "",
                        "error": last_error,
                        "error_code": "CONNECTION_ERROR",
                        "provider": "siliconflow",
                        "retry_count": retry_count,
                    }

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                app_logger.log_error(e, "siliconflow_transcribe")

                # 对于非网络错误，通常重试没有帮助
                break

        # 所有重试都失败了
        return {
            "text": "",
            "error": last_error or "Unknown error",
            "error_code": "MAX_RETRIES_EXCEEDED",
            "provider": "siliconflow",
            "retry_count": retry_count,
        }

    def _should_retry(
        self, status_code: int, retry_count: int, max_retries: int
    ) -> bool:
        """判断是否应该重试请求

        Args:
            status_code: HTTP状态码
            retry_count: 当前重试次数
            max_retries: 最大重试次数

        Returns:
            是否应该重试
        """
        if retry_count >= max_retries:
            return False

        # 5xx 服务器错误通常值得重试
        if 500 <= status_code <= 599:
            return True

        # 429 速率限制值得重试
        if status_code == 429:
            return True

        # 408 请求超时值得重试
        if status_code == 408:
            return True

        # 其他错误通常重试无效
        return False

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """加载模型（云端服务，标记为已加载即可）

        Args:
            model_name: 模型名称，None表示使用当前模型

        Returns:
            是否加载成功
        """
        if model_name:
            if model_name not in self.AVAILABLE_MODELS:
                app_logger.log_audio_event(
                    "Invalid model for load_model",
                    {
                        "requested_model": model_name,
                        "available_models": self.AVAILABLE_MODELS,
                    },
                )
                return False
            self.model_name = model_name

        # 云端服务无需预加载，API 会在首次转录时验证
        self._is_model_loaded = True
        app_logger.log_audio_event(
            "Model marked as loaded (cloud service)",
            {
                "model": self.model_name,
                "provider": "siliconflow",
                "note": "API will be validated on first transcription request"
            },
        )
        return True

    def unload_model(self) -> None:
        """卸载模型（云端服务无需卸载）"""
        self._is_model_loaded = False

        # 清理会话
        with self._session_lock:
            if self._session:
                self._session.close()
                self._session = None

        app_logger.log_audio_event(
            "Model unloaded", {"model": self.model_name, "provider": "siliconflow"}
        )

    def get_available_models(self) -> List[str]:
        """获取可用的模型列表

        Returns:
            模型名称列表
        """
        return self.AVAILABLE_MODELS.copy()

    @property
    def is_model_loaded(self) -> bool:
        """模型是否已加载"""
        return self._is_model_loaded

    def get_statistics(self) -> Dict[str, Any]:
        """获取使用统计信息

        Returns:
            统计信息字典
        """
        avg_request_time = (
            self._total_request_time / self._request_count
            if self._request_count > 0
            else 0
        )

        return {
            "request_count": self._request_count,
            "error_count": self._error_count,
            "average_request_time": avg_request_time,
            "total_request_time": self._total_request_time,
            "success_rate": (self._request_count - self._error_count)
            / self._request_count
            if self._request_count > 0
            else 0,
            "model": self.model_name,
            "provider": "siliconflow",
        }

    def test_connection(self) -> bool:
        """测试API连接（使用真实转录请求）

        Returns:
            连接是否成功
        """
        try:
            # 生成 0.1 秒的静音音频用于测试
            test_audio = np.zeros(1600, dtype=np.float32)  # 0.1秒 @ 16kHz

            app_logger.log_audio_event(
                "Testing connection with real transcription",
                {"provider": "siliconflow"},
            )

            # 执行真实的转录请求（超时时间短一些）
            result = self.transcribe(
                test_audio,
                language=None,
                temperature=0.0,
                max_retries=1,
                retry_delay=1.0
            )

            # 检查是否成功
            success = "error" not in result or not result["error"]

            app_logger.log_audio_event(
                "Connection test",
                {
                    "success": success,
                    "provider": "siliconflow",
                    "error": result.get("error") if not success else None,
                },
            )

            return success
        except Exception as e:
            app_logger.log_error(e, "siliconflow_connection_test")
            return False

    def __del__(self):
        """析构函数，清理资源"""
        try:
            self.unload_model()
        except Exception:
            pass  # 析构时忽略错误
