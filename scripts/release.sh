#!/bin/bash

# ZSim 版本发布脚本
# 使用方法: ./scripts/release.sh [patch|minor|major|alpha|beta] [--draft] [--prerelease]

set -e

# 默认参数
RELEASE_TYPE="patch"
DRAFT=false
PRERELEASE=false
MULTI_PLATFORM=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        patch|minor|major|alpha|beta)
            RELEASE_TYPE="$1"
            shift
            ;;
        --draft)
            DRAFT=true
            shift
            ;;
        --prerelease)
            PRERELEASE=true
            shift
            ;;
        --multi-platform)
            MULTI_PLATFORM=true
            shift
            ;;
        --help)
            echo "用法: $0 [patch|minor|major|alpha|beta] [--draft] [--prerelease] [--multi-platform]"
            echo ""
            echo "参数说明:"
            echo "  patch|minor|major|alpha|beta  发布类型"
            echo "  --draft                    创建草稿发布"
            echo "  --prerelease               标记为预发布"
            echo "  --multi-platform           构建多平台版本（仅macOS）"
            echo "  --help                     显示帮助信息"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

echo "🚀 开始 ZSim 版本发布流程"
echo "📋 发布配置:"
echo "   - 发布类型: $RELEASE_TYPE"
echo "   - 草稿发布: $DRAFT"
echo "   - 预发布: $PRERELEASE"
echo "   - 多平台构建: $MULTI_PLATFORM"
echo ""

# 检查当前工作目录是否为 git 仓库
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 错误: 当前目录不是 git 仓库"
    exit 1
fi

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo "❌ 错误: 存在未提交的更改"
    echo "请先提交所有更改后再进行发布"
    exit 1
fi

# 检查是否在主分支
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
    echo "❌ 错误: 当前不在主分支 ($CURRENT_BRANCH)"
    echo "请切换到 main 或 master 分支进行发布"
    exit 1
fi

# 获取当前版本
echo "📖 获取当前版本信息..."
CURRENT_BACKEND_VERSION=$(uv version --short)
CURRENT_FRONTEND_VERSION=$(cd electron-app && node -p "require('./package.json').version")
echo "   - 后端版本: $CURRENT_BACKEND_VERSION"
echo "   - 前端版本: $CURRENT_FRONTEND_VERSION"
echo ""

# 更新版本号
echo "🔄 更新版本号..."
if [[ "$RELEASE_TYPE" == "alpha" || "$RELEASE_TYPE" == "beta" ]]; then
    echo "更新后端版本..."
    uv version --bump prerelease --pre-token "$RELEASE_TYPE"
    echo "更新前端版本..."
    cd electron-app && pnpm version prerelease --preid "$RELEASE_TYPE" --no-git-tag-version && cd ..
else
    echo "更新后端版本..."
    uv version --bump "$RELEASE_TYPE"
    echo "更新前端版本..."
    cd electron-app && pnpm version "$RELEASE_TYPE" --no-git-tag-version && cd ..
fi

# 获取新版本
NEW_BACKEND_VERSION=$(uv version --short)
NEW_FRONTEND_VERSION=$(cd electron-app && node -p "require('./package.json').version")
echo "✅ 版本更新完成:"
echo "   - 新后端版本: $NEW_BACKEND_VERSION"
echo "   - 新前端版本: $NEW_FRONTEND_VERSION"
echo ""

# 构建应用
echo "🔨 构建应用..."
make clean

# 检测系统并选择构建模式
UNAME_S=$(uname -s)
if [[ "$MULTI_PLATFORM" == "true" ]]; then
    if [[ "$UNAME_S" == "Darwin" ]]; then
        echo "🍎 检测到 macOS，启用交叉编译构建所有平台..."
        make cross-build-all
    else
        echo "❌ 错误: 多平台构建仅在 macOS 上支持"
        echo "🖥️ 回退到构建当前平台版本..."
        make build
    fi
else
    echo "🖥️ 检测到 $UNAME_S，构建当前平台版本..."
    make build
fi
echo "✅ 构建完成"
echo ""

# 提交版本更改
echo "💾 提交版本更改..."
git config --local user.email "action@github.com"
git config --local user.name "GitHub Action"
git add pyproject.toml electron-app/package.json
git commit -m "release: 版本发布 $NEW_BACKEND_VERSION

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 创建标签
echo "🏷️ 创建版本标签..."
git tag -a "v$NEW_BACKEND_VERSION" -m "Version $NEW_BACKEND_VERSION"

# 推送更改
echo "📤 推送更改到远程仓库..."
git push origin main
git push origin "v$NEW_BACKEND_VERSION"
echo "✅ 推送完成"
echo ""

# 生成发布说明
echo "📝 生成发布说明..."
cat > release_notes.md << EOF
## 🎉 ZSim $NEW_BACKEND_VERSION Release

### 📦 版本信息
- 后端版本: $NEW_BACKEND_VERSION
- 前端版本: $NEW_FRONTEND_VERSION

### 🚀 更新内容
#### ✨ 新功能
- 待添加

#### 🐛 问题修复
- 待添加

#### 🔧 性能优化
- 待添加

### 📋 安装说明
1. 下载对应平台的安装包
2. 运行安装程序
3. 启动 ZSim 应用

### 📁 下载文件
- Windows: \`ZSim-Setup-$NEW_BACKEND_VERSION.exe\`
- macOS: \`ZSim-$NEW_BACKEND_VERSION.dmg\`
- Linux: \`ZSim-$NEW_BACKEND_VERSION.AppImage\`

---

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF

echo "✅ 发布说明已生成: release_notes.md"
echo ""

# 创建 GitHub Release (如果安装了 gh cli)
if command -v gh &> /dev/null; then
    echo "🎯 创建 GitHub Release..."
    
    # 准备文件列表
    FILES=$(find electron-app/release -type f \( -name "*.exe" -o -name "*.dmg" -o -name "*.AppImage" -o -name "*.deb" -o -name "*.zip" -o -name "*.blockmap" \) | tr '\n' ' ')
    
    # 创建发布
    if [[ "$DRAFT" == "true" ]]; then
        gh release create "v$NEW_BACKEND_VERSION" $FILES --title "ZSim $NEW_BACKEND_VERSION" --notes-file release_notes.md --draft
    elif [[ "$PRERELEASE" == "true" ]]; then
        gh release create "v$NEW_BACKEND_VERSION" $FILES --title "ZSim $NEW_BACKEND_VERSION" --notes-file release_notes.md --prerelease
    else
        gh release create "v$NEW_BACKEND_VERSION" $FILES --title "ZSim $NEW_BACKEND_VERSION" --notes-file release_notes.md
    fi
    
    echo "✅ GitHub Release 创建完成"
else
    echo "⚠️  GitHub CLI 未安装，跳过自动创建 Release"
    echo "请手动创建 Release 并上传文件"
fi

echo ""
echo "🎉 版本发布流程完成！"
echo "📋 后续操作:"
echo "   1. 编辑 release_notes.md 添加具体的更新内容"
echo "   2. 如果未自动创建 Release，请手动创建"
echo "   3. 通知用户更新"
echo ""

# 清理
rm -f release_notes.md