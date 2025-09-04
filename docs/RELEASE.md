# ZSim 版本发布指南

## 🚀 发布方式

### 1. GitHub Actions 自动发布（推荐）

使用 GitHub Actions 进行自动化版本发布：

1. 访问仓库的 Actions 页面
2. 选择 "Release" 工作流
3. 点击 "Run workflow"
4. 选择发布类型：
   - `patch` - 小版本更新 (1.0.0 → 1.0.1)
   - `minor` - 次版本更新 (1.0.0 → 1.1.0)
   - `major` - 主版本更新 (1.0.0 → 2.0.0)
   - `alpha` - Alpha 预发布 (1.0.0 → 1.0.1-alpha.0)
   - `beta` - Beta 预发布 (1.0.0 → 1.0.1-beta.0)
5. 选择是否创建草稿或预发布
6. 点击 "Run workflow"

### 2. 本地脚本发布

使用本地脚本进行发布：

```bash
# 基本发布
./scripts/release.sh patch

# 预发布
./scripts/release.sh alpha --prerelease

# 草稿发布
./scripts/release.sh minor --draft

# 查看帮助
./scripts/release.sh --help
```

### 3. 手动发布

如果自动发布失败，可以手动进行：

```bash
# 更新版本号
uv version --bump patch
cd electron-app && pnpm version patch --no-git-tag-version && cd ..

# 构建
make clean
make backend
make electron-build

# 提交更改
git add pyproject.toml electron-app/package.json
git commit -m "release: 版本发布 x.x.x"

# 创建标签
git tag -a "vx.x.x" -m "Version x.x.x"

# 推送
git push origin main
git push origin vx.x.x
```

## 📋 发布前检查清单

- [ ] 所有测试通过
- [ ] 代码格式化检查通过
- [ ] 类型检查通过
- [ ] 文档更新
- [ ] CHANGELOG 更新
- [ ] 版本号正确
- [ ] 构建测试通过

## 📝 更新日志生成

### 自动生成

```bash
# 生成当前版本的更新日志
./scripts/changelog.py --update-changelog

# 指定版本号
./scripts/changelog.py --version 1.0.1 --update-changelog

# 输出到文件
./scripts/changelog.py --version 1.0.1 --output release_notes.md
```

### 手动编辑

自动生成的更新日志可能需要手动调整，特别是：

1. 添加详细的更新说明
2. 修复分类错误
3. 添加重要提醒
4. 添加已知问题

## 📦 发布内容

### 自动发布的构建产物

- Windows: `ZSim-Setup-x.x.x.exe`
- macOS: `ZSim-x.x.x.dmg`
- Linux: `ZSim-x.x.x.AppImage`

### 发布说明模板

```markdown
## 🎉 ZSim x.x.x Release

### 📦 版本信息
- 后端版本: x.x.x
- 前端版本: x.x.x

### 🚀 更新内容
#### ✨ 新功能
- 功能1说明
- 功能2说明

#### 🐛 问题修复
- 问题1修复
- 问题2修复

#### 🔧 性能优化
- 优化1说明
- 优化2说明

### 📋 安装说明
1. 下载对应平台的安装包
2. 运行安装程序
3. 启动 ZSim 应用

### 📁 下载文件
- Windows: `ZSim-Setup-x.x.x.exe`
- macOS: `ZSim-x.x.x.dmg`
- Linux: `ZSim-x.x.x.AppImage`

### 🔄 升级说明
- 从旧版本升级时，建议先卸载旧版本
- 配置文件会自动保留
- 如遇问题，请删除配置文件后重新安装
```

## 🔧 版本号规范

遵循 [Semantic Versioning](https://semver.org/) 规范：

- `MAJOR.MINOR.PATCH`
- `1.0.0` - 主版本.次版本.修订版本
- `1.0.0-alpha.1` - Alpha 预发布
- `1.0.0-beta.1` - Beta 预发布

### 版本号更新规则

- **PATCH**: 修复错误，向后兼容
- **MINOR**: 添加功能，向后兼容
- **MAJOR**: 破坏性更改，不向后兼容

## 🚨 回滚发布

如果发布出现问题，需要回滚：

```bash
# 删除远程标签
git push origin --delete vx.x.x

# 删除本地标签
git tag -d vx.x.x

# 回滚提交
git reset --hard HEAD~1

# 强制推送
git push origin main --force
```

## 📊 发布后任务

1. **通知用户**
   - 在社区发布公告
   - 更新应用商店描述
   - 发送版本更新通知

2. **监控反馈**
   - 关注用户反馈
   - 监控错误报告
   - 收集功能建议

3. **文档更新**
   - 更新 README
   - 更新用户指南
   - 更新 API 文档

4. **数据分析**
   - 分析下载量
   - 统计用户活跃度
   - 收集使用数据

## 🔍 故障排除

### 常见问题

1. **构建失败**
   - 检查依赖是否安装
   - 确认环境变量设置
   - 查看构建日志

2. **版本号冲突**
   - 确认版本号唯一性
   - 检查标签是否存在
   - 清理本地缓存

3. **权限问题**
   - 确认 GitHub Token 权限
   - 检查仓库设置
   - 验证用户权限

### 获取帮助

- 查看构建日志：`Actions` → `Release` → 构建记录
- 检查仓库设置：`Settings` → `Actions` → `General`
- 联系维护者：创建 Issue 或讨论

## 📈 发布最佳实践

1. **定期发布**
   - 保持稳定的发布节奏
   - 避免长时间不发布
   - 建立发布周期

2. **质量保证**
   - 充分测试每个版本
   - 确保向后兼容性
   - 准备回滚方案

3. **用户沟通**
   - 提前预告重要更新
   - 详细说明变更内容
   - 及时响应用户反馈

4. **文档维护**
   - 保持文档与代码同步
   - 提供清晰的升级指南
   - 记录重要的变更历史