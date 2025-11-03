"""混合语音服务 - 智能本地/云端切换

实现本地Whisper和云端转录服务的智能切换，提供最佳的用户体验。
特性：
- 自动故障转移
- 网络状态检测
- 性能监控
- 成本控制
- 用户偏好学习
"""

import time
import threading
from typing import Optional, Dict, Any, List
from ..core.interfaces import ISpeechService, IConfigService, IEventService
from ..utils import app_logger


class HybridSpeechService(ISpeechService):
    """混合语音服务

    智能管理本地和云端转录服务，根据网络状况、
    性能需求和用户偏好自动选择最佳提供者。
    """

    def __init__(
        self,
        local_service: ISpeechService,
        cloud_service: ISpeechService,
        config_service: IConfigService,
        event_service: IEventService,
    ):
        """初始化混合语音服务

        Args:
            local_service: 本地转录服务（Whisper）
            cloud_service: 云端转录服务（SiliconFlow等）
            config_service: 配置服务
            event_service: 事件服务
        """
        self.local_service = local_service
        self.cloud_service = cloud_service
        self.config_service = config_service
        self.event_service = event_service

        # 当前活跃服务
        self._active_service = None
        self._service_type = None  # "local", "cloud", "hybrid"

        # 性能统计
        self._performance_stats = {
            "local": {
                "count": 0,
                "total_time": 0.0,
                "success_count": 0,
                "error_count": 0,
                "avg_time": 0.0,
            },
            "cloud": {
                "count": 0,
                "total_time": 0.0,
                "success_count": 0,
                "error_count": 0,
                "avg_time": 0.0,
            },
        }

        # 网络状态
        self._network_available = True
        self._last_network_check = 0
        self._network_check_interval = 30  # 30秒检查一次

        # 配置参数
        self._update_config()

        # 线程安全
        self._lock = threading.RLock()

        # 初始化服务选择
        self._initialize_service()

        app_logger.log_audio_event(
            "Hybrid speech service initialized",
            {
                "local_available": local_service is not None,
                "cloud_available": cloud_service is not None,
                "initial_service": self._service_type,
            },
        )

    def _update_config(self) -> None:
        """更新配置参数"""
        with self._lock:
            self.provider = self.config_service.get_setting(
                "transcription.provider", "local"
            )
            self.use_cloud_fallback = self.config_service.get_setting(
                "transcription.siliconflow.use_local_fallback", True
            )
            self.retry_on_error = self.config_service.get_setting(
                "transcription.siliconflow.retry_on_error", True
            )
            self.max_retries = self.config_service.get_setting(
                "transcription.siliconflow.max_retries", 3
            )
            self.cloud_timeout = self.config_service.get_setting(
                "transcription.siliconflow.timeout", 30
            )

    def _initialize_service(self) -> None:
        """初始化服务选择"""
        if self.provider == "cloud":
            self._active_service = self.cloud_service
            self._service_type = "cloud"
        elif self.provider == "local":
            self._active_service = self.local_service
            self._service_type = "local"
        else:  # hybrid
            # 智能选择初始服务
            if self._is_network_available() and self.cloud_service:
                self._active_service = self.cloud_service
                self._service_type = "cloud"
            elif self.local_service:
                self._active_service = self.local_service
                self._service_type = "local"
            else:
                # 没有可用服务
                self._active_service = None
                self._service_type = None

    def _is_network_available(self) -> bool:
        """检查网络连接状态"""
        current_time = time.time()

        # 缓存网络状态检查结果
        if current_time - self._last_network_check < self._network_check_interval:
            return self._network_available

        try:
            # 简单的网络连通性检查
            import socket

            socket.create_connection(("api.siliconflow.cn", 443), timeout=3)
            self._network_available = True
        except Exception:
            self._network_available = False

        self._last_network_check = current_time
        return self._network_available

    def _should_use_cloud(self) -> bool:
        """判断是否应该使用云端服务"""
        if not self.cloud_service:
            return False

        if not self._is_network_available():
            return False

        # 检查云端服务的成功率
        cloud_stats = self._performance_stats["cloud"]
        if cloud_stats["count"] > 0:
            cloud_success_rate = cloud_stats["success_count"] / cloud_stats["count"]
            if cloud_success_rate < 0.8:  # 成功率低于80%则避免使用
                return False

        # 检查云端服务平均响应时间
        if cloud_stats["avg_time"] > 15.0:  # 平均响应时间超过15秒则避免使用
            return False

        return True

    def _update_performance_stats(
        self, service_type: str, success: bool, duration: float
    ) -> None:
        """更新性能统计"""
        with self._lock:
            stats = self._performance_stats[service_type]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["avg_time"] = stats["total_time"] / stats["count"]

            if success:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1

        app_logger.log_audio_event(
            "Performance stats updated",
            {
                "service_type": service_type,
                "success": success,
                "duration": duration,
                "new_avg_time": stats["avg_time"],
                "success_rate": stats["success_count"] / stats["count"],
            },
        )

    def _smart_service_selection(self) -> str:
        """智能服务选择"""
        # 网络不可用时使用本地服务
        if not self._is_network_available():
            if self.local_service:
                return "local"
            else:
                return "cloud"  # 即使网络不可用，也只能尝试云端

        # 基于性能统计选择
        local_stats = self._performance_stats["local"]
        cloud_stats = self._performance_stats["cloud"]

        # 如果有足够的统计数据
        if local_stats["count"] >= 5 and cloud_stats["count"] >= 5:
            local_success_rate = local_stats["success_count"] / local_stats["count"]
            cloud_success_rate = cloud_stats["success_count"] / cloud_stats["count"]

            # 优先选择成功率更高的服务
            if cloud_success_rate > local_success_rate and self._should_use_cloud():
                return "cloud"
            elif local_success_rate > cloud_success_rate:
                return "local"

        # 默认选择云端服务（如果可用）
        if self._should_use_cloud():
            return "cloud"
        elif self.local_service:
            return "local"
        else:
            return "cloud"  # 最后的备选

    def transcribe(self, audio_data, language: Optional[str] = None) -> Dict[str, Any]:
        """转录音频数据，支持智能切换"""
        start_time = time.time()

        with self._lock:
            # 更新配置
            self._update_config()

            # 智能服务选择
            if self.provider == "hybrid":
                preferred_service = self._smart_service_selection()
            else:
                preferred_service = self.provider

            # 确定使用哪个服务
            service = None
            service_type = None

            if (
                preferred_service == "cloud"
                and self.cloud_service
                and self._should_use_cloud()
            ):
                service = self.cloud_service
                service_type = "cloud"
            elif preferred_service == "local" and self.local_service:
                service = self.local_service
                service_type = "local"
            else:
                # 备选服务
                if self.local_service:
                    service = self.local_service
                    service_type = "local"
                elif self.cloud_service:
                    service = self.cloud_service
                    service_type = "cloud"

            if not service:
                return {
                    "text": "",
                    "error": "No transcription service available",
                    "provider": "hybrid",
                    "service_used": None,
                }

            # 记录服务切换
            if self._service_type != service_type:
                app_logger.log_audio_event(
                    "Service switched",
                    {
                        "from_service": self._service_type,
                        "to_service": service_type,
                        "reason": "smart_selection",
                        "network_available": self._is_network_available(),
                    },
                )
                self._active_service = service
                self._service_type = service_type

        # 执行转录
        try:
            result = service.transcribe(audio_data, language)
            duration = time.time() - start_time

            # 更新统计
            success = bool(result.get("text", "").strip())
            self._update_performance_stats(service_type, success, duration)

            # 添加混合服务信息
            result["provider"] = "hybrid"
            result["service_used"] = service_type
            result["network_available"] = self._is_network_available()

            return result

        except Exception as e:
            duration = time.time() - start_time
            self._update_performance_stats(service_type, False, duration)

            # 错误处理和故障转移
            if self.retry_on_error and service_type == "cloud":
                # 云端服务失败，尝试本地服务
                if self.local_service and self.use_cloud_fallback:
                    app_logger.log_audio_event(
                        "Cloud service failed, falling back to local",
                        {"error": str(e), "fallback_enabled": self.use_cloud_fallback},
                    )

                    try:
                        result = self.local_service.transcribe(audio_data, language)
                        duration = time.time() - start_time

                        result["provider"] = "hybrid"
                        result["service_used"] = "local_fallback"
                        result["cloud_error"] = str(e)

                        self._update_performance_stats("local", True, duration)
                        return result
                    except Exception as fallback_error:
                        app_logger.log_error(fallback_error, "hybrid_fallback")

            # 返回错误结果
            return {
                "text": "",
                "error": str(e),
                "provider": "hybrid",
                "service_used": service_type,
                "network_available": self._is_network_available(),
            }

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """加载模型"""
        with self._lock:
            if self._active_service:
                return self._active_service.load_model(model_name)
        return False

    def unload_model(self) -> None:
        """卸载模型"""
        with self._lock:
            if self.local_service:
                self.local_service.unload_model()
            if self.cloud_service:
                self.cloud_service.unload_model()

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        models = []
        with self._lock:
            if self.local_service:
                models.extend(
                    [f"local:{m}" for m in self.local_service.get_available_models()]
                )
            if self.cloud_service:
                models.extend(
                    [f"cloud:{m}" for m in self.cloud_service.get_available_models()]
                )
        return models

    @property
    def is_model_loaded(self) -> bool:
        """模型是否已加载"""
        with self._lock:
            if self._active_service:
                return self._active_service.is_model_loaded
        return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        with self._lock:
            return {
                "services": self._performance_stats.copy(),
                "current_service": self._service_type,
                "network_available": self._is_network_available(),
                "provider": self.provider,
                "config": {
                    "use_cloud_fallback": self.use_cloud_fallback,
                    "retry_on_error": self.retry_on_error,
                    "max_retries": self.max_retries,
                    "cloud_timeout": self.cloud_timeout,
                },
            }

    def set_provider(self, provider: str) -> None:
        """手动设置提供者"""
        with self._lock:
            old_provider = self.provider
            self.provider = provider

            # 更新配置
            self.config_service.set_setting("transcription.provider", provider)

            app_logger.log_audio_event(
                "Provider changed", {"from": old_provider, "to": provider}
            )

            # 重新初始化服务选择
            self._initialize_service()

    def force_service(self, service_type: str) -> None:
        """强制使用指定服务类型（临时）"""
        with self._lock:
            if service_type == "local" and self.local_service:
                self._active_service = self.local_service
                self._service_type = "local"
            elif service_type == "cloud" and self.cloud_service:
                self._active_service = self.cloud_service
                self._service_type = "cloud"

            app_logger.log_audio_event(
                "Service forced",
                {"service_type": service_type, "active_service": self._service_type},
            )

    def __del__(self):
        """析构函数"""
        try:
            self.unload_model()
        except:
            pass
