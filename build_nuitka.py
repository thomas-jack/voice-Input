#!/usr/bin/env python
"""
Nuitka compilation script - Package as single file executable

This script compiles SonicInput into a standalone Windows executable using Nuitka.
Includes support for sherpa-onnx C extension modules and all required dependencies.
"""

import shutil
import string
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree


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


def _collect_translation_text(assets_dir: Path) -> str:
    text_chunks = []
    i18n_dir = assets_dir / "i18n"
    for ts_file in sorted(i18n_dir.glob("*.ts")):
        try:
            tree = ElementTree.parse(ts_file)
        except Exception:
            continue
        root = tree.getroot()
        for elem in root.iter():
            if elem.tag in {"source", "translation"} and elem.text:
                text_chunks.append(elem.text)

    base_chars = (
        string.ascii_letters
        + string.digits
        + " .,:;!?\"'()[]{}<>+-=*/\\\\|@#$%^&~`_"
        + "\n\r\t"
    )
    text_chunks.append(base_chars)
    unique_chars = sorted(set("".join(text_chunks)))
    return "".join(unique_chars)


def _subset_font(source_font: Path, target_font: Path, text: str) -> None:
    try:
        from fontTools.subset import Options, Subsetter
        from fontTools.ttLib import TTFont
    except Exception as exc:
        raise RuntimeError(
            "fontTools is required to subset bundled fonts. "
            "Install build dependencies (e.g., uv sync --group dev)."
        ) from exc

    options = Options()
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]
    options.notdef_glyph = True
    options.notdef_outline = True
    options.recalc_bounds = True
    options.recalc_timestamp = True
    options.prune_unicode_ranges = True

    font = TTFont(str(source_font))
    subsetter = Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    target_font.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(target_font))


def stage_assets() -> Path:
    assets_dir = Path("assets")
    staging_dir = Path("build") / "assets_staging"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    # Copy icon
    shutil.copy2(assets_dir / "icon.png", staging_dir / "icon.png")

    # Copy compiled translations only
    i18n_dir = staging_dir / "i18n"
    i18n_dir.mkdir(parents=True, exist_ok=True)
    for qm_file in (assets_dir / "i18n").glob("*.qm"):
        shutil.copy2(qm_file, i18n_dir / qm_file.name)

    # Subset bundled fonts
    font_source_dir = assets_dir / "fonts" / "resource-han-rounded"
    font_target_dir = staging_dir / "fonts" / "resource-han-rounded"
    font_target_dir.mkdir(parents=True, exist_ok=True)
    subset_text = _collect_translation_text(assets_dir)
    for font_name in [
        "ResourceHanRoundedCN-Regular.ttf",
        "ResourceHanRoundedCN-Bold.ttf",
    ]:
        _subset_font(
            font_source_dir / font_name, font_target_dir / font_name, subset_text
        )

    # Copy font license/notice
    for doc_name in ["OFL-License.txt", "FONT-NOTICE.txt"]:
        shutil.copy2(font_source_dir / doc_name, font_target_dir / doc_name)

    return staging_dir


version = get_version()
print(f"Building SonicInput v{version}")

staged_assets_dir = stage_assets()
print(f"Using staged assets: {staged_assets_dir}")

# Nuitka command with sherpa-onnx support
nuitka_cmd = [
    sys.executable,
    "-m",
    "nuitka",
    "--standalone",  # Create standalone distribution
    "--onefile",  # Package everything into single .exe
    "--windows-console-mode=attach",  # Attach to console when launched from cmd, GUI when double-clicked
    "--enable-plugin=pyside6",  # Enable PySide6 plugin for Qt support
    # Package inclusions
    "--include-package=sonicinput",  # Main application package
    "--include-package=sherpa_onnx",  # sherpa-onnx package (local ASR engine, includes C extension)
    # Note: Removed --include-package-data=sherpa_onnx due to 'nul' file issue
    # The .pyd extension module will be included automatically
    "--include-module=sonicinput.utils.constants",  # Ensure constants.py is included
    f"--include-data-dir={staged_assets_dir}=assets",  # UI translations/fonts and other assets
    # Windows API dependencies (for clipboard input and GUI operations)
    "--include-package=win32clipboard",  # Clipboard operations (clipboard input method)
    "--include-package=win32con",  # Windows constants
    "--include-package=win32api",  # Windows API wrapper
    "--include-package=win32gui",  # Windows GUI operations
    "--include-package=pywintypes",  # pywin32 base types
    # pynput backend support (alternative hotkey manager)
    "--include-package=pynput",  # pynput library for keyboard/mouse control
    # Exclude test/dev dependencies
    "--nofollow-import-to=pytest",
    "--nofollow-import-to=mypy",
    "--nofollow-import-to=tests",
    "--nofollow-import-to=scipy",
    "--nofollow-import-to=PySide6.QtPdf",
    "--nofollow-import-to=PySide6.QtOpenGL",
    "--noinclude-dlls=qt6pdf.dll",
    "--noinclude-dlls=qt6opengl.dll",
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
    new_name = dist_dir / f"SonicInput-v{version}-win64.exe"

    if old_name.exists():
        # Delete target file if exists
        if new_name.exists():
            new_name.unlink()

        # Rename
        shutil.move(str(old_name), str(new_name))
        print("\n[SUCCESS] Build successful!")
        print(f"[OUTPUT] {new_name}")
        print(f"[SIZE] {new_name.stat().st_size / (1024 * 1024):.2f} MB")
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
