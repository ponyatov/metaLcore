# \ var
MODULE  = $(notdir $(CURDIR))
OS      = $(shell uname -s)
NOW     = $(shell date +%d%m%y)
REL     = $(shell git rev-parse --short=4 HEAD)
BRANCH  = $(shell git rev-parse --abbrev-ref HEAD)
CORES   = $(shell grep processor /proc/cpuinfo| wc -l)
# / var

# \ dir
CWD     = $(CURDIR)
BIN     = $(CWD)/bin
DOC     = $(CWD)/doc
LIB     = $(CWD)/lib
SRC     = $(CWD)/src
TMP     = $(CWD)/tmp
PYPATH  = $(HOME)/.local/bin
# / dir

# \ tool
CURL    = curl -L -o
PY      = $(shell which python3)
PIP     = $(shell which pip3)
PEP     = $(PYPATH)/autopep8
PYT     = $(PYPATH)/pytest
# / tool

# \ src
Y += $(MODULE).py metaL.py
R += $(shell find src -type f -regex ".+.rs$$")
S += $(Y) $(R)
# / src

# \ all

all:

meta: $(PY) $(MODULE).py
	$^ $@ meta
	$(MAKE) format

test:

format: tmp/format_py
tmp/format_py: $(Y)
	$(PEP) --ignore=E26,E302,E305,E401,E402,E701,E702 --in-place $?
	touch $@
# / all

# \ doc
doxy:
	rm -rf docs ; doxygen doxy.gen 1>/dev/null
doc:
# / doc

# \ install
install: $(OS)_install doc
	$(MAKE) update
update: $(OS)_update
	$(PIP) install --user -U pytest autopep8

Linux_install Linux_update:
	sudo apt update
	sudo apt install -u `cat apt.txt apt.dev`
# / install

# \ merge
MERGE  = Makefile README.md .gitignore apt.dev apt.txt $(S)
MERGE += .vscode bin doc lib src tmp

.PHONY: ponymuck
ponymuck:
	git push -v
	git checkout $@
	git pull -v

.PHONY: dev
dev:
	git push -v
	git checkout $@
	git pull -v
	git checkout ponymuck -- $(MERGE)

.PHONY: release
release:
	git tag $(NOW)-$(REL)
	git push -v --tags
	$(MAKE) ponymuck

.PHONY: zip
ZIP = $(TMP)/$(MODULE)_$(BRANCH)_$(NOW)_$(REL).src.zip
zip:
	git archive --format zip --output $(ZIP) HEAD
	$(MAKE) doxy ; zip -r $(ZIP) docs
# / merge
