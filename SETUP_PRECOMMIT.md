# Pre-commit 设置指南 (Ruff 专用)

## 安装和设置

1. **安装依赖**
```bash
uv sync
```

2. **安装 pre-commit hooks**
```bash
uv run pre-commit install
```

3. **手动运行所有检查**
```bash
uv run pre-commit run --all-files
```

## 配置的检查项

### Ruff 代码检查和格式化
- **ruff**: Python 代码检查和自动修复 (`--fix`)
- **ruff-format**: Python 代码格式化

## 使用说明

### 每次 commit 时自动运行
设置完成后，每次 `git commit` 都会自动运行 ruff 检查和格式化。

### 手动运行检查
```bash
# 对所有文件运行检查
uv run pre-commit run --all-files

# 对暂存的文件运行检查
uv run pre-commit run

# 只运行检查（不格式化）
uv run ruff check

# 只运行格式化
uv run ruff format
```

### 更新 hooks
```bash
uv run pre-commit autoupdate
```

## 注意事项

1. **自动修复**：Ruff 会自动修复大部分代码问题和格式问题
2. **性能**：Ruff 非常快速，通常在几秒内完成
3. **配置**：所有 Ruff 配置都在 `pyproject.toml` 的 `[tool.ruff]` 部分

## 配置文件位置
- 主配置：`.pre-commit-config.yaml`
- Ruff 配置：`pyproject.toml` 中的 `[tool.ruff]` 部分