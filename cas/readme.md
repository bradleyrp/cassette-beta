                                                
                                  _   _         
        ____ ____  ___  ___  ____| |_| |_  ____ 
       / ___) _  |/___)/___)/ _  )  _)  _)/ _  )
      ( (__( ( | |\__\ \__\( (/ /| |_| |_( (/ / 
       \____)_||_(___/(___/ \____)\___)___)____)
                                                

"A small case for holding and sharing academic documents."

### USAGE
#-------------------------------------------------------------------

The cassette codes provide version control and git-enabled
collaboration functions alongside a document parser which makes 
web and TeX-derived PDF documents from simple markdown files. 

### Markdown format
#-------------------------------------------------------------------

The cassette codes use a minimal markdown format that includes most
of the standard and some customized extras. The goal of the code is
to convert simple markdown manuscripts into both HTML and PDF via 
LaTex. There are a few other bells and whistles. Most importantly, 
the markdown drafts are converted to newline-delimited texts which 
are tracked automatically by a git repository (in the "history" 
subfolder) so that changes are limited to the sentences in which 
they appear. The code is designed to render the markdown into 
various formats specified in the header material, including PDF 
files that follow journal-specific templates (found in 
"cas/sources/header-<name>.tex"). The code will render TeX equations
 to PNG files for presentations, allows for annotations in the HTML 
 version, and provides a convenient HTML page for serving the 
 various formats over e.g. dropbox.

The cassette codes uses a minimal markdown format adapted for 
writing academic papers. Most of the markdown features are syntax-
highlighted in common text editors, so even raw text documents can
be easy on the eyes. 

-- Headings are marked by hash symbols (#) whose number determines 
   the level of sub-headings.

-- The preamble should also contain the title, authors in a list,
   and the abstract. It ends with three hyphens ("---")

-- Equations are written in TeX and separated by "$".

-- Add references from a bib file specified by the bibliography in
   the preamble by using @Author-Year in a sequence.

-- Like all good markdown, use asterisks to make something **bold**
   or *italicized* or ***both***.

-- Refer to figures by a relative path in the following format:
   ![caption](path/image.png) {#fig:key width=0.65}
   and refer to it in the text with @fig.key. 

-- Highlight any parenthetical comments inside double brackets.
   as in: [[this comment is highlighted]].

### Commands
#-------------------------------------------------------------------

make......................compile markdown documents in text 
make clean................remove rendered drafts

### Additional notes
#-------------------------------------------------------------------

note that header-pnas.tex requires the ctan-times package
note that header-pnas.tex requires (definitely) cbfonts 
    (probably) newunicodechar,textgreek,babel-greek,greek-fontenc
