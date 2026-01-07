#!/usr/bin/env python
"""
Nuitka compilation script - Cloud-only version (no sherpa-onnx)

This script compiles SonicInput cloud version without local transcription support.
Smaller file size, only supports online transcription services (Groq/SiliconFlow/Qwen).
"""

import subprocess
import sys
from pathlib import Path
import shutil


# Read version number
def get_version():
    """Read version from pyproject.toml"""
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        with open(pyproject, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("version ="):
                    # Extract version: version = "0.1.2" -> 0.1.2
                    return line.split('"')[1]
    return "0.0.0"


version = get_version()
print(f"Building SonicInput Cloud v{version}")
print("NOTE: This version does NOT include local transcription (sherpa-onnx)")
print("      Only online transcription services are supported.\n")

# Nuitka command for cloud-only version
nuitka_cmd = [
    sys.executable,
    "-m",
    "nuitka",
    "--standalone",  # Create standalone distribution
    "--onefile",  # Package everything into single .exe
    "--windows-console-mode=disable",  # GUI mode (no console window)
    "--enable-plugin=pyside6",  # Enable PySide6 plugin for Qt support
    # Package inclusions
    "--include-package=sonicinput",  # Main application package
    "--include-data-dir=assets=assets",  # UI translations/fonts and other assets
    # Exclude test/dev dependencies and local transcription
    "--nofollow-import-to=pytest",
    "--nofollow-import-to=mypy",
    "--nofollow-import-to=tests",
    "--nofollow-import-to=sherpa_onnx",  # Exclude sherpa-onnx for cloud version
    # Application metadata
    "--windows-icon-from-ico=src/sonicinput/resources/icons/app_icon.ico",
    "--output-dir=dist",
    "app.py",
]

print("\nRunning Nuitka compilation...\n")
print(f"Command: {' '.join(nuitka_cmd)}\n")

# Execute compilation
result = subprocess.run(nuitka_cmd)

if result.returncode == 0:
    # Compilation successful, rename output file
    dist_dir = Path("dist")
    old_name = dist_dir / "app.exe"
    new_name = dist_dir / f"SonicInput-v{version}-win64-cloud.exe"

    if old_name.exists():
        # Delete target file if exists
        if new_name.exists():
            new_name.unlink()

        # Rename
        shutil.move(str(old_name), str(new_name))
        print("\n[SUCCESS] Cloud build successful!")
        print(f"[OUTPUT] {new_name}")
        print(f"[SIZE] {new_name.stat().st_size / (1024 * 1024):.2f} MB")
        print("\n[NOTE] This version requires internet connection for transcription.")
        print("       Supported services: Groq, SiliconFlow, Qwen")
    else:
        print(f"\n[WARNING] Expected output file not found: {old_name}")
        # List dist directory contents
        if dist_dir.exists():
            print("\nFiles in dist directory:")
            for file in dist_dir.iterdir():
                print(f"  - {file.name}")
else:
    print(f"\n[ERROR] Build failed with exit code {result.returncode}")

sys.exit(result.returncode)
