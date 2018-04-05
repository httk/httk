all:	httk.cfg maketemplates 
	@echo "================================="
	@echo "==== Please read INSTALL.txt ===="
	@echo "================================="
maketemplates:
	echo '$$HTTKVERSION' | Templates/subsvars.sh > VERSION
	( cd Templates; \
	  for template in *.txt; do \
		./subsvars.sh < "$$template" > "../$$template"; \
	  done; \
	)

httk.cfg: 
	( if [ ! -e httk.cfg ]; then \
		cat httk.cfg.default | grep -v "^##" > httk.cfg; \
	  fi; \
	)

clean: preclean
	find . -name "*.pyc" -print0 | xargs -0 rm -f

preclean: 
	(cd Examples; make clean)
	(cd Programs; make clean)
	find . -name "*~" -print0 | xargs -0 rm -f
	rm -f httk_*.tgz
	rm -f httk_*.md5

dist: preclean templates
	echo '$$HTTKVERSION' | Templates/subsvars.sh > VERSION
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	rm -f "httk_${VERSION}.tgz"
	tar -zcvf "httk_v$$(cat VERSION).tgz" Examples Programs Templates httk README.txt INSTALL.txt CHANGELOG.txt \
		httk.cfg Makefile COPYING --exclude=".*" --exclude="Programs/runs/*"
	md5sum "httk_v$$(cat VERSION).tgz" > "httk_$$(cat VERSION).md5"

presentation: 
	( cd Presentation; \
	   make; \
	)
	cp Presentation/presentation.pdf httk_overview.pdf

presentation_clean: 
	( cd Presentation; \
	   make clean; \
	)
	rm -f httk_overview.pdf
