"""专用的Whisper工作线程，用于隔离Qt环境对DLL加载的干扰"""

import os
import sys
import time
import platform
import threading
import shutil

from PySide6.QtCore import QThread, Signal
from ..utils import app_logger


class WhisperWorkerThread(QThread):
    """
    专用的Whisper工作线程
    在独立线程中重置DLL环境，避免Qt对whisper/numba/llvmlite加载的干扰
    """

    # 信号定义
    model_loaded = Signal(bool, str)  # success, error_message
    progress_update = Signal(str)  # status_message
    environment_reset = Signal(bool)  # success

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_name = None
        self.timeout_seconds = 300
        self.whisper_engine = None
        self.should_stop = False

        # 环境重置标志
        self.environment_prepared = False

        app_logger.log_gui_operation(
            "WhisperWorkerThread", "Initialized dedicated whisper worker thread"
        )

    def set_parameters(
        self, whisper_engine, model_name: str, timeout_seconds: int = 300
    ):
        """设置加载参数"""
        self.whisper_engine = whisper_engine
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

        app_logger.log_gui_operation(
            "WhisperWorkerThread Parameters",
            f"Model: {model_name}, Timeout: {timeout_seconds}s",
        )

    def stop_loading(self):
        """停止加载过程"""
        self.should_stop = True
        app_logger.log_gui_operation("WhisperWorkerThread", "Stop loading requested")

    def reset_dll_environment(self):
        """重置DLL环境以避免Qt干扰"""
        try:
            app_logger.log_model_loading_step(
                "Starting DLL environment reset in worker thread"
            )

            # 步骤1: 记录当前环境状态
            original_path = os.environ.get("PATH", "")
            app_logger.log_model_loading_step(
                "Original PATH recorded",
                {"path_length": len(original_path), "thread_id": threading.get_ident()},
            )

            # 步骤2: Windows特定的DLL搜索路径设置
            if platform.system() == "Windows":
                self._reset_windows_dll_paths()

            # 步骤3: 清理可能冲突的环境变量
            self._clean_conflicting_env_vars()

            # 步骤4: 设置CUDA环境变量
            self._setup_cuda_environment()

            # 步骤5: 强制清理已导入的冲突模块
            self._cleanup_imported_modules()

            self.environment_prepared = True
            app_logger.log_model_loading_step(
                "DLL environment reset completed successfully"
            )
            self.environment_reset.emit(True)

        except Exception as e:
            app_logger.log_detailed_error(
                e,
                "DLL_Environment_Reset",
                [
                    "Check Windows DLL search paths",
                    "Verify CUDA installation",
                    "Check Qt library conflicts",
                    "Try running as administrator",
                ],
            )
            self.environment_prepared = False
            self.environment_reset.emit(False)
            raise

    def _reset_windows_dll_paths(self):
        """重置Windows DLL搜索路径"""
        try:
            app_logger.log_model_loading_step("Resetting Windows DLL search paths")

            # 获取系统关键路径
            system_paths = []

            # Windows系统目录
            try:
                import ctypes

                system_dir = ctypes.create_unicode_buffer(260)
                ctypes.windll.kernel32.GetSystemDirectoryW(system_dir, 260)
                system_paths.append(system_dir.value)

                # Windows目录
                windows_dir = ctypes.create_unicode_buffer(260)
                ctypes.windll.kernel32.GetWindowsDirectoryW(windows_dir, 260)
                system_paths.append(windows_dir.value)

                app_logger.log_model_loading_step(
                    "System directories located",
                    {"system_dir": system_dir.value, "windows_dir": windows_dir.value},
                )
            except Exception as e:
                app_logger.log_model_loading_step(
                    f"Warning: Could not get system directories: {e}"
                )

            # 添加CUDA路径到DLL搜索路径
            cuda_paths = self._find_all_cuda_paths()

            for cuda_path in cuda_paths:
                if cuda_path and os.path.exists(cuda_path):
                    bin_path = os.path.join(cuda_path, "bin")
                    lib_path = os.path.join(cuda_path, "lib", "x64")

                    if os.path.exists(bin_path):
                        try:
                            os.add_dll_directory(bin_path)
                            app_logger.log_model_loading_step(
                                f"Added CUDA bin to DLL search: {bin_path}"
                            )
                        except Exception as e:
                            app_logger.log_model_loading_step(
                                f"Warning: Could not add CUDA bin path: {e}"
                            )

                    if os.path.exists(lib_path):
                        try:
                            os.add_dll_directory(lib_path)
                            app_logger.log_model_loading_step(
                                f"Added CUDA lib to DLL search: {lib_path}"
                            )
                        except Exception as e:
                            app_logger.log_model_loading_step(
                                f"Warning: Could not add CUDA lib path: {e}"
                            )
                    break

            # 添加当前Python环境的DLL路径
            if hasattr(sys, "base_prefix"):
                python_dll_path = os.path.join(sys.base_prefix, "DLLs")
                if os.path.exists(python_dll_path):
                    try:
                        os.add_dll_directory(python_dll_path)
                        app_logger.log_model_loading_step(
                            f"Added Python DLLs to search: {python_dll_path}"
                        )
                    except Exception as e:
                        app_logger.log_model_loading_step(
                            f"Warning: Could not add Python DLL path: {e}"
                        )

        except Exception as e:
            app_logger.log_model_loading_step(f"Warning in Windows DLL path reset: {e}")

    def _clean_conflicting_env_vars(self):
        """清理可能冲突的环境变量"""
        app_logger.log_model_loading_step(
            "Cleaning potentially conflicting environment variables"
        )

        # 不强制设置CUDA_VISIBLE_DEVICES为空，保持GPU可用
        # 清理可能的Qt相关DLL路径冲突
        qt_vars_to_check = ["QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH"]
        for var in qt_vars_to_check:
            if var in os.environ:
                original_value = os.environ[var]
                app_logger.log_model_loading_step(
                    f"Found Qt variable {var}: {original_value}"
                )

        # 确保NUMBA相关变量设置正确
        os.environ["NUMBA_CACHE_DIR"] = os.path.join(
            os.path.expanduser("~"), ".numba_cache"
        )
        os.environ["NUMBA_DISABLE_INTEL_SVML"] = "1"  # 避免Intel SVML库冲突

        app_logger.log_model_loading_step("Environment variables cleaned")

    def _setup_cuda_environment(self):
        """设置CUDA环境"""
        app_logger.log_model_loading_step("Setting up CUDA environment")

        # 确保CUDA路径正确
        cuda_path = os.environ.get("CUDA_PATH")
        if not cuda_path:
            # 尝试找到CUDA安装路径
            possible_cuda_paths = [
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9",
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8",
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.7",
            ]

            for path in possible_cuda_paths:
                if os.path.exists(path):
                    os.environ["CUDA_PATH"] = path
                    app_logger.log_model_loading_step(f"Set CUDA_PATH to: {path}")
                    break

        # 设置CUDA缓存目录
        cuda_cache_dir = os.path.join(os.path.expanduser("~"), ".cuda_cache")
        os.environ["CUDA_CACHE_PATH"] = cuda_cache_dir

        app_logger.log_model_loading_step("CUDA environment setup completed")

    def _cleanup_imported_modules(self):
        """清理已导入的可能冲突的模块"""
        app_logger.log_model_loading_step(
            "Cleaning up potentially conflicting imported modules"
        )

        # 要清理的模块列表（但不删除，只是记录）
        modules_to_check = ["numba", "llvmlite", "whisper"]

        found_modules = []
        for module_name in modules_to_check:
            if module_name in sys.modules:
                found_modules.append(module_name)

        if found_modules:
            app_logger.log_model_loading_step(
                "Found pre-loaded modules",
                {
                    "modules": found_modules,
                    "note": "These modules were already loaded before thread isolation",
                },
            )
        else:
            app_logger.log_model_loading_step(
                "No conflicting modules found - clean slate"
            )

    def run(self):
        """主要运行方法"""
        try:
            if self.should_stop:
                return

            # 步骤1: 重置DLL环境
            self.progress_update.emit("[INIT] Preparing isolated thread environment...")
            self.reset_dll_environment()

            if not self.environment_prepared or self.should_stop:
                self.model_loaded.emit(False, "Failed to prepare thread environment")
                return

            # 步骤2: 验证参数
            if not self.whisper_engine or not self.model_name:
                self.model_loaded.emit(False, "Invalid parameters for model loading")
                return

            # 步骤3: 在隔离环境中加载模型
            self.progress_update.emit(
                f"[LOAD] Loading {self.model_name} in isolated thread..."
            )

            start_time = time.time()

            try:
                # 使用whisper_engine的internal方法，在隔离线程中直接加载
                self.whisper_engine._load_model_internal(self.timeout_seconds)

                load_time = time.time() - start_time

                app_logger.log_model_loading_step(
                    "Model loaded successfully in isolated thread",
                    {
                        "model_name": self.model_name,
                        "load_time": f"{load_time:.2f}s",
                        "thread_id": threading.get_ident(),
                    },
                )

                self.model_loaded.emit(True, "")

            except Exception as e:
                error_msg = f"Model loading failed in isolated thread: {e}"
                app_logger.log_detailed_error(
                    e,
                    f"Isolated_Thread_Load_{self.model_name}",
                    [
                        "Check if the DLL environment reset was successful",
                        "Verify CUDA is available in the isolated thread",
                        "Check thread-specific resource limits",
                        "Try a smaller model first",
                    ],
                )
                self.model_loaded.emit(False, error_msg)

        except Exception as e:
            error_msg = f"Worker thread failed: {e}"
            app_logger.log_detailed_error(
                e,
                "WhisperWorkerThread",
                [
                    "Check thread creation and initialization",
                    "Verify Qt thread integration",
                    "Check system resources",
                ],
            )
            self.model_loaded.emit(False, error_msg)

    def cleanup(self):
        """清理资源"""
        app_logger.log_gui_operation("WhisperWorkerThread", "Cleaning up worker thread")
        self.should_stop = True

        # 等待线程结束
        if self.isRunning():
            self.quit()
            self.wait(3000)  # 等待最多3秒

        app_logger.log_gui_operation(
            "WhisperWorkerThread", "Worker thread cleanup completed"
        )

    def _find_all_cuda_paths(self) -> list:
        """动态查找所有可用的CUDA安装路径"""
        cuda_paths = []

        try:
            # 1. 环境变量中的CUDA路径
            env_cuda_path = os.environ.get("CUDA_PATH")
            if env_cuda_path:
                cuda_paths.append(env_cuda_path)

            # 2. 程序文件中的NVIDIA GPU Computing Toolkit
            program_files = [
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA",
                r"C:\Program Files (x86)\NVIDIA GPU Computing Toolkit\CUDA",
            ]

            for base_path in program_files:
                if os.path.exists(base_path):
                    # 查找所有CUDA版本
                    try:
                        for item in os.listdir(base_path):
                            if item.startswith("v") and os.path.isdir(
                                os.path.join(base_path, item)
                            ):
                                cuda_paths.append(os.path.join(base_path, item))
                    except (PermissionError, OSError):
                        continue

            # 3. 查找系统PATH中的CUDA相关路径
            system_path = os.environ.get("PATH", "").split(os.pathsep)
            for path in system_path:
                if "cuda" in path.lower() and os.path.exists(path):
                    # 获取CUDA的根目录
                    cuda_root = path
                    while "bin" in os.path.basename(cuda_root).lower():
                        cuda_root = os.path.dirname(cuda_root)
                    if cuda_root not in cuda_paths:
                        cuda_paths.append(cuda_root)

            # 4. 使用nvidia-smi获取CUDA路径（如果可用）
            try:
                import subprocess

                result = subprocess.run(
                    ["nvidia-smi"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    # nvidia-smi可用，尝试通过其位置找到CUDA
                    nvidia_smi_path = shutil.which("nvidia-smi")
                    if nvidia_smi_path:
                        # 通常nvidia-smi在CUDA的bin目录中
                        cuda_root = os.path.dirname(os.path.dirname(nvidia_smi_path))
                        if cuda_root not in cuda_paths:
                            cuda_paths.append(cuda_root)
            except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
                pass

            # 5. 去重并按版本排序（优先使用最新版本）
            cuda_paths = list(set(cuda_paths))
            cuda_paths.sort(key=self._get_cuda_version_key, reverse=True)

            app_logger.log_model_loading_step(f"Found CUDA paths: {cuda_paths}")
            return cuda_paths

        except Exception as e:
            app_logger.log_warning(
                "Failed to dynamically find CUDA paths", {"error": str(e)}
            )
            # 降级到硬编码路径
            return [
                os.environ.get("CUDA_PATH"),
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9",
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8",
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.7",
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6",
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.5",
            ]

    def _get_cuda_version_key(self, path: str) -> tuple:
        """从CUDA路径提取版本号用于排序"""
        try:
            import re

            # 提取版本号，如 "v12.8" -> (12, 8)
            version_match = re.search(r"v(\d+)\.(\d+)", path)
            if version_match:
                major = int(version_match.group(1))
                minor = int(version_match.group(2))
                return (major, minor)
            return (0, 0)  # 无法解析版本的排在最后
        except Exception as e:
            app_logger.log_error(
                e,
                "cuda_version_parse_failed",
                {"context": "Failed to parse CUDA version from path", "path": path}
            )
            return (0, 0)
