simple: httk.cfg version

all:	httk.cfg version httk_overview.pdf webdocs

httk.cfg:
	if [ ! -e httk.cfg ]; then cat httk.cfg.example | grep -v "^#" > httk.cfg; fi

init_venvs:
	tox --notest

tox:
	tox

tox27:
	HTTK_TEST_TYPE=pyver tox -c tox-conda.ini -e py27

tests: unittests2 unittests3

pytests: pytest2 pytest3

unittests:
	(cd Tests; TEST_EXPECT_PYVER=ignore python all.py)

unittests2:
	echo "Running unittests with default python, expecting Python 2"
	(cd Tests; TEST_EXPECT_PYVER=2 PATH="$$(pwd -P)/python_versions/ver2:$$PATH" python all.py)

unittests3: link_python3
	echo "Running unittests with default python, expecting Python 2"
	(cd Tests; TEST_EXPECT_PYVER=3 PATH="$$(pwd -P)/python_versions/ver3:$$PATH" python all.py)

pytest:
	(cd Tests; TEST_EXPECT_PYVER=ignore py.test)

pytest2:
	echo "Running pytest with default python, expecting Python 2"
	(cd Tests; TEST_EXPECT_PYVER=2 py.test)

pytest3:
	echo "Running pytest with default python, expecting Python 3"
	(cd Tests; TEST_EXPECT_PYVER=3 py.test-3)

.PHONY: tox tox27 unittests unittests2 unittests3 pytest pytest2 pytest3

autopep8:
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r httk/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Tutorial/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Examples/

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	(cd Examples; make clean)
	(cd Tutorial; make clean)
	find . -name "*~" -print0 | xargs -0 rm -f
	rm -f httk_*.tgz
	rm -f httk_*.md5
	rm -f Docs/full/httk.*
	rm -rf Docs/full/_build

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
