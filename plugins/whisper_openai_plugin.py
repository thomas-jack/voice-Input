"""Whisper OpenAI插件

演示如何创建语音识别引擎插件，扩展SonicInput的语音识别能力。
这个插件支持OpenAI Whisper API作为语音识别后端。
"""

from typing import Dict, Any, Optional, List
from sonicinput.core.interfaces import BasePlugin, PluginType, IPluginContext


class WhisperOpenAIPlugin(BasePlugin):
    """Whisper OpenAI插件

    使用OpenAI Whisper API进行语音识别的插件。
    """

    @property
    def name(self) -> str:
        """插件名称"""
        return "whisper_openai_plugin"

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"

    @property
    def description(self) -> str:
        """插件描述"""
        return "使用OpenAI Whisper API的语音识别引擎插件"

    @property
    def author(self) -> str:
        """插件作者"""
        return "SonicInput Team"

    @property
    def plugin_type(self) -> PluginType:
        """插件类型"""
        return PluginType.SPEECH_ENGINE

    @property
    def dependencies(self) -> List[str]:
        """插件依赖列表"""
        return []  # 没有强依赖，所有依赖通过配置传递

    def initialize(self, context: IPluginContext) -> bool:
        """初始化插件"""
        super().initialize(context)
        self._api_key = None
        self._model = "whisper-1"
        self._base_url = "https://api.openai.com/v1/audio/transcriptions"
        self._session = None
        self._is_available = False

        # ���试从配置中获取API密钥
        self._api_key = context.get_config("whisper_openai.api_key")
        if not self._api_key:
            self.log("No OpenAI API key found in configuration")
            return False

        self._model = context.get_config("whisper_openai.model", "whisper-1")
        self._base_url = context.get_config(
            "whisper_openai.base_url", "https://api.openai.com/v1/audio/transcriptions"
        )

        # 测试连接
        if self._test_connection():
            self._is_available = True
            self.log("OpenAI Whisper API connection successful")
            return True
        else:
            self.log("Failed to connect to OpenAI Whisper API")
            return False

    def activate(self) -> bool:
        """激活插件"""
        if not super().activate():
            return False

        if self._is_available:
            self.log("Whisper OpenAI plugin activated")
            return True
        else:
            self.log("Whisper OpenAI plugin not available (no connection)")
            return False

    def deactivate(self) -> bool:
        """停用插件"""
        if not super().deactivate():
            return False

        if self._session:
            self._session.close()
            self._session = None

        self.log("Whisper OpenAI plugin deactivated")
        return True

    def cleanup(self) -> None:
        """清理插件资源"""
        if self._session:
            self._session.close()
            self._session = None
        super().cleanup()

    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        info = super().get_info()
        info.update(
            {
                "features": [
                    "OpenAI Whisper API支持",
                    "高精度语音识别",
                    "多语言支持",
                    "实时转录",
                ],
                "supported_formats": ["wav", "mp3", "m4a", "webm", "ogg"],
                "model": self._model,
                "base_url": self._base_url,
                "is_available": self._is_available,
            }
        )
        return info

    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """获取插件配置模式"""
        return {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "description": "OpenAI API密钥"},
                "model": {
                    "type": "string",
                    "default": "whisper-1",
                    "description": "Whisper模型名称",
                },
                "base_url": {
                    "type": "string",
                    "default": "https://api.openai.com/v1/audio/transcriptions",
                    "description": "API基础URL",
                },
                "language": {
                    "type": "string",
                    "default": "auto",
                    "description": "转录语言",
                },
                "temperature": {
                    "type": "number",
                    "default": 0.0,
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "转录温度参数",
                },
                "timeout": {
                    "type": "number",
                    "default": 30,
                    "description": "请求超时时间（秒）",
                },
            },
            "required": ["api_key"],
        }

    def transcribe(
        self, audio_data: bytes, sample_rate: int = 16000
    ) -> Optional[Dict[str, Any]]:
        """转录音频数据"""
        if not self._is_available or not self._api_key:
            return None

        try:
            # 创建请求
            headers = {"Authorization": f"Bearer {self._api_key}"}

            files = {"file": ("audio.wav", audio_data, "audio/wav")}

            data = {
                "model": self._model,
                "language": self.get_config("language", "auto"),
                "temperature": self.get_config("temperature", 0.0),
            }

            self.log(
                f"Transcribing audio with OpenAI Whisper ({len(audio_data)} bytes)"
            )

            # 发送请求
            response = self._session.post(
                self._base_url,
                headers=headers,
                files=files,
                data=data,
                timeout=self.get_config("timeout", 30),
            )

            if response.status_code == 200:
                result = response.json()
                self.log(f"Transcription completed: {result.get('text', '')[:50]}...")
                return result
            else:
                self.log(f"Transcription failed: HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log(f"Transcription error: {str(e)}")
            return None

    def _test_connection(self) -> bool:
        """测试API连接"""
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}

            # 创建测试音频数据（很短的静音）
            test_audio = b"\x00\x00\x00\x00\x00" * 1000  # 1KB of silence

            files = {"file": ("test.wav", test_audio, "audio/wav")}

            response = self._session.post(
                self._base_url,
                headers=headers,
                files=files,
                data={"model": self._model},
                timeout=10,
            )

            return response.status_code == 200

        except Exception as e:
            self.log(f"Connection test failed: {str(e)}")
            return False

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._is_available
