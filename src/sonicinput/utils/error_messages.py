"""用户友好错误消息转换器

将技术性错误转换为用户可理解的消息
"""

from typing import Optional
import re


class ErrorMessageTranslator:
    """错误消息翻译器 - 将技术错误转换为用户友好消息"""

    # 错误模式到用户消息的映射
    ERROR_PATTERNS = {
        # 音频设备相关
        r"Invalid number of channels|channels.*not supported": {
            "user_msg": "音频设备不支持当前配置，请在设置中更换音频设备",
            "category": "audio_device",
        },
        r"Input overflowed|Overflow": {
            "user_msg": "音频输入过载，请降低麦克风音量或更换设备",
            "category": "audio_overflow",
        },
        r"No Default Input Device Available|device not found": {
            "user_msg": "未找到可用的麦克风设备，请检查麦克风连接",
            "category": "audio_device",
        },
        r"Pa.*Error|portaudio": {
            "user_msg": "音频系统错误，请重启应用或检查音频设备",
            "category": "audio_system",
        },
        # API相关
        r"API key.*not set|api.*key.*invalid": {
            "user_msg": "AI服务API密钥未设置或无效，请在设置中配置API密钥",
            "category": "api_key",
        },
        r"(401|Unauthorized)": {
            "user_msg": "API认证失败，请检查API密钥是否正确",
            "category": "api_auth",
        },
        r"(429|Too Many Requests|rate limit)": {
            "user_msg": "API调用次数超限，请稍后再试或升级API套餐",
            "category": "api_rate_limit",
        },
        r"(500|502|503|504|Internal Server Error|Bad Gateway|Service Unavailable|Gateway Timeout)": {
            "user_msg": "AI服务暂时不可用，请稍后重试",
            "category": "api_server",
        },
        r"Connection.*refused|Connection.*timeout|Network.*error": {
            "user_msg": "网络连接失败，请检查网络连接后重试",
            "category": "network",
        },
        # 模型加载相关
        r"model.*not found|No such file": {
            "user_msg": "语音识别模型未找到，应用会自动下载，请稍等片刻",
            "category": "model_not_found",
        },
        r"CUDA.*out of memory|out of memory": {
            "user_msg": "GPU内存不足，将自动切换到CPU模式（速度较慢）",
            "category": "gpu_memory",
        },
        r"CUDA.*not available|No CUDA": {
            "user_msg": "GPU不可用，使用CPU模式进行识别（速度较慢）",
            "category": "gpu_unavailable",
        },
        # 快捷键相关
        r"hotkey.*already registered|hotkey.*in use": {
            "user_msg": "快捷键已被其他应用占用，请在设置中更换快捷键",
            "category": "hotkey_conflict",
        },
        r"Invalid hotkey|hotkey.*invalid": {
            "user_msg": "快捷键格式无效，请检查快捷键设置",
            "category": "hotkey_invalid",
        },
        # 权限相关
        r"Permission denied|Access denied": {
            "user_msg": "权限不足，请以管理员权限运行应用",
            "category": "permission",
        },
        # 配置相关
        r"config.*corrupt|JSON.*decode": {
            "user_msg": "配置文件损坏，已重置为默认配置",
            "category": "config_corrupt",
        },
    }

    @classmethod
    def translate(cls, error: Exception, context: Optional[str] = None) -> dict:
        """将异常转换为用户友好消息

        Args:
            error: 原始异常对象
            context: 错误上下文（如 "recording", "transcription"）

        Returns:
            包含以下字段的字典：
            - user_message: 用户友好消息
            - technical_message: 技术详情（用于日志）
            - category: 错误类别
            - suggestions: 建议操作（可选）
        """
        error_str = str(error)
        error_type = type(error).__name__

        # 匹配错误模式
        for pattern, info in cls.ERROR_PATTERNS.items():
            if re.search(pattern, error_str, re.IGNORECASE):
                return {
                    "user_message": info["user_msg"],
                    "technical_message": f"{error_type}: {error_str}",
                    "category": info["category"],
                    "suggestions": cls._get_suggestions(info["category"], context),
                }

        # 未匹配到任何模式，返回通用消息
        return cls._get_generic_message(error, context)

    @classmethod
    def _get_generic_message(cls, error: Exception, context: Optional[str]) -> dict:
        """获取通用错误消息"""
        error_type = type(error).__name__
        error_str = str(error)

        # 根据上下文生成更具体的通用消息
        context_messages = {
            "recording": "录音过程中出现错误",
            "transcription": "语音识别过程中出现错误",
            "ai_processing": "AI文本优化过程中出现错误",
            "input": "文本输入过程中出现错误",
            "hotkey": "快捷键注册过程中出现错误",
        }

        user_message = context_messages.get(context, "操作过程中出现未知错误")

        return {
            "user_message": f"{user_message}，请稍后重试",
            "technical_message": f"{error_type}: {error_str}",
            "category": "unknown",
            "suggestions": ["重启应用", "检查日志文件获取详细信息"],
        }

    @classmethod
    def _get_suggestions(cls, category: str, context: Optional[str]) -> list:
        """根据错误类别获取建议操作"""
        suggestions_map = {
            "audio_device": ["检查麦克风连接", "在设置中选择其他音频设备", "重启应用"],
            "audio_overflow": [
                "降低麦克风音量",
                "更换质量更好的麦克风",
                "调整音频设备设置",
            ],
            "audio_system": ["重启应用", "检查系统音频服务", "重新插拔音频设备"],
            "api_key": [
                "在设置 → AI配置中设置正确的API密钥",
                "检查API密钥是否有效",
                "确认API服务商账户状态",
            ],
            "api_auth": [
                "检查API密钥是否正确",
                "确认API服务商账户状态",
                "重新生成API密钥",
            ],
            "api_rate_limit": ["等待几分钟后重试", "升级API套餐", "更换API服务商"],
            "api_server": ["等待几分钟后重试", "检查服务商状态页面", "更换API服务商"],
            "network": ["检查网络连接", "检查防火墙设置", "尝试使用VPN"],
            "model_not_found": [
                "等待模型自动下载完成",
                "检查网络连接",
                "手动下载模型文件",
            ],
            "gpu_memory": [
                "关闭其他占用GPU的程序",
                "在设置中切换到CPU模式",
                "使用更小的模型（如medium或small）",
            ],
            "gpu_unavailable": [
                "检查CUDA是否正确安装",
                "更新显卡驱动",
                "在设置中切换到CPU模式",
            ],
            "hotkey_conflict": [
                "在设置中更换快捷键",
                "关闭占用快捷键的其他应用",
                "使用不常用的组合键",
            ],
            "hotkey_invalid": [
                "检查快捷键格式（如 ctrl+shift+v）",
                "使用支持的按键组合",
                "重置为默认快捷键",
            ],
            "permission": [
                "以管理员权限运行应用",
                "检查文件夹权限",
                "关闭安全软件重试",
            ],
            "config_corrupt": [
                "应用已自动重置配置",
                "重新配置偏好设置",
                "如有备份可手动恢复",
            ],
        }

        return suggestions_map.get(category, ["重启应用", "查看日志获取详细信息"])


def get_user_friendly_error(error: Exception, context: Optional[str] = None) -> str:
    """快捷函数：获取用户友好错误消息（仅返回消息字符串）

    Args:
        error: 原始异常对象
        context: 错误上下文

    Returns:
        用户友好的错误消息字符串
    """
    result = ErrorMessageTranslator.translate(error, context)
    return result["user_message"]
