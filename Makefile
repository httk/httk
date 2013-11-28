VERSION=`cat VERSION`

all:
	echo "No need for make, just read INSTALL.txt. Makefile only exist to allow 'make clean', etc."

clean: preclean
	find . -name "*.pyc" -print0 | xargs -0 rm -f

preclean: 
	(cd Examples; make clean)
	(cd Programs; make clean)
	find . -name "*~" -print0 | xargs -0 rm -f
	rm -f httk_*.tgz
	rm -f httk_*.md5

dist: preclean
	( cd Templates; \
	  for template in *.txt; do \
		./subsvars.sh < "$$template" > "../$$template"; \
	  done; \
	)
	echo '$$HTTKVERSION' | Templates/subsvars.sh > VERSION
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	rm -f "httk_${VERSION}.tgz"
	tar -zcvf "httk_v$$(cat VERSION).tgz" Examples Programs Templates httk README.txt INSTALL.txt CHANGELOG.txt \
		httk.cfg Makefile COPYING --exclude=".*" --exclude="Programs/runs/*"
	md5sum "httk_v$$(cat VERSION).tgz" > "httk_$$(cat VERSION).md5"
	
	