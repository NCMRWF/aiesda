# AIESDA Automation Makefile
# Targets: install, clean, test

.PHONY: install clean test help

# Default target
help:
	@echo "AIESDA Management Commands:"
	@echo "  make install  - Run the unified installer (detects WSL/HPC)"
	@echo "  make clean    - Run the surgical uninstaller for the current version"
	@echo "  make test     - Run post-installation verification"

install:
	@echo "🚀 Launching AIESDA Unified Installer..."
	@bash install.sh

clean:
	@echo "🧹 Launching AIESDA Uninstaller..."
	@bash remove.sh

test:
	@echo "🧪 Running Bridge & Library Tests..."
	@bash -c "source /etc/profile.d/modules.sh && module use ${HOME}/modulefiles && module load aiesda && python3 -c 'import aiesda; print(\"✅ AIESDA Local: OK\")'"
	@if [ -f ${HOME}/build/aiesda_build_$$(cat VERSION)/bin/jedi-run ]; then \
		${HOME}/build/aiesda_build_$$(cat VERSION)/bin/jedi-run python3 -c "import ufo; print('✅ JEDI Bridge: OK')"; \
	fi

reinstall: 
	clean install

# Makefile snippet
bump:
	@chmod +x bump_version.sh
	@./bump_version.sh

# Use this to verify the version before a build
version:
	@echo "Current Target: $$(cat VERSION)"
