# Make sure it always gets remaked, because latexmk takes care of everything.
all: latex generated/httk_overview.html

latex: 
	latexmk -pdf 

clean:
	rm -f *~
	latexmk -C
	rm -r generated

generated/httk_overview.html: pdf_to_html.sh latex
	./pdf_to_html.sh 
