###---CASSETTE MAKEFILE

#---always show the banner
-include banner

#---point latex to extra style files
export TEXINPUTS := .:./cas/sources/extras/:$(TEXINPUTS)

#---extra arguments passed along to downstream functions and scripts
RUN_ARGS := $(wordlist 1,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
#---ensure that we filter out all valid target names from RUN_ARGS
COMMENTS := $(filter-out all banner save add clean silo dispatch init dev clone,$(RUN_ARGS))
#---evaluate all superfluous make arguments to suppress warnings that contain these arguments
$(eval $(COMMENTS):;@:)

#---parse downstream files
SRC_MD = $(filter-out README.md,$(wildcard *.md))
OBJ_MD_HTML = $(patsubst %.md,%.html,$(SRC_MD))
OBJ_TEX_PDF = $(patsubst %.tex,cas/hold/%.pdf,$(SRC_TEX))

#---settings
latex_engine = pdflatex

#---standard
.PHONY: all banner save push pull add start stop
all: init silo $(OBJ_MD_HTML) indexer

#---only dispatch upon request (always index afterwards)
dispatch:
	@python ./cas/parser/dispatch.py ${RUN_ARGS} ${MAKEFLAGS}
	@python ./cas/parser/indexer.py
	@/bin/echo "[INDEX] file:///$(shell pwd)/index.html"

#---draw an index HTML
indexer:
	@python ./cas/parser/indexer.py
	@/bin/echo "[INDEX] file:///$(shell pwd)/index.html"

#---show the banner if no targets
banner:
	@sed -n 1,10p cas/readme.md
	@/bin/echo "[NOTE] use 'make help' for instructions"

#---print help from readme minus banner
help:
ifeq (,$(findstring save,${RUN_ARGS}))
	@/bin/echo -n "[STATUS] printing help: "
	tail -n +10 cas/readme.md
endif

#---! note that we remove tex files from below which precludes using tex as an input
#---remove holding directory and rendered files
clean:
	@/bin/echo "[STATUS] cleaning"
	@rm -rf $(wildcard cas/hold) || true
	@rm -rf $(wildcard ./*.html) || true
	@rm -rf $(wildcard ./*.pdf) || true
	@rm -rf $(wildcard ./*.png) || true
	@rm -rf $(wildcard ./*.tex) || true
	@rm -rf printed || true

list:
	@python ./cas/parser/parser.py ${RUN_ARGS} ${MAKEFLAGS}

###---DOCUMENT

#---send markdown files to parser
%.html: %.md
	@test -d cas/hold || mkdir cas/hold
	@/bin/echo "[STATUS] starting $<"
	@/bin/echo "[STATUS] compiling HTML+PDF (this might take a moment)"
	@python ./cas/parser/parser.py $< || (echo "[STATUS] fail"; exit 1;)
	@if [ -a $(patsubst %.html,cas/hold/%.pdf,$@) ]; then { cp $(patsubst %.html,cas/hold/%.pdf,$@) ./;}; fi;
	@if [ -a $(patsubst %.html,cas/hold/%.tex,$@) ]; then { cp $(patsubst %.html,cas/hold/%.tex,$@) ./;}; fi;
	@/bin/echo "[STATUS] compiled $<"
	@/bin/echo "[VIEW] file:///$(shell pwd)/$(patsubst %.md,%.html,$<)"
	@/bin/echo "[STATUS] saving $<"
	@git --git-dir=./$(siloname)/.git --work-tree=$(siloname)/ ls-files %.pure \
	--error-unmatch &> /dev/null || ( \
	git --git-dir=./$(siloname)/.git --work-tree=$(siloname)/ add $(patsubst %.md,%.pure,$<); \
	git --git-dir=./$(siloname)/.git --work-tree=$(siloname)/ commit -m \
	"added $(patsubst %.md,%.$(siloname),$<)"; ) || ( /bin/echo "[STATUS] nothing to commit" )
	@if [[ ! -z "$$(git --git-dir=./$(siloname)/.git --work-tree=$(siloname)/ diff)" ]]; \
	then git --git-dir ./$(siloname)/.git --work-tree=$(siloname) commit -a -m \
	"checkpoint ""$$(date +"%Y.%m.%d.%H%M") +$(patsubst %.md,%,$<)"; \
	else echo "[STATUS] no changes"; fi

#---move the repo out of the way for the data repo
init:
	@if [[ ! -d "./.gitcas" ]] && \
	`git ls-files cas/parser/parselib.py  --error-unmatch &> /dev/null`; \
	then mv .git .gitcas && cp cas/parser/gitignore-data ./.gitignore; fi

#---talk to the casette git repository
dev:
	@/bin/echo "[NOTE] to update the cassette repo, use: \"git --git-dir=.gitcas\""

#---make a silo typically called "history" if absent
#---also concurrently make a data repository
siloname=history
silo: 
ifeq ($(wildcard $(siloname)/),)
	@/bin/echo -n "[STATUS] init $(siloname) repo: "
	@git init $(siloname)
	@/bin/echo -n "[STATUS] initial commit: "
	@git --git-dir ./$(siloname)/.git --work-tree=$(siloname) commit --allow-empty -m 'initial commit'
	@git init .
	@git commit --allow-empty -m 'initial commit'
	@git add .gitignore
	@git commit --allow-empty -m 'added gitignore'
endif

#---clone an upstream data repository (works on git before and after 2.9)
clone:
	@test ! -d .git || (echo "[ERROR] can only clone if .git is absent"; exit 1;)
	git clone $(upstream) cas/incoming || (echo "[STATUS] fail"; exit 1;)
	mv cas/incoming/.git . || (echo "[STATUS] fail"; exit 1;)
	rm -rf cas/incoming || (echo "[STATUS] fail"; exit 1;)
	git reset --hard || (echo "[STATUS] fail"; exit 1;)

###---VERSIONING

#---write commit messages directly on the command line
#---all other make targets are protected from executing save via ifeq findstring
save: banner
	@/bin/echo -n "[STATUS] saving changes: "
	@/bin/echo ${RUN_ARGS}
	git --git-dir=./$(siloname)/.git --work-tree=$(siloname)/ commit \
	--allow-empty -am "${RUN_ARGS}"
	@if [ false ]; then echo "[STATUS] done"; exit 0; else true; fi	

###---DOCUMENTATION

demo:
	@if [ -f demo.md ]; then { echo "[ERROR] demo.md already exists"; }; \
	else { cp cas/sources/demo.md ./ && echo "[NOTE] run \"make\" to view the demo"; }; fi;
