minimal: httk.cfg VERSION

all:	httk.cfg VERSION presentation docs

VERSION:
	echo '$$HTTKVERSION' | Docs/subsvars.sh > VERSION

httk.cfg:
	if [ ! -e httk.cfg ]; then cp httk.cfg.default httk.cfg; fi

autopep8:
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r httk/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Tutorial/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Examples/

clean: preclean
	find . -name "*.pyc" -print0 | xargs -0 rm -f

preclean: 
	(cd Examples; make clean)
	(cd Tutorial; make clean)
	find . -name "*~" -print0 | xargs -0 rm -f
	rm -f httk_*.tgz
	rm -f httk_*.md5

dist: presentation preclean 
	echo '$$HTTKVERSION' | Docs/subsvars.sh > VERSION
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	rm -f "httk-$$(cat VERSION).tgz"	
	( \
		THISDIR=$$(basename "$$PWD"); \
		cd ..; \
		tar -zcf "$$THISDIR/httk-$$(cat $$THISDIR/VERSION).tgz" "$$THISDIR/Examples" "$$THISDIR/Tutorial" "$$THISDIR/External" "$$THISDIR/Execution" "$$THISDIR/httk" "$$THISDIR/"*.txt "$$THISDIR/LICENSE" "$$THISDIR/COPYING" "$$THISDIR/httk_overview.pdf" "$$THISDIR/bin" \
		"$$THISDIR/httk.cfg.default" "$$THISDIR/VERSION" \
		"$$THISDIR/httk.minimal.files" "$$THISDIR/setup.shell" "$$THISDIR/setup.shell.eval" \
		--exclude=".*" --transform "flags=r;s|httk.cfg.default|httk.cfg|;s|$$THISDIR|httk-$$(cat $$THISDIR/VERSION)|"\
	)
	md5sum "httk-$$(cat VERSION).tgz" > "httk-$$(cat VERSION).md5"

presentation: 
	( cd Presentation; \
	   make; \
	)
	cp Presentation/presentation.pdf httk_overview.pdf

docs: VERSION presentation
	mkdir -p Docs/generated/
	Docs/subsvars.sh < Docs/header.tpl > Docs/generated/header.txt
	rm -f Docs/httk.*
	sphinx-apidoc -F -o Docs httk
	mkdir -p Docs/_static/generated/httk_overview/	
	cp Presentation/generated/*.png Docs/_static/generated/httk_overview/.
	cp Presentation/generated/httk_overview.html Docs/generated/.
	cp Presentation/presentation.pdf Docs/_static/generated/httk_overview.pdf
	(cd Docs; make html; make text)
	cp Docs/_build/text/developers_guide.txt DEVELOPERS_GUIDE.txt
	cp Docs/_build/text/readme.txt README.txt
	cp Docs/_build/text/users_guide.txt USERS_GUIDE.txt
	cp Docs/_build/text/runmanager_details.txt RUNMANAGER_DETAILS.txt
	cp Docs/_build/text/install.txt INSTALL.txt

web:
	(cd Web; \
	  ./sync-httk.sh; \
	  ./sync.sh \
	)
