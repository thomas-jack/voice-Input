"""GPU Manager - PyTorch-free implementation using nvidia-smi"""

import gc
import subprocess
from typing import Dict, Any, Optional
from ..utils import GPUError, app_logger


class GPUManager:
    """GPU memory management and CUDA support checking without PyTorch dependency"""

    def __init__(self):
        self._cuda_available = None
        self._device_info = None
        self._memory_fraction = 0.8
        self._initialize_device()

    def _initialize_device(self) -> None:
        """Initialize device with fallback mechanism"""
        try:
            self._cuda_available = self._check_cuda_via_nvidia_smi()

            if self._cuda_available:
                app_logger.log_audio_event("CUDA device detected via nvidia-smi", {})
                self._device_info = self._get_gpu_info_from_nvidia_smi()
                memory_usage = self.get_memory_usage()
                app_logger.log_gpu_info(True, memory_usage)
            else:
                app_logger.log_audio_event("CUDA not available, using CPU", {})
                app_logger.log_gpu_info(False)

        except Exception as e:
            app_logger.log_error(e, "device_initialization")
            self._cuda_available = False
            app_logger.log_audio_event(
                "Device initialization failed, using CPU", {"error": str(e)}
            )

    def _check_cuda_via_nvidia_smi(self) -> bool:
        """Check CUDA availability using nvidia-smi command"""
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return False

    def _get_gpu_info_from_nvidia_smi(self) -> Optional[Dict[str, Any]]:
        """Get GPU information using nvidia-smi"""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.total,memory.used,memory.free",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
            )

            if result.returncode != 0:
                return None

            # Parse first GPU info
            lines = result.stdout.strip().split("\n")
            if not lines:
                return None

            parts = [p.strip() for p in lines[0].split(",")]
            if len(parts) < 5:
                return None

            return {
                "index": int(parts[0]),
                "name": parts[1],
                "memory_total_mb": float(parts[2]),
                "memory_used_mb": float(parts[3]),
                "memory_free_mb": float(parts[4]),
            }

        except Exception as e:
            app_logger.log_error(e, "get_gpu_info_nvidia_smi")
            return None

    def _get_compute_capability(self) -> Optional[str]:
        """Get compute capability using nvidia-smi"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
            )

            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0].strip()
            return None

        except Exception:
            return None

    def check_cuda_availability(self) -> Dict[str, Any]:
        """Detailed CUDA availability check"""
        result = {
            "available": False,
            "device_count": 0,
            "current_device": None,
            "devices": [],
            "error": None,
        }

        try:
            # Check if nvidia-smi is available
            if not self._check_cuda_via_nvidia_smi():
                result["error"] = "nvidia-smi not available or no CUDA devices"
                return result

            # Get all GPU devices
            smi_result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.total,compute_cap",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
            )

            if smi_result.returncode != 0:
                result["error"] = "Failed to query GPU devices"
                return result

            lines = smi_result.stdout.strip().split("\n")
            result["available"] = len(lines) > 0
            result["device_count"] = len(lines)
            result["current_device"] = 0  # Default to first GPU

            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    device_info = {
                        "id": int(parts[0]),
                        "name": parts[1],
                        "memory_gb": float(parts[2]) / 1024,
                        "compute_capability": parts[3],
                    }
                    result["devices"].append(device_info)

            app_logger.log_audio_event("CUDA availability check completed", result)

        except Exception as e:
            result["error"] = str(e)
            app_logger.log_error(e, "cuda_availability_check")

        return result

    def is_gpu_available(self) -> bool:
        """Check if GPU is available"""
        if self._cuda_available is None:
            self._cuda_available = self._check_cuda_via_nvidia_smi()
        return self._cuda_available

    def get_device(self) -> str:
        """Get current device as string (for compatibility)"""
        return "cuda" if self.is_gpu_available() else "cpu"

    def get_memory_usage(self) -> Dict[str, float]:
        """Get GPU memory usage"""
        if not self.is_gpu_available():
            return {}

        try:
            gpu_info = self._get_gpu_info_from_nvidia_smi()
            if not gpu_info:
                return {}

            total_gb = gpu_info["memory_total_mb"] / 1024
            used_gb = gpu_info["memory_used_mb"] / 1024
            free_gb = gpu_info["memory_free_mb"] / 1024

            return {
                "allocated_gb": used_gb,  # Used memory
                "reserved_gb": used_gb,  # Same as allocated for compatibility
                "total_gb": total_gb,
                "free_gb": free_gb,
                "utilization_percent": (used_gb / total_gb) * 100
                if total_gb > 0
                else 0,
            }

        except Exception as e:
            app_logger.log_error(e, "get_memory_usage")
            return {}

    def clear_cache(self) -> None:
        """温和地清理GPU内存缓存

        注意：使用 torch.cuda.empty_cache() 只清理未使用的缓存，
        不会破坏 CUDA context 或影响正在使用的模型。
        """
        try:
            gc.collect()  # Python垃圾回收

            # 使用 PyTorch 的温和清理方式
            if self.is_gpu_available():
                try:
                    import torch

                    if torch.cuda.is_available():
                        # empty_cache() 只释放缓存中未使用的内存
                        # 不会影响正在使用的模型或破坏 CUDA context
                        torch.cuda.empty_cache()

                        memory_usage = self.get_memory_usage()
                        app_logger.debug(
                            f"GPU cache cleared gently, current usage: {memory_usage}"
                        )

                except Exception as torch_error:
                    app_logger.debug(
                        f"torch.cuda.empty_cache() failed, continuing: {torch_error}"
                    )

        except Exception as e:
            app_logger.log_error(e, "clear_cache")

    def set_memory_fraction(self, fraction: float) -> None:
        """Set memory usage fraction (stored for reference, not enforced)"""
        if not 0.1 <= fraction <= 1.0:
            raise GPUError(
                f"Memory fraction must be between 0.1 and 1.0, got {fraction}"
            )

        self._memory_fraction = fraction
        app_logger.log_audio_event(
            "Memory fraction updated (reference only)",
            {
                "fraction": fraction,
                "note": "CTranslate2 handles memory management internally",
            },
        )

    def check_memory_requirements(self, required_gb: float) -> bool:
        """Check if sufficient memory is available"""
        if not self.is_gpu_available():
            return False

        memory_info = self.get_memory_usage()
        available_gb = memory_info.get("free_gb", 0)

        return available_gb >= required_gb

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        info = {
            "cuda_available": self.is_gpu_available(),
            "device_type": self.get_device(),
            "memory_fraction": self._memory_fraction,
        }

        if self.is_gpu_available():
            gpu_info = self._get_gpu_info_from_nvidia_smi()
            compute_cap = self._get_compute_capability()

            if gpu_info:
                info.update(
                    {
                        "device_name": gpu_info["name"],
                        "compute_capability": compute_cap or "unknown",
                        "total_memory_gb": gpu_info["memory_total_mb"] / 1024,
                    }
                )

            # Add current memory usage
            info.update(self.get_memory_usage())

        return info

    def prepare_for_model_loading(self) -> None:
        """Prepare for model loading"""
        if self.is_gpu_available():
            try:
                self.clear_cache()

                memory_info = self.get_memory_usage()
                app_logger.log_gpu_info(True, memory_info)

                app_logger.log_audio_event(
                    "GPU prepared for model loading", {"memory_info": memory_info}
                )

            except Exception as e:
                app_logger.log_audio_event(
                    "GPU preparation warning",
                    {"error": str(e), "fallback": "proceeding without GPU preparation"},
                )

    def cleanup_after_inference(self) -> None:
        """Cleanup after inference"""
        if self.is_gpu_available():
            self.clear_cache()

    def estimate_model_memory_usage(self, model_name: str) -> float:
        """Estimate model memory usage (GB)"""
        # Whisper model memory usage estimates
        model_memory_map = {
            "tiny": 0.5,
            "base": 0.7,
            "small": 1.2,
            "medium": 2.5,
            "large-v3": 4.2,
            "large-v3-turbo": 3.8,
            "turbo": 3.5,
        }

        for key, memory in model_memory_map.items():
            if key in model_name.lower():
                return memory

        # Default estimate
        return 3.0
