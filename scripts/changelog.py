#!/usr/bin/env python3
"""
ZSim Changelog 生成工具
用于生成版本发布说明和更新日志
"""

import argparse
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def get_current_version() -> str:
    """获取当前版本号"""
    try:
        result = subprocess.run(["uv", "version", "--short"], capture_output=True, text=True)
        return result.stdout.strip()
    except FileNotFoundError:
        # 读取 pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
                return pyproject_data["project"]["version"]
        return "unknown"


def get_git_commits(since_tag: str | None = None) -> List[Dict[str, Any]]:
    """获取 git 提交记录"""
    try:
        if since_tag:
            cmd = ["git", "log", f"{since_tag}..HEAD", "--pretty=format:%H|%s|%an|%ae"]
        else:
            cmd = ["git", "log", "--pretty=format:%H|%s|%an|%ae"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        commits = []

        for line in result.stdout.strip().split("\n"):
            if line:
                commit_hash, subject, author, email = line.split("|")
                commits.append(
                    {"hash": commit_hash, "subject": subject, "author": author, "email": email}
                )

        return commits
    except subprocess.CalledProcessError:
        return []


def categorize_commits(commits: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """按类型分类提交"""
    categories = {
        "✨ 新功能": [],
        "🐛 问题修复": [],
        "🔧 性能优化": [],
        "📝 文档更新": [],
        "🎨 界面优化": [],
        "🧹 代码重构": [],
        "🔒 安全修复": [],
        "🧪 测试相关": [],
        "📦 构建系统": [],
        "🔄 其他更新": [],
    }

    for commit in commits:
        subject = commit["subject"]

        # 跳过合并提交和版本发布提交
        if subject.startswith("Merge ") or subject.startswith("release:"):
            continue

        # 根据提交信息前缀分类
        if any(keyword in subject.lower() for keyword in ["feat:", "add:", "新增", "添加"]):
            categories["✨ 新功能"].append(subject)
        elif any(keyword in subject.lower() for keyword in ["fix:", "bug", "修复", "问题"]):
            categories["🐛 问题修复"].append(subject)
        elif any(keyword in subject.lower() for keyword in ["perf:", "optim", "优化", "性能"]):
            categories["🔧 性能优化"].append(subject)
        elif any(keyword in subject.lower() for keyword in ["docs:", "readme", "文档"]):
            categories["📝 文档更新"].append(subject)
        elif any(keyword in subject.lower() for keyword in ["ui:", "style:", "界面", "样式"]):
            categories["🎨 界面优化"].append(subject)
        elif any(keyword in subject.lower() for keyword in ["refactor:", "重构"]):
            categories["🧹 代码重构"].append(subject)
        elif any(keyword in subject.lower() for keyword in ["security:", "安全"]):
            categories["🔒 安全修复"].append(subject)
        elif any(keyword in subject.lower() for keyword in ["test:", "测试"]):
            categories["🧪 测试相关"].append(subject)
        elif any(keyword in subject.lower() for keyword in ["build:", "ci:", "makefile", "构建"]):
            categories["📦 构建系统"].append(subject)
        else:
            categories["🔄 其他更新"].append(subject)

    return categories


def generate_changelog(version: str, previous_version: str | None = None) -> str:
    """生成更新日志"""
    current_date = datetime.now().strftime("%Y-%m-%d")

    # 获取提交记录
    commits = get_git_commits(previous_version)
    categories = categorize_commits(commits)

    # 获取前端版本
    try:
        with open("electron-app/package.json", "r") as f:
            import json

            package_data = json.load(f)
            frontend_version = package_data["version"]
    except Exception:
        frontend_version = "unknown"

    # 生成 changelog
    changelog = f"""## 🎉 ZSim {version} Release

**发布日期**: {current_date}

### 📦 版本信息
- 后端版本: {version}
- 前端版本: {frontend_version}

### 🚀 更新内容
"""

    # 添加各类更新
    for category, items in categories.items():
        if items:
            changelog += f"#### {category}\n"
            for item in items:
                changelog += f"- {item}\n"
            changelog += "\n"

    # 添加统计信息
    total_commits = len(
        [
            c
            for c in commits
            if not c["subject"].startswith("Merge ") and not c["subject"].startswith("release:")
        ]
    )
    changelog += "### 📊 统计信息\n"
    changelog += f"- 本次更新包含 {total_commits} 个提交\n"

    # 添加安装说明
    changelog += f"""
### 📋 安装说明
1. 下载对应平台的安装包
2. 运行安装程序
3. 启动 ZSim 应用

### 📁 下载文件
- Windows: `ZSim-Setup-{version}.exe`
- macOS: `ZSim-{version}.dmg`
- Linux: `ZSim-{version}.AppImage`

### 🔄 升级说明
- 从旧版本升级时，建议先卸载旧版本
- 配置文件会自动保留
- 如遇问题，请删除配置文件后重新安装

---
"""

    return changelog


def update_changelog_file(changelog_content: str):
    """更新 CHANGELOG.md 文件"""
    changelog_path = Path("CHANGELOG.md")

    if changelog_path.exists():
        # 读取现有内容
        with open(changelog_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # 在开头添加新的 changelog
        new_content = changelog_content + "\n\n" + existing_content
    else:
        # 创建新文件
        new_content = "# 📋 ZSim 更新日志\n\n" + changelog_content

    # 写入文件
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ 已更新 {changelog_path}")


def main():
    parser = argparse.ArgumentParser(description="生成 ZSim 版本更新日志")
    parser.add_argument("--version", "-v", help="指定版本号")
    parser.add_argument("--previous", "-p", help="指定上一个版本号")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--update-changelog", action="store_true", help="更新 CHANGELOG.md 文件")

    args = parser.parse_args()

    # 获取版本号
    version = args.version or get_current_version()
    if version == "unknown":
        print("❌ 无法获取版本号，请手动指定")
        sys.exit(1)

    # 生成 changelog
    changelog_content = generate_changelog(version, args.previous)

    # 输出到文件或控制台
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(changelog_content)
        print(f"✅ 已保存到 {args.output}")
    else:
        print(changelog_content)

    # 更新 CHANGELOG.md
    if args.update_changelog:
        update_changelog_file(changelog_content)


if __name__ == "__main__":
    main()
