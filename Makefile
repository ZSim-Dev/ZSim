.PHONY: build clean run check help frontend frontend-build electron-build cross-build release-all

# Default target
all: build

# Detect operating system
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    OS := linux
    OS_FLAG := linux
else ifeq ($(UNAME_S),Darwin)
    OS := macos
    OS_FLAG := mac
else
    OS := windows
    OS_FLAG := win
endif

# Build backend API for current platform
backend:
	@echo "Starting to build ZSim API for $(OS)..."
	@uv run pyinstaller --noconfirm zsim_api.spec
	@echo "Setting executable permissions..."
	@chmod +x dist/zsim_api
	@echo "Backend API build completed!"

# Build backend API for specific platforms
backend-windows:
	@echo "Starting to build ZSim API for Windows..."
	@TARGET_PLATFORM=windows uv run pyinstaller --noconfirm zsim_api.spec
	@echo "Windows backend API build completed!"

backend-linux:
	@echo "Starting to build ZSim API for Linux..."
	@TARGET_PLATFORM=linux uv run pyinstaller --noconfirm zsim_api.spec
	@echo "Setting executable permissions..."
	@chmod +x dist/zsim_api
	@echo "Linux backend API build completed!"

backend-macos:
	@echo "Starting to build ZSim API for macOS..."
	@TARGET_PLATFORM=macos uv run pyinstaller --noconfirm zsim_api.spec
	@echo "Setting executable permissions..."
	@chmod +x dist/zsim_api
	@echo "macOS backend API build completed!"

# Build backend API for all platforms
backend-all:
	@echo "Starting to build ZSim API for all platforms..."
	@TARGET_PLATFORM=windows uv run pyinstaller --noconfirm zsim_api.spec
	@TARGET_PLATFORM=linux uv run pyinstaller --noconfirm zsim_api.spec
	@TARGET_PLATFORM=macos uv run pyinstaller --noconfirm zsim_api.spec
	@echo "Setting executable permissions..."
	@chmod +x dist/zsim_api
	@echo "All platforms backend API build completed!"

# Build Electron desktop application for current platform
electron-build:
	@echo "Starting to build Electron desktop application for $(OS)..."
	@echo "First, building the backend API..."
	@make backend
	@echo "Copying backend binary files to Electron resource directory..."
	@mkdir -p electron-app/resources
	@cp -r dist/zsim_api electron-app/resources/
	@cd electron-app && pnpm install
	@cd electron-app && pnpm build:$(OS_FLAG)
	@echo "Electron desktop application build completed!"

# Cross-compilation targets
cross-build-windows:
	@echo "Starting to build Electron desktop application for Windows..."
	@echo "First, building the backend API for Windows..."
	@make backend-windows
	@echo "Copying backend binary files to Electron resource directory..."
	@mkdir -p electron-app/resources
	@cp -r dist/zsim_api electron-app/resources/
	@cd electron-app && pnpm install
	@cd electron-app && pnpm build:win
	@echo "Windows Electron desktop application build completed!"

cross-build-linux:
	@echo "Starting to build Electron desktop application for Linux..."
	@echo "First, building the backend API for Linux..."
	@make backend-linux
	@echo "Copying backend binary files to Electron resource directory..."
	@mkdir -p electron-app/resources
	@cp -r dist/zsim_api electron-app/resources/
	@cd electron-app && pnpm install
	@cd electron-app && pnpm build:linux
	@echo "Linux Electron desktop application build completed!"

cross-build-macos:
	@echo "Starting to build Electron desktop application for macOS..."
	@echo "First, building the backend API for macOS..."
	@make backend-macos
	@echo "Copying backend binary files to Electron resource directory..."
	@mkdir -p electron-app/resources
	@cp -r dist/zsim_api electron-app/resources/
	@cd electron-app && pnpm install
	@cd electron-app && pnpm build:mac
	@echo "macOS Electron desktop application build completed!"

# Build all platforms (macOS only)
cross-build-all:
	@if [ "$(UNAME_S)" != "Darwin" ]; then \
		echo "❌ Error: Cross-compilation for all platforms is only supported on macOS"; \
		exit 1; \
	fi
	@echo "Starting to build Electron desktop application for all platforms..."
	@echo "First, building the backend API for all platforms..."
	@make backend-all
	@echo "Copying backend binary files to Electron resource directory..."
	@mkdir -p electron-app/resources
	@cp -r dist/zsim_api electron-app/resources/
	@cd electron-app && pnpm install
	@echo "Building for Windows..."
	@cd electron-app && pnpm build:win
	@echo "Building for Linux..."
	@cd electron-app && pnpm build:linux
	@echo "Building for macOS..."
	@cd electron-app && pnpm build:mac
	@echo "All platforms Electron desktop application build completed!"

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

# Release build for all platforms (macOS only)
# Usage: make release-all RELEASE_TYPE=patch
release-all:
	@if [ "$(UNAME_S)" != "Darwin" ]; then \
		echo "❌ Error: Multi-platform release is only supported on macOS"; \
		exit 1; \
	fi
	@echo "Starting multi-platform release build..."
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
	make clean
	make cross-build-all
	@echo "Multi-platform release build completed!"

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
	make clean
	make backend electron-build
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
	@echo "  backend               - Build backend API for current platform"
	@echo "  backend-windows        - Build backend API for Windows"
	@echo "  backend-linux          - Build backend API for Linux"
	@echo "  backend-macos          - Build backend API for macOS"
	@echo "  backend-all           - Build backend API for all platforms"
	@echo "  electron-build        - Build Electron desktop application for current platform"
	@echo "  backend               - Build backend API"
	@echo "  electron-build        - Build Electron desktop application for current platform"
	@echo "  build                 - Build backend API and frontend application"
	@echo "  clean                 - Clean all build files"
	@echo "  dev                   - Start frontend development server"
	@echo "  help                  - Display this help information"
	@echo ""
	@echo "Cross-compilation:"
	@echo "  cross-build-windows   - Build Windows version"
	@echo "  cross-build-linux     - Build Linux version"
	@echo "  cross-build-macos     - Build macOS version"
	@echo "  cross-build-all       - Build all three platforms"
	@echo ""
	@echo "Release builds:"
	@echo "  release               - Parameterized release for current platform"
	@echo "  release-all           - Multi-platform release (macOS only)"
	@echo ""
	@echo "Usage examples:"
	@echo "  make build                    # Build for current platform"
	@echo "  make cross-build-all          # Build all platforms (macOS only)"
	@echo "  make release RELEASE_TYPE=patch  # Release patch version"
	@echo "  make release-all RELEASE_TYPE=minor  # Multi-platform release"
	@echo "  make dev                      # Start frontend development environment"
	@echo "  make clean                    # Clean all build files"