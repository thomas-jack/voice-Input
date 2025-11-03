"""SonicInput 插件包

SonicInput的插件系统支持多种类型的插件扩展：
- 语音识别引擎插件
- AI服务插件
- 输入方法插件
- 音频处理插件
- UI组件插件
- 事件处理器插件
- 通用扩展插件

使用方法：
1. 将插件文件放入 plugins/ 目录
2. 插件会被自动发现和加载
3. 通过插件管理器控制插件的生命周期

插件开发指南：
- 继承 BasePlugin 基类
- 实现必需的接口方法
- 提供插件配置模式
- 处理插件生命周期事件
"""

from .example_plugin import ExamplePlugin
from .whisper_openai_plugin import WhisperOpenAIPlugin

__all__ = [
    "ExamplePlugin",
    "WhisperOpenAIPlugin",
]