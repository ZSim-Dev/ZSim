.PHONY: build clean run check help

# 默认目标
all: build

# 构建可执行文件
build:
	@echo "开始构建 ZSim API..."
	@uv run pyinstaller zsim_api.spec
	@echo "设置可执行权限..."
	@chmod +x dist/zsim_api
	@echo "构建完成！"
	@echo "使用方法:"
	@echo "  cd dist/zsim_api"
	@echo "  ./zsim_api          # 直接运行"

# 清理构建文件
clean:
	@echo "清理构建文件..."
	@rm -rf build dist
	@echo "清理完成！"

# 运行API
run:
	@echo "启动 ZSim API..."
	@if [ -f dist/zsim_api ]; then \
		cd dist/zsim_api && ./zsim_api; \
	else \
		echo "请先运行 'make build' 构建项目"; \
		exit 1; \
	fi

# 检查依赖
check:
	@echo "检查依赖..."
	@uv run python -c "import PyInstaller; print('✓ PyInstaller已安装')" || \
		(echo "✗ PyInstaller未安装，请运行: uv add --group dev pyinstaller" && exit 1)
	@if [ -f zsim_api.spec ]; then \
		echo "✓ zsim_api.spec 文件存在"; \
	else \
		echo "✗ zsim_api.spec 文件不存在"; \
		exit 1; \
	fi
	
# 显示帮助
help:
	@echo "ZSim API 构建系统"
	@echo "================"
	@echo ""
	@echo "可用的目标:"
	@echo "  build   - 构建可执行文件"
	@echo "  clean   - 清理构建文件"
	@echo "  run     - 运行API"
	@echo "  check   - 检查依赖"
	@echo "  help    - 显示此帮助信息"
	@echo ""
	@echo "直接使用 PyInstaller:"
	@echo "  uv run pyinstaller zsim_api.spec"
	@echo ""
	@echo "构建后运行:"
	@echo "  cd dist/zsim_api && ./zsim_api"