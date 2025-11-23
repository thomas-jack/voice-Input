"""sherpa-onnx 模型管理器

负责模型下载、缓存和配置管理
"""

import tarfile
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen

from loguru import logger

from .. import __version__

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QProgressDialog

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    logger.warning("PySide6 not available, progress dialog will not be shown")

from ..core.base.lifecycle_component import LifecycleComponent


class SherpaModelManager(LifecycleComponent):
    """sherpa-onnx 模型管理器"""

    MODELS = {
        "paraformer": {
            "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-paraformer-bilingual-zh-en.tar.bz2",
            "size_mb": 226,
            "language": ["zh", "en"],
            "description": "中英双语高精度模型（推荐）",
            "rtf": 0.15,
        },
        "zipformer-small": {
            "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-small-bilingual-zh-en-2023-02-16.tar.bz2",
            "size_mb": 112,
            "language": ["zh", "en"],
            "description": "超轻量级双语模型",
            "rtf": 0.10,
        },
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """初始化模型管理器

        Args:
            cache_dir: 模型缓存目录，默认为 ~/.sonicinput/sherpa_models
        """
        super().__init__("SherpaModelManager")

        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # 默认缓存到用户目录
            self.cache_dir = Path.home() / ".sonicinput" / "sherpa_models"

        self._model_cache: Dict[str, Path] = {}  # Cache for model directories

    def is_model_cached(self, model_name: str) -> bool:
        """检查模型是否已缓存

        Args:
            model_name: 模型名称

        Returns:
            True if cached, False otherwise
        """
        if model_name not in self.MODELS:
            logger.error(f"Unknown model: {model_name}")
            return False

        model_dir = self._get_model_dir(model_name)

        # 检查必要文件是否存在
        required_files = [
            "tokens.txt",
            "encoder-epoch-99-avg-1.onnx",
            "decoder-epoch-99-avg-1.onnx",
        ]
        if model_name == "paraformer":
            # Paraformer 特殊文件名
            required_files = ["tokens.txt", "encoder.int8.onnx", "decoder.int8.onnx"]

        return model_dir.exists() and all(
            (model_dir / f).exists() for f in required_files
        )

    def download_model(self, model_name: str, progress_callback=None) -> Path:
        """下载模型到本地缓存

        Args:
            model_name: 模型名称
            progress_callback: 进度回调函数 (bytes_downloaded, total_bytes)

        Returns:
            模型目录路径

        Raises:
            ValueError: 如果模型名称不存在
            RuntimeError: 如果下载失败
        """
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}")

        # 检查是否已缓存
        if self.is_model_cached(model_name):
            logger.info(f"Model {model_name} already cached")
            return self._get_model_dir(model_name)

        model_info = self.MODELS[model_name]
        url = model_info["url"]
        size_mb = model_info["size_mb"]

        logger.info(f"Downloading model {model_name} from {url}")
        logger.info(f"Size: {size_mb} MB")

        # 创建进度对话框 (如果 PySide6 可用)
        progress_dialog = None
        if PYSIDE6_AVAILABLE:
            try:
                progress_dialog = QProgressDialog()
                progress_dialog.setWindowTitle("模型下载")
                progress_dialog.setLabelText(
                    f"正在下载模型：{model_name}\n大小：{size_mb} MB"
                )
                progress_dialog.setCancelButton(None)  # 隐藏取消按钮
                progress_dialog.setWindowModality(Qt.WindowModal)
                progress_dialog.setMinimum(0)
                progress_dialog.setMaximum(100)
                progress_dialog.setValue(0)
                progress_dialog.show()
                QApplication.processEvents()
            except Exception as e:
                logger.warning(f"Failed to create progress dialog: {e}")
                progress_dialog = None

        # 下载到临时文件
        archive_path = self.cache_dir / f"{model_name}.tar.bz2"

        try:
            # 下载
            request = Request(url, headers={"User-Agent": f"SonicInput/{__version__}"})
            with urlopen(request, timeout=300) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(archive_path, "wb") as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 更新进度对话框
                        if progress_dialog:
                            try:
                                percent = (
                                    int(downloaded * 100 / total_size)
                                    if total_size > 0
                                    else 0
                                )
                                progress_dialog.setValue(percent)
                                downloaded_mb = downloaded / (1024 * 1024)
                                total_mb = total_size / (1024 * 1024)
                                progress_dialog.setLabelText(
                                    f"正在下载模型：{model_name}\n"
                                    f"进度：{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percent}%)"
                                )
                                QApplication.processEvents()
                            except Exception as e:
                                logger.warning(f"Failed to update progress dialog: {e}")

                        # 保持旧的回调接口兼容性
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            logger.info(f"Download complete: {archive_path}")

            # 解压
            logger.info("Extracting model files...")
            if progress_dialog:
                try:
                    progress_dialog.setValue(95)
                    progress_dialog.setLabelText(
                        f"正在解压模型：{model_name}\n请稍候..."
                    )
                    QApplication.processEvents()
                except Exception as e:
                    logger.warning(
                        f"Failed to update progress dialog during extraction: {e}"
                    )

            with tarfile.open(archive_path, "r:bz2") as tar:
                # Securely extract files with path validation (防止路径遍历攻击)
                safe_members = []
                for member in tar.getmembers():
                    # Normalize member path and resolve it relative to cache_dir
                    member_path = Path(self.cache_dir) / member.name
                    try:
                        # Check if resolved path is within cache_dir (防止../类攻击)
                        member_path.resolve().relative_to(
                            Path(self.cache_dir).resolve()
                        )
                        safe_members.append(member)
                    except ValueError:
                        logger.warning(
                            f"Skipping potentially unsafe tar member: {member.name}"
                        )

                tar.extractall(self.cache_dir, members=safe_members)

            # 删除压缩包
            archive_path.unlink()
            logger.info("Model extraction complete")

            # 关闭进度对话框
            if progress_dialog:
                try:
                    progress_dialog.setValue(100)
                    progress_dialog.close()
                except Exception:
                    pass

            return self._get_model_dir(model_name)

        except Exception as e:
            logger.error(f"Failed to download model: {e}")

            # 关闭进度对话框
            if progress_dialog:
                try:
                    progress_dialog.close()
                except Exception:
                    pass

            # 清理失败的下载
            if archive_path.exists():
                archive_path.unlink()
            raise RuntimeError(f"Failed to download model {model_name}: {e}")

    def ensure_model_available(self, model_name: str) -> Path:
        """确保模型可用（如果不存在则下载）

        Args:
            model_name: 模型名称

        Returns:
            模型目录路径
        """
        if not self.is_model_cached(model_name):
            logger.info(f"Model {model_name} not cached, downloading...")
            return self.download_model(model_name)

        return self._get_model_dir(model_name)

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """获取模型配置（供 sherpa-onnx 使用）

        Args:
            model_name: 模型名称

        Returns:
            模型配置字典

        Raises:
            ValueError: 如果模型不存在
            RuntimeError: 如果模型文件缺失
        """
        model_dir = self.ensure_model_available(model_name)

        if model_name == "paraformer":
            # Paraformer 配置（只支持greedy_search）
            return {
                "tokens": str(model_dir / "tokens.txt"),
                "encoder": str(model_dir / "encoder.int8.onnx"),
                "decoder": str(model_dir / "decoder.int8.onnx"),
                "model_type": "paraformer",
                "num_threads": 4,
                "provider": "cpu",
                "decoding_method": "greedy_search",
            }
        elif model_name == "zipformer-small":
            # Zipformer 配置（保守使用greedy_search以确保兼容性）
            return {
                "tokens": str(model_dir / "tokens.txt"),
                "encoder": str(model_dir / "encoder-epoch-99-avg-1.onnx"),
                "decoder": str(model_dir / "decoder-epoch-99-avg-1.onnx"),
                "joiner": str(model_dir / "joiner-epoch-99-avg-1.onnx"),
                "model_type": "zipformer",
                "num_threads": 4,
                "provider": "cpu",
                "decoding_method": "greedy_search",
            }
        else:
            raise ValueError(f"Unknown model: {model_name}")

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息

        Args:
            model_name: 模型名称

        Returns:
            模型信息字典
        """
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}")

        info = self.MODELS[model_name].copy()
        info["cached"] = self.is_model_cached(model_name)
        info["cache_path"] = str(self._get_model_dir(model_name))

        return info

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用模型

        Returns:
            模型名称 -> 模型信息的字典
        """
        return {name: self.get_model_info(name) for name in self.MODELS.keys()}

    def _get_model_dir(self, model_name: str) -> Path:
        """获取模型目录路径

        Args:
            model_name: 模型名称

        Returns:
            模型目录路径
        """
        if model_name == "paraformer":
            # Paraformer 解压后的目录名
            return self.cache_dir / "sherpa-onnx-streaming-paraformer-bilingual-zh-en"
        elif model_name == "zipformer-small":
            # Zipformer 解压后的目录名
            return (
                self.cache_dir
                / "sherpa-onnx-streaming-zipformer-small-bilingual-zh-en-2023-02-16"
            )
        else:
            # 通用模式
            return self.cache_dir / f"sherpa-onnx-{model_name}"

    # LifecycleComponent implementation

    def _do_start(self) -> bool:
        """Initialize model manager - ensure cache directory exists

        Returns:
            True if initialization successful
        """
        try:
            # Create cache directory
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Model cache directory: {self.cache_dir}")

            # Verify directory is writable
            test_file = self.cache_dir / ".test_write"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                logger.error(f"Cache directory not writable: {e}")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to initialize model manager: {e}")
            return False

    def _do_stop(self) -> bool:
        """Cleanup model manager resources

        Returns:
            True if cleanup successful
        """
        try:
            # Clear cached model directories
            self._model_cache.clear()
            logger.info("Model manager stopped, cache cleared")
            return True

        except Exception as e:
            logger.error(f"Error stopping model manager: {e}")
            return False
