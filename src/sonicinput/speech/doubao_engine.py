"""Doubao (ByteDance) Speech Recognition Engine - Simplified version

Cloud-based speech recognition service powered by ByteDance's Doubao large model.
Uses async task submission and polling for audio transcription.
"""

import numpy as np
import time
import threading
import requests
import wave
import io
import uuid
import base64
import json
from typing import Optional, Dict, Any, List
from ..utils import app_logger
from .cloud_base import CloudTranscriptionBase


class DoubaoEngine(CloudTranscriptionBase):
    """Doubao large model audio transcription engine - simplified version

    Features:
    - High accuracy powered by Doubao large model
    - Async task-based transcription (different from direct HTTP)
    - Intelligent text normalization
    - Punctuation restoration
    - Zero GPU dependency: Pure cloud service
    """

    # Provider metadata
    provider_id = "doubao"
    display_name = "Doubao ASR"
    description = "ByteDance cloud transcription with Chinese dialect support"
    api_endpoint = "https://openspeech.bytedance.com/api/v1/auc/submit"  # Submit endpoint

    # Doubao API endpoints
    BASE_URL = "https://openspeech.bytedance.com"
    SUBMIT_ENDPOINT = "/api/v1/auc/submit"
    QUERY_ENDPOINT = "/api/v1/auc/query"

    # Model types
    MODEL_STANDARD = "respeak.opensource.auto"  # 标准版
    MODEL_FAST = "respeak.opensource.auto"      # 极速版 (same endpoint, different cluster)

    def __init__(
        self,
        api_key: str = "",
        app_id: Optional[str] = None,
        token: Optional[str] = None,
        cluster: Optional[str] = None,
        model_type: str = "standard",
        base_url: Optional[str] = None,
    ):
        """初始化Doubao引擎

        Args:
            api_key: API密钥 (default: empty, must be set via initialize)
            app_id: 应用ID (可选，某些API需要)
            token: 访问令牌 (可选)
            cluster: 集群名称 (可选，用于极速版)
            model_type: 模型类型 ("standard" 或 "fast")
            base_url: 自定义API端点 (可选)
        """
        # Note: Doubao doesn't use super().__init__() because it has different auth
        self.api_key = api_key
        self.app_id = app_id
        self.token = token
        self.cluster = cluster
        self.model_type = model_type
        self.base_url = base_url if base_url else self.BASE_URL
        self._is_model_loaded = False
        self.device = "cloud"
        self.use_gpu = False

        # Thread safety for requests
        self._session = None
        self._session_lock = threading.RLock()

        # Performance tracking
        self._request_count = 0
        self._total_request_time = 0.0
        self._error_count = 0

    def _get_session(self) -> requests.Session:
        """Get or create HTTP session"""
        with self._session_lock:
            if self._session is None:
                self._session = requests.Session()
                self._session.headers.update({
                    "User-Agent": "SonicInput/1.4",
                    "Content-Type": "application/json",
                })
            return self._session

    def prepare_request_data(self, **kwargs) -> Dict[str, Any]:
        """准备Doubao特有的请求数据（异步任务模式）

        Args:
            **kwargs: 转录参数

        Returns:
            Doubao API请求参数
        """
        # Doubao使用异步任务模式，这里准备submit请求的数据
        request_data = {
            "app": {
                "appid": self.app_id,
                "token": self.token,
                "cluster": self.cluster,
            },
            "user": {
                "uid": "sonicinput_user",
            },
            "audio": {
                "format": "wav",
                "rate": 16000,
                "bits": 16,
                "channel": 1,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "nbest": 1,
                "continuous": True,
            }
        }

        # Add language if specified
        language = kwargs.get("language")
        if language and language != "auto":
            # Convert language codes to Doubao format if needed
            if language == "zh":
                language = "zh-CN"
            elif language == "en":
                language = "en-US"
            request_data["request"]["language"] = language

        return request_data

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析Doubao API响应为标准格式

        Note: This is called after async task completion

        Args:
            response_data: 原始API响应数据

        Returns:
            标准转录结果格式
        """
        # Doubao response format after task completion
        text = ""
        confidence = 0.0
        segments = []

        if "data" in response_data:
            data = response_data["data"]

            # Extract text from segments
            if "segments" in data:
                for i, seg in enumerate(data["segments"]):
                    seg_text = seg.get("text", "")
                    seg_start = seg.get("start_time", 0.0) / 1000.0  # Convert ms to seconds
                    seg_end = seg.get("end_time", 0.0) / 1000.0

                    if seg_text:
                        text += seg_text
                        segments.append({
                            "id": i,
                            "start": seg_start,
                            "end": seg_end,
                            "text": seg_text,
                            "avg_logprob": 0.0,  # Doubao doesn't provide this
                            "no_speech_prob": 0.0,  # Doubao doesn't provide this
                        })

            # Get overall confidence if available
            if "confidence" in data:
                confidence = data["confidence"] / 100.0  # Convert percentage to 0-1
            else:
                # Default high confidence for Doubao
                confidence = 0.9

        # Detect language from text or use default
        language = "zh"  # Default to Chinese for Doubao
        if text and any(ord(char) > 127 for char in text[:10]):
            language = "zh"
        else:
            language = "en"

        return {
            "text": text.strip(),
            "language": language,
            "confidence": confidence,
            "segments": segments,
        }

    def get_auth_headers(self) -> Dict[str, str]:
        """获取Doubao特有的认证头

        Returns:
            认证头字典
        """
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """转录音频数据（异步任务模式）

        Args:
            audio_data: 音频数据
            language: 语言代码
            temperature: 采样温度（Doubao不使用）
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            **kwargs: 其他参数

        Returns:
            转录结果
        """
        start_time = time.time()

        # Validate input
        if audio_data is None or len(audio_data) == 0:
            return {
                "text": "",
                "error": "Empty audio data",
                "provider": self.provider_id,
            }

        try:
            # Convert audio to base64 (Doubao's format)
            wav_bytes = self._numpy_to_wav_bytes(audio_data)
            audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

            # Prepare request data
            request_data = self.prepare_request_data(language=language, **kwargs)
            request_data["audio"]["data"] = audio_base64

            # Submit task
            submit_url = f"{self.base_url}{self.SUBMIT_ENDPOINT}"
            response = self._get_session().post(
                submit_url,
                json=request_data,
                timeout=30,
            )

            self._request_count += 1

            if response.status_code != 200:
                self._error_count += 1
                return {
                    "text": "",
                    "error": f"Submit failed: {response.text}",
                    "provider": self.provider_id,
                }

            submit_result = response.json()
            if submit_result.get("code") != 0:
                self._error_count += 1
                return {
                    "text": "",
                    "error": f"Submit failed: {submit_result.get('message', 'Unknown error')}",
                    "provider": self.provider_id,
                }

            task_id = submit_result.get("data", {}).get("taskid")
            if not task_id:
                return {
                    "text": "",
                    "error": "No task ID returned",
                    "provider": self.provider_id,
                }

            # Poll for result
            query_url = f"{self.base_url}{self.QUERY_ENDPOINT}"
            max_wait_time = 120  # Maximum wait time in seconds
            poll_interval = 1.0

            while time.time() - start_time < max_wait_time:
                query_response = self._get_session().post(
                    query_url,
                    json={"taskid": task_id},
                    timeout=10,
                )

                if query_response.status_code == 200:
                    query_result = query_response.json()

                    if query_result.get("code") == 0:
                        data = query_result.get("data", {})
                        status = data.get("status", "")

                        if status == "success":
                            # Parse successful result
                            processing_time = time.time() - start_time
                            audio_duration = len(audio_data) / 16000.0

                            parsed_result = self.parse_response(query_result)
                            parsed_result.update({
                                "processing_time": processing_time,
                                "duration": audio_duration,
                                "real_time_factor": processing_time / audio_duration if audio_duration > 0 else 0,
                                "provider": self.provider_id,
                            })

                            self._total_request_time += processing_time
                            return parsed_result
                        elif status == "failed":
                            self._error_count += 1
                            return {
                                "text": "",
                                "error": f"Task failed: {data.get('message', 'Unknown error')}",
                                "provider": self.provider_id,
                            }
                        elif status in ["running", "pending"]:
                            # Continue polling
                            time.sleep(poll_interval)
                            continue

                time.sleep(poll_interval)

            # Timeout
            self._error_count += 1
            return {
                "text": "",
                "error": "Transcription timeout",
                "provider": self.provider_id,
            }

        except Exception as e:
            self._error_count += 1
            app_logger.log_error(e, "doubao_transcribe")
            return {
                "text": "",
                "error": f"Transcription failed: {str(e)}",
                "provider": self.provider_id,
            }

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """加载模型（云端服务，标记为已加载即可）

        Args:
            model_name: 模型名称（Doubao不需要）

        Returns:
            True if successful
        """
        self._is_model_loaded = True
        app_logger.log_audio_event(
            "Doubao service marked as loaded",
            {"model_type": self.model_type, "provider": "doubao"}
        )
        return True

    def test_connection(self) -> Dict[str, Any]:
        """测试API连接

        Returns:
            Connection test result
        """
        if not self.token or self.token.strip() == "":
            return {
                "success": False,
                "message": "Doubao token not configured",
                "provider": self.provider_id,
            }

        # For Doubao, we can test with a very short audio
        test_audio = np.zeros(800, dtype=np.float32)  # 0.05 seconds

        try:
            result = self.transcribe(
                test_audio,
                language="zh",
                max_retries=1,
            )

            if "error" in result and result["error"]:
                return {
                    "success": False,
                    "message": f"API test failed: {result['error']}",
                    "provider": self.provider_id,
                }

            return {
                "success": True,
                "message": "Connection successful",
                "provider": self.provider_id,
                "details": {
                    "model_type": self.model_type,
                    "base_url": self.base_url,
                },
            }

        except Exception as e:
            app_logger.log_error(e, "doubao_test_connection")
            return {
                "success": False,
                "message": f"Connection test error: {str(e)}",
                "provider": self.provider_id,
            }

    def initialize(self, config: Dict[str, Any]) -> None:
        """使用配置初始化Doubao引擎

        Args:
            config: 配置字典

        Raises:
            ValueError: 无效配置
            RuntimeError: 初始化失败
        """
        # Extract configuration
        self.api_key = config.get("api_key", "")
        self.app_id = config.get("app_id", "")
        self.token = config.get("token", "")
        self.cluster = config.get("cluster", "")
        self.model_type = config.get("model_type", "standard")
        self.base_url = config.get("base_url", self.BASE_URL)

        # Validate required fields
        if not self.token or self.token.strip() == "":
            raise ValueError("Doubao token is required")

        if not self.app_id or self.app_id.strip() == "":
            raise ValueError("Doubao app_id is required")

        # Mark as loaded
        self._is_model_loaded = True

        app_logger.log_model_loading_step(
            "Doubao provider initialized",
            {
                "model_type": self.model_type,
                "base_url": self.base_url,
                "has_cluster": bool(self.cluster),
            }
        )

    def cleanup(self) -> None:
        """清理资源"""
        with self._session_lock:
            if self._session:
                self._session.close()
                self._session = None

        self._is_model_loaded = False

    def __del__(self):
        """析构函数"""
        try:
            self.cleanup()
        except Exception:
            pass