#!/usr/bin/python -i
import os;execfile(os.environ['PYTHONSTARTUP'])

"""
DEVELOPMENT
code which takes a rendered tex document and formats it with revtex for PRL-affiliated journals
touch text/draft-v3.md ; make ; ./cas/parser/revtex.py
"""

import re

filebase = 'draft-v3'

with open('cas/sources/header-revtex.tex') as fp: lines = fp.readlines()
with open('cas/hold/%s.tex'%filebase) as fp: 
	addlines = fp.readlines()
	end_header = next(ii for ii,i in enumerate(addlines) if re.search('%.*END HEADER',i))
	lines.extend(addlines[end_header:])
with open('text/%s.v3.tex'%filebase,'w') as fp:
	for line in lines: fp.write(line)
