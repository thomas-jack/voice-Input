"""诊断和修复工具"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

# Windows平台窗口隐藏标志
if sys.platform == "win32":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0


# 延迟导入app_logger以避免循环依赖
def _get_logger():
    """懒加载logger"""
    try:
        from ..utils import app_logger

        return app_logger
    except ImportError:
        return None


class DependencyDiagnostics:
    """依赖诊断和修复工具"""

    def __init__(self):
        self.python_executable = sys.executable
        self.python_dir = Path(sys.executable).parent

    def comprehensive_diagnosis(self) -> Dict[str, Any]:
        """全面诊断系统状态"""
        results = {
            "timestamp": self._get_timestamp(),
            "system_info": self._get_system_info(),
            "python_info": self._get_python_info(),
            "cuda_info": self._get_cuda_info(),
            "pytorch_info": self._get_pytorch_info(),
            "whisper_info": self._get_whisper_info(),
            "path_info": self._get_path_info(),
            "recommendations": [],
        }

        # 生成建议
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import platform

        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        }

    def _get_python_info(self) -> Dict[str, Any]:
        """获取Python环境信息"""
        return {
            "executable": self.python_executable,
            "version": sys.version,
            "path": sys.path[:5],  # 前5个路径
            "prefix": sys.prefix,
            "base_prefix": getattr(sys, "base_prefix", "N/A"),
            "is_venv": hasattr(sys, "real_prefix")
            or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix),
        }

    def _get_cuda_info(self) -> Dict[str, Any]:
        """获取CUDA信息"""
        cuda_info = {
            "cuda_path": os.environ.get("CUDA_PATH", "Not set"),
            "cuda_home": os.environ.get("CUDA_HOME", "Not set"),
            "nvcc_available": False,
            "nvidia_smi_available": False,
        }

        # 检查 nvcc
        try:
            result = subprocess.run(
                ["nvcc", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                cuda_info["nvcc_available"] = True
                cuda_info["nvcc_version"] = result.stdout.strip()
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            pass

        # 检查 nvidia-smi
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                cuda_info["nvidia_smi_available"] = True
                # 提取GPU信息的前几行
                lines = result.stdout.split("\n")[:10]
                cuda_info["nvidia_smi_info"] = "\n".join(lines)
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            pass

        return cuda_info

    def _get_pytorch_info(self) -> Dict[str, Any]:
        """获取PyTorch信息"""
        pytorch_info = {"installed": False}

        try:
            import torch

            pytorch_info.update(
                {
                    "installed": True,
                    "version": torch.__version__,
                    "cuda_available": torch.cuda.is_available(),
                    "cuda_version": torch.version.cuda
                    if hasattr(torch.version, "cuda")
                    else "N/A",
                    "cudnn_version": torch.backends.cudnn.version()
                    if torch.backends.cudnn.is_available()
                    else "N/A",
                    "device_count": torch.cuda.device_count()
                    if torch.cuda.is_available()
                    else 0,
                }
            )

            if torch.cuda.is_available():
                devices = []
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    devices.append(
                        {
                            "id": i,
                            "name": props.name,
                            "memory_gb": props.total_memory / 1024**3,
                            "compute_capability": f"{props.major}.{props.minor}",
                        }
                    )
                pytorch_info["devices"] = devices

        except ImportError as e:
            pytorch_info["import_error"] = str(e)
        except Exception as e:
            pytorch_info["error"] = str(e)

        return pytorch_info

    def _get_whisper_info(self) -> Dict[str, Any]:
        """获取Whisper信息"""
        whisper_info = {"installed": False}

        try:
            # 延迟导入whisper，避免破坏主应用的延迟导入策略
            import whisper

            whisper_info.update(
                {
                    "installed": True,
                    "version": getattr(whisper, "__version__", "unknown"),
                    "available_models": whisper.available_models(),
                    "model_count": len(whisper.available_models()),
                }
            )

            # 尝试加载最小模型来测试功能（诊断时才执行）
            try:
                test_model = whisper.load_model("tiny", device="cpu")
                whisper_info["load_test"] = "SUCCESS"
                del test_model  # 清理
            except Exception as load_error:
                whisper_info["load_test"] = f"FAILED: {load_error}"

        except ImportError as e:
            whisper_info["import_error"] = str(e)
        except Exception as e:
            whisper_info["error"] = str(e)

        return whisper_info

    def _get_path_info(self) -> Dict[str, Any]:
        """获取PATH和环境信息"""
        path_env = os.environ.get("PATH", "")
        paths = path_env.split(os.pathsep)

        # 查找重要的路径
        important_paths = {
            "python_dir": str(self.python_dir),
            "scripts_dir": str(self.python_dir / "Scripts"),
            "cuda_bin": None,
            "system32": None,
        }

        # 检查CUDA路径
        cuda_path = os.environ.get("CUDA_PATH")
        if cuda_path:
            cuda_bin = Path(cuda_path) / "bin"
            if cuda_bin.exists():
                important_paths["cuda_bin"] = str(cuda_bin)

        # 检查system32
        system32 = Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "system32"
        if system32.exists():
            important_paths["system32"] = str(system32)

        # 检查这些路径是否在PATH中
        path_status = {}
        for name, path in important_paths.items():
            if path:
                path_status[name] = {
                    "path": path,
                    "exists": Path(path).exists(),
                    "in_path": path in paths,
                }

        return {
            "path_count": len(paths),
            "important_paths": path_status,
            "first_10_paths": paths[:10],  # 前10个路径
        }

    def _generate_recommendations(self, diagnosis: Dict[str, Any]) -> List[str]:
        """基于诊断结果生成建议"""
        recommendations = []

        # 检查PyTorch
        pytorch_info = diagnosis.get("pytorch_info", {})
        if not pytorch_info.get("installed", False):
            recommendations.append(
                "[ERROR] PyTorch not installed, please install PyTorch first"
            )
        elif not pytorch_info.get("cuda_available", False):
            recommendations.append(
                "[WARNING] PyTorch CUDA support not available, please install CUDA version of PyTorch"
            )

        # 检查Whisper
        whisper_info = diagnosis.get("whisper_info", {})
        if not whisper_info.get("installed", False):
            recommendations.append(
                "[ERROR] Whisper not installed, please install openai-whisper"
            )
        elif whisper_info.get("load_test", "").startswith("FAILED"):
            recommendations.append(
                f"[WARNING] Whisper load test failed: {whisper_info.get('load_test', '')}"
            )

        # 检查CUDA环境
        cuda_info = diagnosis.get("cuda_info", {})
        if not cuda_info.get("nvcc_available", False):
            recommendations.append(
                "[WARNING] NVCC not available, may need to install CUDA Toolkit"
            )
        if not cuda_info.get("nvidia_smi_available", False):
            recommendations.append(
                "[WARNING] nvidia-smi not available, may need to install/update NVIDIA drivers"
            )

        # 检查PATH
        path_info = diagnosis.get("path_info", {})
        important_paths = path_info.get("important_paths", {})

        python_dir_info = important_paths.get("python_dir", {})
        if not python_dir_info.get("in_path", False):
            recommendations.append(
                "[WARNING] Python directory not in PATH, may cause library loading issues"
            )

        cuda_bin_info = important_paths.get("cuda_bin", {})
        if cuda_bin_info and not cuda_bin_info.get("in_path", False):
            recommendations.append(
                "[WARNING] CUDA bin directory not in PATH, may cause CUDA library loading issues"
            )

        # 生成修复建议
        if recommendations:
            recommendations.append("\n[FIX] Repair suggestions:")
            recommendations.append("1. Try reinstalling: uv sync --reinstall")
            recommendations.append(
                "2. Install CUDA version PyTorch: uv add torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
            )
            recommendations.append("3. Reinstall Whisper: uv add openai-whisper")
            recommendations.append("4. Restart application")

        return recommendations

    def save_diagnosis_report(
        self, diagnosis: Dict[str, Any], filepath: str = None
    ) -> str:
        """保存诊断报告到文件"""
        if filepath is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"dependency_diagnosis_{timestamp}.json"

        try:
            import json

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(diagnosis, f, indent=2, ensure_ascii=False, default=str)

            return filepath
        except Exception as e:
            logger = _get_logger()
            if logger:
                logger.log_error(e, "save_diagnosis_report")
            raise

    def print_diagnosis_summary(self, diagnosis: Dict[str, Any]) -> None:
        """打印诊断摘要"""
        print("=" * 60)
        print("Dependency Diagnosis Report")
        print("=" * 60)

        # 系统信息
        system_info = diagnosis.get("system_info", {})
        print(f"System: {system_info.get('platform', 'Unknown')}")
        print(f"Python: {system_info.get('python_version', 'Unknown')}")

        # PyTorch状态
        pytorch_info = diagnosis.get("pytorch_info", {})
        if pytorch_info.get("installed", False):
            print(f"[OK] PyTorch: {pytorch_info.get('version', 'Unknown')}")
            if pytorch_info.get("cuda_available", False):
                print(f"[OK] CUDA: {pytorch_info.get('cuda_version', 'Unknown')}")
                print(f"[OK] GPU devices: {pytorch_info.get('device_count', 0)}")
            else:
                print("[FAIL] CUDA: Not available")
        else:
            print("[FAIL] PyTorch: Not installed")

        # Whisper状态
        whisper_info = diagnosis.get("whisper_info", {})
        if whisper_info.get("installed", False):
            print(f"[OK] Whisper: {whisper_info.get('version', 'Unknown')}")
            load_test = whisper_info.get("load_test", "")
            if load_test == "SUCCESS":
                print("[OK] Whisper load test: Passed")
            else:
                print(f"[FAIL] Whisper load test: {load_test}")
        else:
            print("[FAIL] Whisper: Not installed")

        # 建议
        recommendations = diagnosis.get("recommendations", [])
        if recommendations:
            print("\nRecommendations:")
            for rec in recommendations:
                # 移除emoji，只保留文本
                clean_rec = (
                    rec.replace("❌", "[ERROR]")
                    .replace("⚠️", "[WARNING]")
                    .replace("🔧", "[FIX]")
                )
                print(f"  {clean_rec}")

        print("=" * 60)


# 创建全局诊断工具实例
dependency_diagnostics = DependencyDiagnostics()
