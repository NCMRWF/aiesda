# AIESDA Automation Makefile
# Targets: install, clean, test

# Default message if none is provided
MSG ?= "routine_update"
# Archive local changes with a message
# Usage: make archive MSG="your_message_here"

SITE ?= docker

.PHONY: install clean test help sync version bump archive reinstall update release

# Default target
help:
	@echo "AIESDA Management Commands:"
	@echo "  make sync      - Pull remote source (handles elogin)"
	@echo "  make install   - Build and install [SITE=$(SITE)]"
	@echo "  make clean     - Surgical uninstall of current version"
	@echo "  make update    - Sync source and reinstall"
	@echo "  make release   - Bump version and push to repository"
	@echo "  make test      - Run post-installation verification"

# Use this to verify the version before a build
version:
	@echo "Current Target: $$(cat VERSION)"

sync:
	@bash jobs/update_pkg.sh

install:
	@bash jobs/install.sh SITE=$(SITE)

clean:
	@bash jobs/remove.sh $$(cat VERSION)

test:
	@bash jobs/aiesda-dev-cycle-test.sh

bump:
	@bash jobs/bump_version.sh

archive:
	@bash jobs/archive_pkg.sh -m $(MSG)

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
	@$(MAKE) archive -m $(MSG)
