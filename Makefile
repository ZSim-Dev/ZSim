.PHONY: build clean run check help frontend frontend-build electron-build

# Default target
all: build

# Build backend API
backend:
	@echo "Starting to build ZSim API..."
	@uv run pyinstaller --noconfirm zsim_api.spec
	@echo "Setting executable permissions..."
	@chmod +x dist/zsim_api
	@echo "Backend API build completed!"

# Build Electron desktop application
electron-build:
	@echo "Starting to build Electron desktop application..."
	@echo "First, building the backend API..."
	@make backend
	@echo "Copying backend binary files to Electron resource directory..."
	@mkdir -p electron-app/resources
	@cp -r dist/zsim_api electron-app/resources/
	@cd electron-app && pnpm install
	@cd electron-app && pnpm build:$(shell uname -s | tr '[:upper:]' '[:lower:]')
	@echo "Electron desktop application build completed!"

# Clean build files
clean:
	@echo "Cleaning build files..."
	@rm -rf build dist resources
	@cd electron-app && rm -rf dist dist-electron release node_modules/.vite
	@echo "Cleanup completed!"

# Full build (includes Electron)
build: clean backend electron-build
	@echo "Full build completed!"
	@echo "Backend API: dist/zsim_api/"
	@echo "Electron app: electron-app/release/"

# Release build (parameterized release support)
# Usage: make release RELEASE_TYPE=patch
release:
	@echo "Starting release build..."
	@echo "Release type: $(RELEASE_TYPE)"
	@echo "Updating backend version..."
	uv version --bump $(RELEASE_TYPE); \
	@echo "Updating frontend version..."
	@cd electron-app && if [ "$(RELEASE_TYPE)" = "alpha" ] || [ "$(RELEASE_TYPE)" = "beta" ]; then \
		pnpm version prerelease --preid $(RELEASE_TYPE) --no-git-tag-version; \
	else \
		pnpm version $(RELEASE_TYPE) --no-git-tag-version; \
	fi
	@echo "Cleaning and rebuilding..."
	clean backend electron-build
	@echo "Release build completed!"

# Run frontend development server
dev:
	@echo "Starting frontend development server..."
	@cd electron-app && pnpm dev

# Check dependencies
check:
	@echo "Checking backend dependencies..."
	@uv run python -c "import PyInstaller; print('✓ PyInstaller is installed')" || \
		(echo "✗ PyInstaller is not installed. Run: uv add --group dev pyinstaller" && exit 1)
	@if [ -f zsim_api.spec ]; then \
		echo "✓ zsim_api.spec file exists"; \
	else \
		echo "✗ zsim_api.spec file does not exist"; \
		exit 1; \
	fi
	@echo "Checking frontend dependencies..."
	@if [ -f electron-app/package.json ]; then \
		cd electron-app && npm list pnpm > /dev/null 2>&1 && echo "✓ pnpm is installed" || (echo "✗ pnpm is not installed" && exit 1); \
	else \
		echo "✗ electron-app/package.json does not exist"; \
		exit 1; \
	fi

# Show help
help:
	@echo "ZSim Build System"
	@echo "================"
	@echo ""
	@echo "Available targets:"
	@echo "  backend         - Build backend API"
	@echo "  frontend        - Build frontend application"
	@echo "  electron-build  - Build Electron desktop application"
	@echo "  build           - Build backend API and frontend application"
	@echo "  full-build      - Full build (includes Electron)"
	@echo "  clean           - Clean all build files"
	@echo "  run             - Run backend API"
	@echo "  dev             - Start frontend development server"
	@echo "  run-electron    - Run Electron application"
	@echo "  check           - Check dependencies"
	@echo "  help            - Display this help information"
	@echo ""
	@echo "Release build:"
	@echo "  release         - Parameterized release (make release RELEASE_TYPE=patch)"
	@echo ""
	@echo "Usage examples:"
	@echo "  make build              # Build backend and frontend"
	@echo "  make run                # Run backend API"
	@echo "  make dev                # Start frontend development environment"
	@echo "  make full-build         # Full build"
	@echo "  make clean              # Clean all build files"
	@echo "  make release RELEASE_TYPE=patch  # Release patch version"