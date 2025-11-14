"""sherpa-onnx 模型管理器

负责模型下载、缓存和配置管理
"""

import tarfile
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.request import urlopen, Request
from loguru import logger


class SherpaModelManager:
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
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # 默认缓存到用户目录
            self.cache_dir = Path.home() / ".sonicinput" / "sherpa_models"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model cache directory: {self.cache_dir}")

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
        required_files = ["tokens.txt", "encoder-epoch-99-avg-1.onnx", "decoder-epoch-99-avg-1.onnx"]
        if model_name == "paraformer":
            # Paraformer 特殊文件名
            required_files = ["tokens.txt", "encoder.int8.onnx", "decoder.int8.onnx"]

        return model_dir.exists() and all((model_dir / f).exists() for f in required_files)

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

        logger.info(f"Downloading model {model_name} from {url}")
        logger.info(f"Size: {model_info['size_mb']} MB")

        # 下载到临时文件
        archive_path = self.cache_dir / f"{model_name}.tar.bz2"

        try:
            # 下载
            request = Request(url, headers={"User-Agent": "SonicInput/0.2.0"})
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

                        if progress_callback:
                            progress_callback(downloaded, total_size)

            logger.info(f"Download complete: {archive_path}")

            # 解压
            logger.info("Extracting model files...")
            with tarfile.open(archive_path, "r:bz2") as tar:
                tar.extractall(self.cache_dir)

            # 删除压缩包
            archive_path.unlink()
            logger.info("Model extraction complete")

            return self._get_model_dir(model_name)

        except Exception as e:
            logger.error(f"Failed to download model: {e}")
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
            return self.cache_dir / "sherpa-onnx-streaming-zipformer-small-bilingual-zh-en-2023-02-16"
        else:
            # 通用模式
            return self.cache_dir / f"sherpa-onnx-{model_name}"
