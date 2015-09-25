# Make sure it always gets remaked, because latexmk takes care of everything.
all: latex httk_overview.html

latex: 
	latexmk -pdf 

clean:
	rm -f *~
	latexmk -C
	rm httk_overview.html

httk_overview.html: pdf_to_html.sh presentation.pdf
	./pdf_to_html.sh 
