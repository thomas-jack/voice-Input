# ACT本地测试环境设置脚本 (Windows PowerShell版)

param(
    [switch]$SkipDockerPull
)

Write-Host "=== ACT Local CI/CD Test Setup ===" -ForegroundColor Green
Write-Host ""

# 检查必要工具
Write-Host "1. Checking required tools..." -ForegroundColor Yellow

# 检查ACT
try {
    $actVersion = & act --version 2>$null
    Write-Host "✓ act version: $actVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: act is not installed." -ForegroundColor Red
    Write-Host "Please install it first:" -ForegroundColor Yellow
    Write-Host "  Windows: choco install act-cli" -ForegroundColor Cyan
    exit 1
}

# 检查Docker
try {
    $dockerInfo = & docker info 2>$null
    Write-Host "✓ docker is available and running" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not installed or not running." -ForegroundColor Red
    Write-Host "Please install Docker Desktop and ensure it's running." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 拉取ACT基础镜像
if (-not $SkipDockerPull) {
    Write-Host "2. Pulling ACT base image..." -ForegroundColor Yellow
    try {
        & docker pull catthehacker/ubuntu:act-latest
        Write-Host "✓ Base image pulled" -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Failed to pull base image. You can pull it later with:" -ForegroundColor Yellow
        Write-Host "  docker pull catthehacker/ubuntu:act-latest" -ForegroundColor Cyan
    }
} else {
    Write-Host "2. Skipping Docker image pull (use -SkipDockerPull to skip)" -ForegroundColor Yellow
}

Write-Host ""

# 创建必要的目录
Write-Host "3. Creating directories..." -ForegroundColor Yellow
$directories = @(
    ".github\workflows",
    "scripts",
    "dist",
    "tests\ci\reports"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    } else {
        Write-Host "✓ Directory exists: $dir" -ForegroundColor Gray
    }
}

Write-Host ""

# 设置环境变量
Write-Host "4. Setting up environment variables..." -ForegroundColor Yellow
$env:CI = "true"
$env:GITHUB_ACTIONS = "true"
$env:GITHUB_REPOSITORY = "local-test/sonicinput"
$env:GITHUB_RUN_ID = "local_run_$(Get-Date -Format yyyyMMddHHmmss)"

try {
    $gitSha = & git rev-parse HEAD 2>$null
    $env:GITHUB_SHA = if ($gitSha) { $gitSha } else { "local_sha_unknown" }
} catch {
    $env:GITHUB_SHA = "local_sha_unknown"
}

$env:GITHUB_REF = "refs/heads/main"

Write-Host "✓ Environment variables set:" -ForegroundColor Green
Write-Host "  CI=$($env:CI)" -ForegroundColor Gray
Write-Host "  GITHUB_ACTIONS=$($env:GITHUB_ACTIONS)" -ForegroundColor Gray
Write-Host "  GITHUB_REPOSITORY=$($env:GITHUB_REPOSITORY)" -ForegroundColor Gray
Write-Host "  GITHUB_RUN_ID=$($env:GITHUB_RUN_ID)" -ForegroundColor Gray
Write-Host "  GITHUB_SHA=$($env:GITHUB_SHA)" -ForegroundColor Gray
Write-Host "  GITHUB_REF=$($env:GITHUB_REF)" -ForegroundColor Gray

Write-Host ""

# 显示可用的workflows
Write-Host "5. Available workflows:" -ForegroundColor Yellow

if (Test-Path ".github\workflows\ci.yml") {
    Write-Host "  - CI Tests (Linux)" -ForegroundColor Green
    Write-Host "    Command: act -j lint" -ForegroundColor Cyan
    Write-Host "    Command: act -j test" -ForegroundColor Cyan
    Write-Host "    Command: act -j quick-test" -ForegroundColor Cyan
    Write-Host "    Command: act -j security" -ForegroundColor Cyan
}

if (Test-Path ".github\workflows\build.yml") {
    Write-Host "  - Build (Windows) - NOT AVAILABLE IN ACT" -ForegroundColor Yellow
    Write-Host "    Reason: ACT doesn't support Windows runners" -ForegroundColor Gray
    Write-Host "    Alternative: Run locally with uv run nuitka ..." -ForegroundColor Cyan
}

Write-Host ""

# 快速验证脚本
Write-Host "6. Quick verification..." -ForegroundColor Yellow

# 验证workflows语法
if (Test-Path ".github\workflows\ci.yml") {
    try {
        # 简单的YAML语法检查
        $content = Get-Content ".github\workflows\ci.yml" -Raw
        if ($content) {
            Write-Host "✓ CI workflow file exists and readable" -ForegroundColor Green
        }
    } catch {
        Write-Host "WARNING: CI workflow file may have issues" -ForegroundColor Yellow
    }
}

# 验证测试套件
if (Test-Path "tests\ci\run_ci_tests.py") {
    Write-Host "✓ CI test suite exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""

Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  # Run all CI tests" -ForegroundColor Gray
Write-Host "  act -j test" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Run quick tests only" -ForegroundColor Gray
Write-Host "  act -j quick-test" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Run linting" -ForegroundColor Gray
Write-Host "  act -j lint" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Check available jobs" -ForegroundColor Gray
Write-Host "  act -l" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Run with specific event" -ForegroundColor Gray
Write-Host "  act -j test -e push" -ForegroundColor Cyan
Write-Host ""
Write-Host "Windows-specific:" -ForegroundColor Yellow
Write-Host "  # Run local Windows build (not through ACT)" -ForegroundColor Gray
Write-Host "  uv run nuitka --standalone --onefile --windows-console-mode=disable --enable-plugin=pyside6 --include-package=sonicinput --nofollow-import-to=pytest --nofollow-import-to=mypy --windows-icon-from-ico=src/sonicinput/resources/icons/app_icon.ico --output-dir=dist app.py" -ForegroundColor Cyan
Write-Host ""