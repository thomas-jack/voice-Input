#!/usr/bin/env python3
"""
CI测试运行器

专门为CI环境设计的测试运行脚本：
1. 自动检测CI环境
2. 配置合适的测试参数
3. 提供详细的测试报告
4. 处理CI特定的配置
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import time


def is_ci_environment():
    """检测是否在CI环境中"""
    return any([
        os.getenv("CI"),
        os.getenv("GITHUB_ACTIONS"),
        os.getenv("GITLAB_CI"),
        os.getenv("TRAVIS"),
        os.getenv("APPVEYOR"),
        os.getenv("JENKINS_URL"),
        os.getenv("CIRCLECI"),
    ])


def get_ci_config():
    """获取CI环境配置"""
    return {
        "timeout": "30",  # 30秒超时
        "parallel": "auto",  # 自动并行
        "verbose": True,  # 详细输出
        "color": "yes",  # 彩色输出
        "durations": "10",  # 显示最慢的10个测试
        "markers": "not slow and not gpu and not gui",  # 排除慢速、GPU、GUI测试
    }


def run_unit_tests(ci_config):
    """运行单元测试"""
    print("=" * 60)
    print("Running Unit Tests")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        f"--timeout={ci_config['timeout']}",
        "-m", "unit",
        "--disable-warnings",
    ]

    if is_ci_environment():
        cmd.extend([
            "--junit-xml=reports/unit-tests.xml",
            "--html=reports/unit-tests.html",
            "--self-contained-html",
        ])

    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


def run_integration_tests(ci_config):
    """运行集成测试"""
    print("=" * 60)
    print("Running Integration Tests")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        f"--timeout={ci_config['timeout']}",
        "-m", "integration",
        "--disable-warnings",
    ]

    if is_ci_environment():
        cmd.extend([
            "--junit-xml=reports/integration-tests.xml",
            "--html=reports/integration-tests.html",
            "--self-contained-html",
        ])

    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


def run_all_ci_tests(ci_config):
    """运行所有CI测试"""
    print("=" * 60)
    print("CI Tests Starting")
    print("=" * 60)
    print(f"Environment: {'CI' if is_ci_environment() else 'Local'}")
    print(f"Timeout: {ci_config['timeout']}s")
    print(f"Test Markers: {ci_config['markers']}")
    print()

    start_time = time.time()

    # 确保报告目录存在
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    # 运行测试
    results = {}

    try:
        results["unit"] = run_unit_tests(ci_config)
    except Exception as e:
        print(f"Unit Tests Failed: {e}")
        results["unit"] = False

    try:
        results["integration"] = run_integration_tests(ci_config)
    except Exception as e:
        print(f"Integration Tests Failed: {e}")
        results["integration"] = False

    # 汇总结果
    end_time = time.time()
    duration = end_time - start_time

    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Total Duration: {duration:.2f}s")
    print(f"Unit Tests: {'PASS' if results['unit'] else 'FAIL'}")
    print(f"Integration Tests: {'PASS' if results['integration'] else 'FAIL'}")

    overall_success = all(results.values())
    print(f"Overall Result: {'ALL PASS' if overall_success else 'SOME FAIL'}")

    if is_ci_environment():
        # 生成CI特定的报告
        summary_file = reports_dir / "ci-summary.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"CI Test Summary\n")
            f.write(f"{'='*50}\n")
            f.write(f"Duration: {duration:.2f}s\n")
            f.write(f"Unit Tests: {'PASS' if results['unit'] else 'FAIL'}\n")
            f.write(f"Integration Tests: {'PASS' if results['integration'] else 'FAIL'}\n")
            f.write(f"Overall: {'PASS' if overall_success else 'FAIL'}\n")

    return overall_success


def run_quick_tests():
    """快速测试模式 - 只运行最重要的测试"""
    print("=" * 60)
    print("Quick Test Mode")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        "--timeout=10",
        "-m", "unit",
    ]

    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="CI测试运行器")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="只运行快速测试"
    )
    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="只运行单元测试"
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="只运行集成测试"
    )
    parser.add_argument(
        "--timeout",
        default="30",
        help="测试超时时间（秒）"
    )

    args = parser.parse_args()

    ci_config = get_ci_config()
    if args.timeout != "30":
        ci_config["timeout"] = args.timeout

    # 创建报告目录
    if is_ci_environment():
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)

    success = True

    if args.quick:
        success = run_quick_tests()
    elif args.unit_only:
        success = run_unit_tests(ci_config)
    elif args.integration_only:
        success = run_integration_tests(ci_config)
    else:
        success = run_all_ci_tests(ci_config)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()