simple: httk.cfg version

all:	httk.cfg version httk_overview.pdf webdocs

httk.cfg:
	if [ ! -e httk.cfg ]; then cat httk.cfg.example | grep -v "^#" > httk.cfg; fi

##############################
## Virtual environment helpers
##############################
#
# make init_default_venv: initializes the standard dev venv in .venvs/uv/default and symlinks .venv to it
#
# make init_uv_venv
# make init_conda_venv: creates the default venv under .venvs/{uv,conda}/py310
#
# make init_uv_venv venv=py312
# make init_conda_venv venv=py312: creates a virtual environment for Pyton 3.12 under .venvs/{uv,conda}/py312
#
# make init_tox_venv
# make init_tox_venv venv=py312: use tox-uv to init the selected uv environment
#
# make init_all_tox_venvs: use tox to init all uv environments defined in tox
#
# Note: the uv environments force install of pyside6, because tkinter does not work
# in the standalone Python used by uv

default_python = py310
venv ?= py310

init_default_venv:
	type -t deactivate 1>/dev/null && deactivate; PYVER=$$(echo $(default_python) | sed 's/^py\([0-9]\)\([0-9]*\)/\1.\2/') && uv venv --python "$${PYVER}" ".venvs/uv/default" && uv pip install --python ".venvs/uv/default/bin/python" -r "requirements.txt" -r "requirements-dev.txt" pyside6
	ln -nsf .venvs/uv/default .venv
	echo "Activate this environment with:"
	echo "  source \".venv/bin/activate\""

init_conda_venv:
	type -t deactivate 1>/dev/null && deactivate; PYVER=$$(echo $(venv) | sed 's/^py\([0-9]\)\([0-9]*\)/\1.\2/') && eval "$$(conda 'shell.bash' 'hook' 2> /dev/null)" && conda create -y -p ".venvs/conda/$(venv)" "python=$$PYVER" && conda activate ".venvs/conda/$(venv)" && python -m pip install -r "requirements.txt" -r "requirements-dev.txt"
	echo "Activate this environment with:"
	echo "  conda activate \".venvs/conda/$(venv)\""

# init_uv_venv only works with uv-supported versions of Python: py38, py39, ...
init_uv_venv:
	type -t deactivate 1>/dev/null && deactivate; PYVER=$$(echo $(venv) | sed 's/^py\([0-9]\)\([0-9]*\)/\1.\2/') && uv venv --python "$${PYVER}" ".venvs/uv/$(venv)" && uv pip install --python ".venvs/uv/$(venv)/bin/python" -r "requirements.txt" -r "requirements-dev.txt" pyside6
	echo "Activate this environment with:"
	echo "  source \".venvs/uv/$(venv)/bin/activate\""

# tox uses the tox-uv plugin, so this should mostly do the same as init_uv_venv
init_tox_venv:
	tox --notest -r -e $(venv)

init_all_tox_venvs:
	tox --notest -r

##############################
## Tests
##############################
#
# make tox
#  - or just -
# tox : runs tests for all python versions defined in tox.ini
#
# make ci: runs a subset of the tests selected as fitting to run as part of the CI
#
# make tests
# make unittests
# make pytests : runs all test in the currently active environment (assuming Python 3)
#
# make unittests2
# make pytests2 : runs all test in the currently active environment (assuming Python 2)
#
# make unittest_autopy27_conda
# make pytests_autopy27_conda: autoinstall a py27 environment and run all tests
#
# For 'unittests' you can add HTTK_TEST_TYPE=<test type> to run a subset of the tests:
#   * all (default): the full test suite
#   * ci: a light set of tests suitable to run in CI
#   * pyver: just test that the tox and environment setup works
#          to test things with the intended python versions.
#

HTTK_TEST_TYPE ?= all

tox:
	rm -rf .tox
	tox

ci: flake8
	cd Tests && PYTHONPATH=$$(pwd -P)/../src:$$PYTHONPATH PATH=$$(pwd -P)../bin:$$PATH python ci.py

tests: flake8 unittests

unittests:
	echo "Running pytest with current default python, expecting supported Python 3 version"
	(cd Tests; python $(HTTK_TEST_TYPE).py)

pytests:
	echo "Running pytest with current default python, expecting supported Python 3 version"
	(cd Tests; py.test)

flake8:
	flake8 . --count --select=E9,F63,F7,F82 --ignore=F824 --show-source --statistics --exclude "ht_instantiate.py,ht.instantiate.py,.tox,.venv,.venvs"

validate_pep8:
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --diff --exit-code -r src/ > /dev/null
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --diff --exit-code -r Tutorial/ > /dev/null
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --diff --exit-code -r Examples/ > /dev/null


