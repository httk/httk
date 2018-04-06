typical: httk.cfg VERSION docs

minimal: httk.cfg VERSION

all:	httk.cfg VERSION presentation webdocs pregendocs docs


VERSION: 
	python -c "import httk" >/dev/null 

.PHONY: VERSION

httk.cfg:
	if [ ! -e httk.cfg ]; then cp httk.cfg.default httk.cfg; fi

autopep8:
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r httk/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Tutorial/
	autopep8 --ignore=E501,E401,E402,W291,W293,W391,E265,E266,E226 --aggressive --in-place -r Examples/

docs: VERSION
	HTTK_VERSION=$$(cat VERSION); \
	HTTK_COPYRIGHT_NOTICE=$$(python -c "import httk, sys; httk.citation.dont_print_citations_at_exit(); sys.stdout.write(httk.httk_copyright_note)"); \
	for FILE in $$(cd Docs/pre-generated-templates; ls *.tpl); do \
	  BASENAME="$$(basename "$$FILE" .tpl)"; \
	  cat Docs/pre-generated-templates/"$$FILE" | sed 's/$${{HTTK_VERSION}}/'"$$HTTK_VERSION"'/;s/$${{HTTK_COPYRIGHT_NOTICE}}/'"$$HTTK_COPYRIGHT_NOTICE"'/' > "$$BASENAME.txt"; \
	done;

.PHONY: docs

clean: preclean
	find . -name "*.pyc" -print0 | xargs -0 rm -f

preclean: 
	(cd Examples; make clean)
	(cd Tutorial; make clean)
	find . -name "*~" -print0 | xargs -0 rm -f
	rm -f httk_*.tgz
	rm -f httk_*.md5

dist: VERSION presentation preclean 
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	rm -f "httk-$$(cat VERSION).tgz"	
	( \
		THISDIR=$$(basename "$$PWD"); \
		cd ..; \
		tar -zcf "$$THISDIR/httk-$$(cat $$THISDIR/VERSION).tgz" "$$THISDIR/Examples" "$$THISDIR/Tutorial" "$$THISDIR/Execution" "$$THISDIR/httk" "$$THISDIR/"*.txt "$$THISDIR/LICENSE" "$$THISDIR/COPYING" "$$THISDIR/httk_overview.pdf" "$$THISDIR/bin" \
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

pregendocs: VERSION
	sphinx-apidoc -F -o Docs/full httk
	(cd Docs/full; make text)
	cp Docs/full/_build/text/developers_guide.txt Docs/pre-generated-templates/DEVELOPERS_GUIDE.tpl
	cp Docs/full/_build/text/readme.txt Docs/pre-generated-templates/README.tpl
	cp Docs/full/_build/text/users_guide.txt Docs/pre-generated-templates/USERS_GUIDE.tpl
	cp Docs/full/_build/text/runmanager_details.txt Docs/pre-generated-templates/RUNMANAGER_DETAILS.tpl
	cp Docs/full/_build/text/install.txt Docs/pre-generated-templates/INSTALL.tpl

webdocs: VERSION presentation
	rm -f Docs/full/httk.*
	sphinx-apidoc -F -o Docs/full httk
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
