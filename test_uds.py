#!/usr/bin/env python3
"""
测试UDS功能的脚本
"""

import os
import sys
import time
import requests
import platform
import subprocess
from pathlib import Path

def test_uds_connection():
    """测试UDS连接功能"""
    print("=" * 60)
    print("测试UDS连接功能")
    print("=" * 60)
    
    # 检查系统平台
    current_platform = platform.system()
    print(f"当前系统平台: {current_platform}")
    
    if current_platform == "Windows":
        print("Windows系统不支持UDS，跳过测试")
        return False
    
    uds_path = "/tmp/zsim_api.sock"
    print(f"UDS路径: {uds_path}")
    
    # 清理旧的socket文件
    if os.path.exists(uds_path):
        print("清理旧的socket文件...")
        os.unlink(uds_path)
    
    # 启动后端服务器
    print("启动后端服务器...")
    backend_env = os.environ.copy()
    backend_env.update({
        "ZSIM_IPC_MODE": "uds",
        "ZSIM_UDS_PATH": uds_path
    })
    
    # 获取项目根目录
    script_dir = Path(__file__).parent
    backend_script = script_dir / "zsim" / "api.py"
    
    print(f"后端脚本路径: {backend_script}")
    
    if not backend_script.exists():
        print(f"错误: 后端脚本不存在: {backend_script}")
        return False
    
    # 启动后端进程
    backend_process = subprocess.Popen(
        ["python", str(backend_script)],
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # 等待服务器启动
        print("等待服务器启动...")
        time.sleep(5)
        
        # 检查socket文件是否存在
        if os.path.exists(uds_path):
            print("✓ UDS socket文件已创建")
        else:
            print("✗ UDS socket文件未创建")
            return False
        
        # 测试健康检查端点
        print("测试健康检查端点...")
        
        # 使用requests的Unix Socket适配器
        try:
            import requests_unixsocket
            
            session = requests_unixsocket.Session()
            url = f"http+unix://{uds_path}:/health"
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✓ 健康检查成功: {response.json()}")
            else:
                print(f"✗ 健康检查失败: {response.status_code}")
                return False
                
        except ImportError:
            print("requests_unixsocket 未安装，使用curl测试...")
            # 使用curl测试
            import subprocess as sp
            try:
                result = sp.run([
                    "curl", "-s", "--unix-socket", uds_path, 
                    "http://localhost/health"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"✓ 健康检查成功: {result.stdout}")
                else:
                    print(f"✗ 健康检查失败: {result.stderr}")
                    return False
            except sp.TimeoutExpired:
                print("✗ 健康检查超时")
                return False
        
        # 测试API端点
        print("测试API端点...")
        try:
            if 'requests_unixsocket' in sys.modules:
                url = f"http+unix://{uds_path}:/api/sessions/"
                response = session.get(url, timeout=10)
                
                if response.status_code == 200:
                    print(f"✓ API端点测试成功")
                    print(f"  响应: {response.json()}")
                else:
                    print(f"✗ API端点测试失败: {response.status_code}")
                    return False
            else:
                # 使用curl测试
                result = sp.run([
                    "curl", "-s", "--unix-socket", uds_path, 
                    "http://localhost/api/sessions/"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"✓ API端点测试成功")
                    print(f"  响应: {result.stdout}")
                else:
                    print(f"✗ API端点测试失败: {result.stderr}")
                    return False
                
        except Exception as e:
            print(f"✗ API端点测试异常: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("✓ 所有UDS测试通过")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    finally:
        # 清理
        print("清理进程...")
        backend_process.terminate()
        backend_process.wait(timeout=5)
        
        if os.path.exists(uds_path):
            os.unlink(uds_path)

def test_http_connection():
    """测试HTTP连接功能作为对比"""
    print("\n" + "=" * 60)
    print("测试HTTP连接功能")
    print("=" * 60)
    
    # 启动后端服务器
    print("启动后端服务器...")
    backend_env = os.environ.copy()
    backend_env.update({
        "ZSIM_IPC_MODE": "http",
        "ZSIM_API_PORT": "8001"
    })
    
    # 获取项目根目录
    script_dir = Path(__file__).parent
    backend_script = script_dir / "zsim" / "api.py"
    
    # 启动后端进程
    backend_process = subprocess.Popen(
        ["python", str(backend_script)],
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # 等待服务器启动
        print("等待服务器启动...")
        time.sleep(5)
        
        # 测试健康检查端点
        print("测试健康检查端点...")
        response = requests.get("http://127.0.0.1:8001/health", timeout=10)
        
        if response.status_code == 200:
            print(f"✓ 健康检查成功: {response.json()}")
        else:
            print(f"✗ 健康检查失败: {response.status_code}")
            return False
        
        # 测试API端点
        print("测试API端点...")
        response = requests.get("http://127.0.0.1:8001/api/sessions/", timeout=10)
        
        if response.status_code == 200:
            print(f"✓ API端点测试成功")
            print(f"  响应: {response.json()}")
        else:
            print(f"✗ API端点测试失败: {response.status_code}")
            return False
        
        print("\n" + "=" * 60)
        print("✓ 所有HTTP测试通过")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    finally:
        # 清理
        print("清理进程...")
        backend_process.terminate()
        backend_process.wait(timeout=5)

def main():
    """主函数"""
    print("ZSim UDS功能测试")
    print("=" * 60)
    
    # 测试HTTP连接
    http_success = test_http_connection()
    
    # 测试UDS连接
    uds_success = test_uds_connection()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"HTTP测试: {'✓ 通过' if http_success else '✗ 失败'}")
    print(f"UDS测试: {'✓ 通过' if uds_success else '✗ 失败'}")
    
    if http_success and uds_success:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print("\n❌ 部分测试失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main())