.PHONY: tox tests unittests pytests unittests2 pytests2 unittests_autopy27_conda pytests_autopy27_conda

##############################
## python 2.7 support 
##############################
# Deprecated; will be removed in next major release of httk
# Note: duckdb doesn't work in Python3

init_conda_venv27:
	type -t deactivate 1>/dev/null && deactivate; eval "$$(conda 'shell.bash' 'hook' 2> /dev/null)" && conda create -y -p ".venvs/conda/py27" "python=2.7" && conda activate ".venvs/conda/py27" && python -m pip install -r py27requirements.txt -r py27requirements-dev.txt
	echo "Activate this environment with:"
	echo "  conda activate \".venvs/conda/py27\""

unittests2:
	echo "Running pytest with current default python, expecting supported Python 2 version"
	(cd Tests; HTTK_TEST_EXPECT_PYVER=py2 python $(HTTK_TEST_TYPE).py)

pytests2:
	echo "Running pytest with default python, expecting Python 2"
	(cd Tests; HTTK_TEST_EXPECT_PYVER=py2 py.test)

##############################
## Code cleanup
##############################
#
# make autopep8: cleans up all source files inline

autopep8:
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r httk/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Tutorial/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Examples/

.PHONY: autopep8

##############################
## Dev directory cleanup
##############################
#
# make clean: remove all generated files

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	(cd Examples; make clean)
	(cd Tutorial; make clean)
	find . -name "*~" -print0 | xargs -0 rm -f
	rm -f httk_*.tgz
	rm -f httk_*.md5
	rm -f Docs/full/httk.*
	rm -rf Docs/full/_build
	rm -rf .tox
	rm src/httk/core/database.sqlite
	rm -rf .pytest_cache
	find . -name "__pycache__" -print0 | xargs -0 rm -rf

.PHONY: clean

##############################
## Distribution helpers
##############################
#

version:
	(cd src/httk/config; python -c "import sys, config; sys.stdout.write(config.version + '\n')") > VERSION

.PHONY: version

dist: version docs httk_overview.pdf clean

	(cd src/httk/config; python -c "import sys, config; sys.stdout.write('version = \"' + config.version + '\"\n'); sys.stdout.write('version_date = \"' + config.version_date+'\"\n'); sys.stdout.write('copyright_note = \"' + config.copyright_note+'\"\n'); sys.stdout.write('root = \"../..\"\n');") > src/httk/distdata.py

	rm -f "httk-$$(cat VERSION).tgz"

	( \
		THISDIR=$$(basename "$$PWD"); \
		cd ..; \
		tar -zcf "$$THISDIR/httk-$$(cat $$THISDIR/VERSION).tgz" "$$THISDIR/Examples" "$$THISDIR/Tutorial" "$$THISDIR/Execution" "$$THISDIR/src" "$$THISDIR/"*.txt "$$THISDIR/README.rst" "$$THISDIR/httk_overview.pdf" "$$THISDIR/bin" \
		"$$THISDIR/httk.cfg.example" "$$THISDIR/VERSION" \
		"$$THISDIR/httk.minimal.files" "$$THISDIR/init.shell" "$$THISDIR/init.shell.eval"  "$$THISDIR/setup.py" \
		--transform "flags=r;s|httk.cfg.example|httk.cfg|;s|$$THISDIR|httk-$$(cat $$THISDIR/VERSION)|"\
	)
	md5sum "httk-$$(cat VERSION).tgz" > "httk-$$(cat VERSION).md5"
	if [ -e .git ];	then rm -f src/httk/distdata.py src/httk/distdata.pyc; fi

httk_overview.pdf: Presentation/presentation.tex
	( cd Presentation; \
	   make; \
	)
	cp Presentation/presentation.pdf httk_overview.pdf

docs:
	sphinx-apidoc -F -o Docs/full src/httk
	(cd Docs/full; make text)
	cp Docs/full/_build/text/developers_guide.txt ./DEVELOPERS_GUIDE.txt
	cp Docs/full/_build/text/users_guide.txt ./USERS_GUIDE.txt
	cp Docs/full/_build/text/runmanager_details.txt RUNMANAGER_DETAILS.txt
	cp Docs/full/_build/text/install.txt ./INSTALL.txt

.PHONY: docs

webdocs: version httk_overview.pdf
	rm -f Docs/full/httk.*
	#sphinx-apidoc -F -o Docs/full src/httk
	mkdir -p Docs/full/_static/generated/httk_overview/
	cp Presentation/generated/*.png Docs/full/_static/generated/httk_overview/.
	cp Presentation/generated/httk_overview.html Docs/full/generated/.
	cp Presentation/presentation.pdf Docs/full/_static/generated/httk_overview.pdf
	(cd Docs/full; make html)

.PHONY: webdocs
