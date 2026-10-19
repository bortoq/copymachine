# Included only by source components inside this workspace.
WORKSPACE_ROOT := $(realpath $(dir $(lastword $(MAKEFILE_LIST)))/..)
WORKSPACE_COMPONENT := $(patsubst $(WORKSPACE_ROOT)/%,%,$(CURDIR))
BUILD_DIR := $(WORKSPACE_ROOT)/build/$(WORKSPACE_COMPONENT)/build
DISTDIR := $(WORKSPACE_ROOT)/build/$(WORKSPACE_COMPONENT)/dist
TMPDIR := $(WORKSPACE_ROOT)/build/$(WORKSPACE_COMPONENT)/tmp
