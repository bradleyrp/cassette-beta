#!/usr/bin/python

import os,sys,re

"""
Renders custom markdown to tex, PDF, and HTML.
Updated from parser.py to include revtex and more explicit data handling.
"""

#---settings
instruct = sys.argv[1]
with open('cas/parser/parselib.py') as f: exec(f.read())
#---list the available texts
if instruct == 'list':
	#---! verbatim from director.py
	class colorprint:
		HEADER,OKBLUE,OKGREEN = '\033[95m','\033[94m','\033[92m'
		WARNING,FAIL,ENDC = '\033[93m','\033[91m','\033[0m'
		BOLD,UNERLINE = '\033[1m','\033[4m'
		means = {'g':OKGREEN,'b':OKBLUE,'s':BOLD,'r':FAIL,'w':WARNING}
		def __init__(self,*args):
			out = ''
			for form,msg in args:
				out = out + msg if not form else out + ''.join(
					[self.means[letter] for letter in form]+[msg]+[self.ENDC for letter in form])
			print(out)
	fns = [i for i in glob.glob('*.md') if i != 'README.md']
	if any(fns): colorprint(('sr','[CONTENTS]'),(None,' available texts:'))
	else: colorprint(('s','[CONTENTS]'),('g',' nothing yet'))
	for fn in fns: colorprint(*[('sb','[text]'),(None,' %s'%fn)]) 
elif os.path.isfile(instruct) and re.search('\.md$',instruct):
	doc = TexDocument(instruct)
else: 
	#---! an error on some systems causes the temporary yaml for the tiler to end up here
	print('[WARNING] parser cannot understand argument: %s'%sys.argv[1])
