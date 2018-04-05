# Make sure it always gets remaked, because latexmk takes care of everything.
all: latex generated/httk_overview.html

latex: 
	latexmk -pdf 

clean:
	rm -rf *~ *.nav *.snm
	latexmk -C
	rm -rf generated

generated/httk_overview.html: pdf_to_html.sh latex
	./pdf_to_html.sh 
