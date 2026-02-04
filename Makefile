# AIESDA Automation Makefile
# Targets: install, clean, test

# Default message if none is provided
MSG ?= "routine_update"
# Archive local changes with a message
# Usage: make archive MSG="your_message_here"

SITE ?= docker

.PHONY: install clean test help sync version bump archive reinstall update release check-paths

# Use a variable for colors to make it maintainable
GREEN  := $(shell tput -Txterm setaf 2)
RESET  := $(shell tput -Txterm sgr0)

# Default target
help:
	@echo "AIESDA Management Commands:"
	@echo "  ${GREEN} make sync ${RESET}      - Pull remote source (handles elogin)"
	@echo "  ${GREEN} make install ${RESET}   - Build and install [SITE=$(SITE)]"
	@echo "  ${GREEN} make clean ${RESET}     - Surgical uninstall of current version"
	@echo "  ${GREEN} make update ${RESET}    - Sync source and reinstall"
	@echo "  ${GREEN} make release ${RESET}   - Bump version and push to repository"
	@echo "  ${GREEN} make test ${RESET}      - Run post-installation verification"

# Use this to verify the version before a build
version:
	@echo "Current Target: $$(cat VERSION)"

check-paths:
	@if [ $$(pwd) = $$(readlink -f $(BUILD_DIR) | cut -c 1-$${#$$(pwd)}) ]; then \
		echo "Build directory cannot be inside the source tree!"; \
		exit 1; \
	fi

check-modules:
	@bash jobs/setup_env_module.sh

sync:
	@bash jobs/update_pkg.sh

clean:
	@bash jobs/remove.sh $$(cat VERSION)

test:
	@$(MAKE) sync
	@bash jobs/aiesda-dev-cycle-test.sh --site $(SITE)

bump:
	@bash jobs/bump_version.sh

archive:
	@bash jobs/archive_pkg.sh -m $(MSG)

jedidocker:
	@bash jobs/jedi_docker_build.sh

jedilocal:
	@bash jobs/jedi_local_build.sh

install:
	@$(MAKE) check-paths
	@bash jobs/install.sh --site $(SITE)

# Ensure clean finishes before install starts
reinstall:
	@$(MAKE) clean
	@$(MAKE) install SITE=$(SITE)

update: 
	@$(MAKE) sync
	@$(MAKE) reinstall SITE=$(SITE)

release: 
	@$(MAKE) test
	@$(MAKE) bump
	@$(MAKE) archive MSG=$(MSG)
