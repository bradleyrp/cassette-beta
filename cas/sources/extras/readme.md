                                                
                                  _   _         
        ____ ____  ___  ___  ____| |_| |_  ____ 
       / ___) _  |/___)/___)/ _  )  _)  _)/ _  )
      ( (__( ( | |\__\ \__\( (/ /| |_| |_( (/ / 
       \____)_||_(___/(___/ \____)\___)___)____)
                                                

"A small case for holding and sharing academic documents."

### USAGE
#-------------------------------------------------------------------

The cassette codes provide version control and git-enable
collaboration functions alongside a document parser which makes 
web and TeX-derived PDF documents from simple markdown files. These
codes are specifically meant to 

### Markdown format
#-------------------------------------------------------------------

The cassette codes uses a minimal markdown format adapted for 
writing academic papers. Most of the markdown features are syntax-
highlighted in common text editors, so even raw text documents can
be easy on the eyes. 

-- Headings are marked by hash symbols (#) whose number determines 
   the level of sub-headings.

-- The preamble includes parameters that tell cassette how to 
   compile the document. For example "pdf: false" creates only an
   HTML file. Use "documentclass <name>" to specify a header 
   file found in cas/sources/header-<name>.tex or the bibliography
   key to link to a proper bib file.

-- The preamble should also contain the title, authors in a list,
   and the abstract. It ends with three hyphens ("---")

-- EVERY SENTENCE GETS ITS OWN LINE IN THE DOCUMENT. This makes
   change tracking by git much more sensible.

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
make save <message>.......save changes (git commit)
make start <branch>.......start a branch (git checkout)
make stop <branch>........conclude a branch (git merge --no-ff)
make pull.................update from the source (git pull)
make send.................send changes to the source (git push)

