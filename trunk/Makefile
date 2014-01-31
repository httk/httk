all:	httk.cfg templates 
	@echo "================================="
	@echo "==== Please read INSTALL.txt ===="
	@echo "================================="
templates:
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
