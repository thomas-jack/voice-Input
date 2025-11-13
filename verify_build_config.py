#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证构建配置脚本

检查构建环境是否正确配置，包括：
1. Python 环境和版本
2. Nuitka 安装
3. C 编译器可用性
4. sherpa-onnx 安装（本地版）
5. 所需依赖包
"""
import sys
import subprocess
from pathlib import Path
import io

# Windows 控制台编码处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_python_version():
    """检查 Python 版本"""
    print_section("Python 环境")
    print(f"Python 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}")

    version_info = sys.version_info
    if version_info.major == 3 and version_info.minor >= 10:
        print("状态: OK (Python 3.10+)")
        return True
    else:
        print("状态: 错误 (需要 Python 3.10+)")
        return False

def check_nuitka():
    """检查 Nuitka 安装"""
    print_section("Nuitka 编译器")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True
        )
        print(result.stdout.strip())
        print("状态: OK")
        return True
    except Exception as e:
        print(f"状态: 错误 - {e}")
        print("请运行: uv sync --dev")
        return False

def check_c_compiler():
    """检查 C 编译器"""
    print_section("C 编译器 (MSVC)")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True
        )
        if "cl.exe" in result.stdout or "cl " in result.stdout:
            for line in result.stdout.split('\n'):
                if 'compiler' in line.lower() or 'cl.exe' in line:
                    print(line.strip())
            print("状态: OK")
            return True
        else:
            print("状态: 错误 - 未找到 MSVC 编译器")
            print("请安装 Visual Studio Build Tools")
            return False
    except Exception as e:
        print(f"状态: 错误 - {e}")
        return False

def check_sherpa_onnx():
    """检查 sherpa-onnx 安装"""
    print_section("sherpa-onnx (本地转录)")
    try:
        import sherpa_onnx
        print(f"sherpa-onnx 版本: {sherpa_onnx.__version__ if hasattr(sherpa_onnx, '__version__') else 'Unknown'}")
        print(f"模块路径: {sherpa_onnx.__file__}")

        # 检查 C 扩展
        from sherpa_onnx.lib import _sherpa_onnx
        pyd_path = Path(_sherpa_onnx.__file__)
        pyd_size = pyd_path.stat().st_size / (1024*1024)
        print(f"C 扩展: {pyd_path.name} ({pyd_size:.2f} MB)")
        print("状态: OK (本地版)")
        return True
    except ImportError as e:
        print(f"状态: 未安装 - {e}")
        print("仅云端版: 如需本地转录，请运行: uv sync --extra local")
        return False

def check_dependencies():
    """检查关键依赖"""
    print_section("关键依赖")

    dependencies = {
        "PySide6": "GUI 框架",
        "numpy": "数值计算",
        "scipy": "科学计算",
        "sounddevice": "音频录制",
        "win32api": "Windows API",  # pywin32 的实际导入名称
        "pynput": "全局热键",
        "loguru": "日志系统",
        "requests": "HTTP 请求",
    }

    all_ok = True
    for module_name, description in dependencies.items():
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "Unknown")
            print(f"  {module_name:15} {version:15} - {description}")
        except ImportError:
            print(f"  {module_name:15} {'缺失':15} - {description}")
            all_ok = False

    if all_ok:
        print("\n状态: OK (所有依赖已安装)")
    else:
        print("\n状态: 错误 (缺少依赖)")
        print("请运行: uv sync")

    return all_ok

def check_resources():
    """检查资源文件"""
    print_section("资源文件")

    resources = [
        "src/sonicinput/resources/icons/app_icon.ico",
        "app.py",
        "pyproject.toml",
    ]

    all_ok = True
    for resource in resources:
        path = Path(resource)
        if path.exists():
            size = path.stat().st_size
            print(f"  {resource:50} ({size:,} bytes)")
        else:
            print(f"  {resource:50} 缺失")
            all_ok = False

    if all_ok:
        print("\n状态: OK")
    else:
        print("\n状态: 错误 (缺少资源)")

    return all_ok

def check_build_scripts():
    """检查构建脚本"""
    print_section("构建脚本")

    scripts = [
        ("build_nuitka.py", "本地版构建脚本"),
        ("build_nuitka_cloud.py", "云端版构建脚本"),
    ]

    all_ok = True
    for script, desc in scripts:
        path = Path(script)
        if path.exists():
            print(f"  {script:30} - {desc}")
        else:
            print(f"  {script:30} - 缺失")
            all_ok = False

    if all_ok:
        print("\n状态: OK")
    else:
        print("\n状态: 错误 (缺少脚本)")

    return all_ok

def main():
    """主函数"""
    print(f"\n{'='*60}")
    print("  SonicInput 构建配置验证")
    print(f"{'='*60}")

    results = {
        "Python 环境": check_python_version(),
        "Nuitka 编译器": check_nuitka(),
        "C 编译器": check_c_compiler(),
        "sherpa-onnx": check_sherpa_onnx(),
        "关键依赖": check_dependencies(),
        "资源文件": check_resources(),
        "构建脚本": check_build_scripts(),
    }

    # 总结
    print_section("验证总结")

    has_sherpa = results["sherpa-onnx"]

    for name, status in results.items():
        status_icon = "通过" if status else "失败"
        print(f"  {name:20} {status_icon}")

    print(f"\n{'='*60}")

    if all(v for k, v in results.items() if k != "sherpa-onnx"):
        if has_sherpa:
            print("  准备就绪: 可以构建本地版和云端版")
            print("  构建本地版: uv run python build_nuitka.py")
            print("  构建云端版: uv run python build_nuitka_cloud.py")
        else:
            print("  准备就绪: 可以构建云端版")
            print("  构建云端版: uv run python build_nuitka_cloud.py")
            print()
            print("  如需构建本地版:")
            print("    1. 安装 sherpa-onnx: uv sync --extra local")
            print("    2. 重新运行此脚本验证")
            print("    3. 构建本地版: uv run python build_nuitka.py")
    else:
        print("  环境未就绪，请根据上述错误修复问题")
        return 1

    print(f"{'='*60}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
