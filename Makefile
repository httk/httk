typical: httk.cfg VERSION 

all:	httk.cfg VERSION presentation webdocs

VERSION: 
	python -c "import sys, os, inspect; _realpath = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])); sys.path.insert(1, os.path.join(_realpath,'src')); import httk" >/dev/null 

.PHONY: VERSION

httk.cfg:
	if [ ! -e httk.cfg ]; then cat httk.cfg.example | grep -v "^#" > httk.cfg; fi

autopep8:
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r httk/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Tutorial/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Examples/

.PHONY: docs

clean: preclean
	find . -name "*.pyc" -print0 | xargs -0 rm -f

preclean: 
	(cd Examples; make clean)
	(cd Tutorial; make clean)
	find . -name "*~" -print0 | xargs -0 rm -f
	rm -f httk_*.tgz
	rm -f httk_*.md5

dist: VERSION docs presentation preclean 
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	rm -f "httk-$$(cat VERSION).tgz"

	python -c "import sys, os, inspect; _realpath = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])); sys.path.insert(1, os.path.join(_realpath,'src'));import httk; httk.citation.dont_print_citations_at_exit(); sys.stdout.write('version = \"' + httk.__version__+'\"\n'); sys.stdout.write('version_date = \"' + httk.httk_version_date+'\"\n'); sys.stdout.write('copyright_note = \"' + httk.httk_copyright_note+'\"\n')" > httk/version_dist.py
	( \
		THISDIR=$$(basename "$$PWD"); \
		cd ..; \
		tar -zcf "$$THISDIR/httk-$$(cat $$THISDIR/VERSION).tgz" "$$THISDIR/Examples" "$$THISDIR/Tutorial" "$$THISDIR/Execution" "$$THISDIR/httk" "$$THISDIR/"*.txt "$$THISDIR/LICENSE" "$$THISDIR/COPYING" "$$THISDIR/httk_overview.pdf" "$$THISDIR/bin" \
		"$$THISDIR/httk.cfg.default" "$$THISDIR/VERSION" \
		"$$THISDIR/httk.minimal.files" "$$THISDIR/setup.shell" "$$THISDIR/setup.shell.eval" \
		--exclude=".*" --transform "flags=r;s|httk.cfg.default|httk.cfg|;s|$$THISDIR|httk-$$(cat $$THISDIR/VERSION)|"\
	)
	md5sum "httk-$$(cat VERSION).tgz" > "httk-$$(cat VERSION).md5"
	rm -f httk/version_dist.*

presentation: 
	( cd Presentation; \
	   make; \
	)
	cp Presentation/presentation.pdf httk_overview.pdf

docs: 
	sphinx-apidoc -F -o Docs/full src/httk
	(cd Docs/full; make text)
	cp Docs/full/_build/text/developers_guide.txt ./DEVELOPERS_GUIDE.txt
	cp Docs/full/_build/text/overview.txt ./OVERVIEW.txt
	cp Docs/full/_build/text/users_guide.txt ./USERS_GUIDE.txt
	cp Docs/full/_build/text/runmanager_details.txt RUNMANAGER_DETAILS.txt
	cp Docs/full/_build/text/install.txt ./INSTALL.txt

webdocs: VERSION presentation
	rm -f Docs/full/httk.*
	sphinx-apidoc -F -o Docs/full src/httk
	mkdir -p Docs/full/_static/generated/httk_overview/	
	cp Presentation/generated/*.png Docs/full/_static/generated/httk_overview/.
	cp Presentation/generated/httk_overview.html Docs/full/generated/.
	cp Presentation/presentation.pdf Docs/full/_static/generated/httk_overview.pdf
	(cd Docs/full; make html)

web:
	(cd Web; \
	  ./sync-httk.sh; \
	  ./sync.sh \
	)
