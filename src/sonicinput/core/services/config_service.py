"""配置服务 - 向后兼容的导出接口

为保持向后兼容性，将RefactoredConfigService导出为ConfigService。
原来的920行ConfigService已重构为多个专职服务。
"""

# 导入重构后的配置服务，作为ConfigService导出
from .config.config_service_refactored import RefactoredConfigService as ConfigService

__all__ = ["ConfigService"]
