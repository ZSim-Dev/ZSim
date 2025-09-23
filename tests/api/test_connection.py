#!/usr/bin/env python3
"""
简单的前后端连接测试
"""

import json
import os
import subprocess
import sys


def test_backend_connection():
    """测试后端连接"""
    print("测试后端连接...")

    # 测试UDS连接
    uds_path = "/tmp/zsim_api.sock"

    if os.path.exists(uds_path):
        print(f"✓ UDS socket文件存在: {uds_path}")

        try:
            # 使用curl测试UDS连接
            # 测试健康检查
            result = subprocess.run(
                ["curl", "-s", "--unix-socket", uds_path, "http://localhost/health"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                print(f"✓ 健康检查成功: {data}")
            else:
                print(f"✗ 健康检查失败: {result.stderr}")
                return None

            # 测试API端点
            result = subprocess.run(
                ["curl", "-s", "--unix-socket", uds_path, "http://localhost/api/sessions/"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                print(f"✓ API端点测试成功: {data}")
            else:
                print(f"✗ API端点测试失败: {result.stderr}")
                return None

            return True

        except Exception as e:
            print(f"✗ UDS连接测试失败: {e}")
            return None
    else:
        print(f"✗ UDS socket文件不存在: {uds_path}")
        return None


def test_http_fallback():
    """测试HTTP回退连接"""
    print("\n测试HTTP回退连接...")

    try:
        # 尝试使用curl测试常见的端口
        for port in [8000, 8001, 8002]:
            try:
                result = subprocess.run(
                    ["curl", "-s", f"http://127.0.0.1:{port}/health"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )

                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    print(f"✓ HTTP连接成功 (端口 {port}): {data}")

                    # 测试API端点
                    api_result = subprocess.run(
                        ["curl", "-s", f"http://127.0.0.1:{port}/api/sessions/"],
                        capture_output=True,
                        text=True,
                    )

                    if api_result.returncode == 0:
                        api_data = json.loads(api_result.stdout)
                        print(f"✓ API端点测试成功: {api_data}")
                        return True
                    else:
                        print(f"✗ API端点测试失败: {api_result.stderr}")
                        return False
            except Exception:
                continue

        print("✗ 未找到可用的HTTP端口")
        return False

    except Exception as e:
        print(f"✗ HTTP连接测试失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("前后端连接测试")
    print("=" * 50)

    # 测试UDS连接
    uds_success = test_backend_connection()

    # 如果UDS失败，测试HTTP回退
    if not uds_success:
        http_success = test_http_fallback()
    else:
        http_success = False

    print("\n" + "=" * 50)
    print("测试结果")
    print("=" * 50)
    print(f"UDS连接: {'✓ 成功' if uds_success else '✗ 失败'}")
    print(f"HTTP连接: {'✓ 成功' if http_success else '✗ 失败/未测试'}")

    if uds_success or http_success:
        print("\n🎉 后端连接正常!")
        return 0
    else:
        print("\n❌ 后端连接失败!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
