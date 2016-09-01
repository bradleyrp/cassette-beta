#!/usr/bin/python

"""
Renders custom markdown to tex, PDF, and HTML.
"""

import re,os,sys
import tempfile

#---settings
citation_type = 'cite'
pdflatex = 'pdflatex'
figpref = ''
eqnpref = ''

#---IMAGE WRITER
#-------------------------------------------------------------------------------------------------------------

total_equations_written = 0

template = r"""
\documentclass[border=2pt]{standalone}
\usepackage{amsmath}
\usepackage{varwidth}
%s
\begin{document}
\begin{varwidth}{\linewidth}
%s
\end{varwidth}
\end{document}
"""

vector_bold_command = r'%---all vectors are bold'+'\n'+r'\renewcommand{\vec}[1]{\mathbf{#1}}'+'\n'

def write_tex_png(formula,name,count):

	"""
	Convert a TeX equation to PNG.
	"""

	tmpdir = tempfile.mkdtemp()
	outtex = (template%('' if not vectorbold else vector_bold_command,formula)).split('\n')
	for ll,line in enumerate(outtex):
		if re.match(r'^\\label',line): outtex[ll] = ''
		if re.match(r'^\\begin\{eq',line): outtex[ll] = r'\begin{equation*}'
		if re.match(r'^\\end\{eq',line): outtex[ll] = r'\end{equation*}'
	with open('%s/snaptex2.tex'%tmpdir,'w') as fp: 
		fp.write('\n'.join([i for i in outtex if not re.match('^\s*$',i)]))
	os.system(pdflatex+' --output-directory=%s %s/snaptex2.tex'%(tmpdir,tmpdir))
	os.system(
		'convert -trim -density 300 '+
		'%s/snaptex2.pdf -quality 100 %s-eq%d.png'%(tmpdir,name,count+1))

#---RULES
#-------------------------------------------------------------------------------------------------------------

#---convert markdown to figure
figure_text = r"""
\begin{figure}[htbp]
\centering
\includegraphics%s{%s}
\caption{%s%s}
\end{figure}
"""

#---convert markdown to HTML figure
figlist = []
figure_text_html = """
<figure id="fig:%s" class="figure">
<a name="fig:%s"></a> 
<img src="%s" style="%s" align="middle">\n%s\n
</figure>
"""

def figure_convert(extracts):

	"""
	Convert markdown figure to latex figure. Handles optional caption, height, width (in linewidth) etc.
	"""

	args = [(key,re.findall('^%s=(.+)'%key,r).pop()) 
		for key in ['width','height'] 
		for r in extracts[3:] 
		if re.match('^%s=(.+)'%key,r)]
	graphics_args_rules = {'height':r'height=%s\textheight','width':'width=%s\linewidth'}
	figure_text_order = ['graphics_args','path','caption','label']
	figure_text_dictionary = {
		'path':image_location+extracts[1],
		'caption':extracts[0],
		'label':' \label{%s}'%extracts[2] if extracts[2]!='' else '',
		'graphics_args':('[width=1.0\linewidth]' if args == [] else (
			'['+','.join([graphics_args_rules[arg[0]]%arg[1] for arg in args])+']'))}
	return figure_text%tuple([figure_text_dictionary[f] for f in figure_text_order])

def figure_convert_html(extracts):

	"""
	Convert markdown figure to HTML with numbering.
	"""

	defaults = {'width':1.0}
	argdict = lambda s : {
		'width':'width:%.f%%;'%(float(s[1])*100),
		}[s[0]]
	extras = dict([ex.split('=') for ex in extracts[3].split(' ') if '=' in ex])
	arglist = [argdict((key,extras[key] if key in extras else defaults[key])) for key in defaults]
	extra_args = ''.join(['%s;'%i for i in arglist])
	figname = 'dummy%d'%len(figlist) if extracts[2] == '' else extracts[2]
	caption = '' if extracts[0] == '' else \
		"""<figcaption><strong>@fig:%s</strong> %s</figcaption>"""%(
		figname,extracts[0])
	figlist.append(figname)
	return figure_text_html% tuple([extracts[2],extracts[2],image_location+extracts[1],extra_args,caption])

#---RULES
#-------------------------------------------------------------------------------------------------------------

#---constants
labelchars = '[A-Za-z0-9_-]'
bibkey = '[a-zA-Z]+-[0-9]{4}[a-z]?'

#---special substutions for tex
specsubs = {
	r'%':r'\%',
	r' "':r' ``',
	r'" ':"'' ",
	r' \'':r' `',
	r'\' ':"' ",
	r'~':r'$\sim$',
	r'\.\.\.':r'\ldots',
	}

#---special stubstitutions for html
htmlspecsubs = {
	r'---':r"""&mdash;""",
	r'\\AA':r"\mathrm{\mathring{A}}",
	}

#---replacement rules for document processing
rules = {
	'^(#+)\s(.+)$':lambda s : '\%ssection{%s}\label{%s}'%((len(s[0])-1)*'sub',s[1],s[1].lower()),
	'^\$\$\s+?$':lambda s : r'\begin{equation}'+'\n',
	'^\$\$\s+{#(eq:.+)}':lambda s : '%s\end{equation}'%('' if s=='' else '\label{%s}\n'%s)+'\n',
	'^\!\[(.*)\]\((.+)\)\s?{?(?:#fig:([^\s=}]+))*\s?(.+=[^}]+)?}*':figure_convert,
	}

#---replacement rules for HTML
rules_html = {
	'^(#+)\s(.+)$':lambda s : '\n<br><h%d id="%s">%s</h%d>\n'%(len(s[0])+1,s[1].lower(),s[1],len(s[0])),
	'^\!\[(.*)\]\((.+)\)\s?{?(?:#fig:(%s+))*\s?(.+=[^}]+)?}*'%labelchars:figure_convert_html,
	'^\$\$\s+?$':lambda s : "$$"+('' if not vectorbold else vector_bold_command)+'\n'+\
		r"""\begin{equation}"""+'\n',
	'^\$\$\s+{#(eq:%s+)}'%labelchars:lambda s : r"%s\end{equation}"%(
		'' if s=='' else '\label{%s}\n'%s)+'\n'+'\n$$\n',
	'^>+\s*$':lambda s : s,
	'^[0-9]+\.\s?(.+)':lambda s : '<li>%s</li>\n'%s,
	}

#---set whether you want the word equation to appear
spacing_chars = '\s:\.,'
rules2 = {
	'@(eq:%s+)'%labelchars:r"equation \\eqref{\1}",
	'@fig:(%s+)'%labelchars:r"""figure (%s\\ref{\1})"""%figpref,
	'\[\[([^\]]+)\]\]':r"\pdfmarkupcomment[markup=Highlight,color=yellow]{\1}{}",
	'\:\:([^\>]+)\:\:':r"",
	'\<\<([^\>]+)\>\>':r"\\textcolor{babypink}{\pdfmarkupcomment[markup=Highlight,color=aliceblue]{\1}{}}",
	'\$([^\$]+)\$':r"$\mathrm{\1}$",
	'\*([^\*]+)\*':r'\emph{\1}',
	'\*\*([^\*]+)\*\*':r'\textbf{\1}',
	}
	
#---? figure will not be capitalized sometimes
#---? double asterisk may not work if dictionary in wrong order
rules2_html = {
	'@(eq:%s+)'%labelchars:r"""equation \eqref{\1}""",
	'(@fig:%s+)'%labelchars:r"""\1""",
	'\*\*([^\*]+)\*\*':r'<strong>\1</strong>',
	'\*([^\*]+)\*':r'<em>\1</em>',
	'\[\[([^\]]+)\]\]':r"""<span style="background-color: #FFFF00">\1</span>""",
	'\<\<([^\>]+)\>\>':r"""<span style="background-color: #F0F8FF; color: #F4C2C2">\1</span>""",
	'\:\:([^\>]+)\:\:':r"<!-- \1 -->",
	'\$([^\$]+)\$':r"$\mathrm{\1}$",
	"\\\pdfmarkupcomment\\[markup=[A-Za-z]+,color=[A-Za-z]+\\]\{([^\}]+)\}\{[^\}]*\}":
		r"""<span style="background-color: #FFFF00">\1</span>""",
	'`([^`]+)`':r"<code>\1</code>",
	'\[([^\]]+)\]\(([^\)]+)\)':r'<a href="\2">\1</a>',
	'^>\s*(.+)':r"<blockquote>\1</blockquote>",
	}
	
#---FUNCTIONS
#-------------------------------------------------------------------------------------------------------------

def linesnip(lines,*regex):

	"""
	Custom function for choosing sections of the markdown file for specific processing rules.
	"""

	if len(regex)==1:
		#---a single regex will return the line numbers for all matches
		line_nos = [ii for ii,i in enumerate(lines) if re.match(regex[0],i)]
	else:
		#---if multiple regexes then we return the line number for first match for each kind
		line_nos = []
		for reg in regex:
			sub_lines = lines[(slice(None,None) if len(line_nos)==0 else slice(line_nos[-1]+1,None))]
			new_lineno = [ii+(1 if len(line_nos)==0 else line_nos[-1]) 
				for ii,i in enumerate(sub_lines) if re.match(reg,i)]
			new_lineno = len(lines)-1 if new_lineno == [] else new_lineno[0]
			line_nos.append(new_lineno)
	#---if there are exactly two regexes we assume this is ending in a slice object so we move the end
	if len(line_nos)==2: line_nos[1] += 1
	return line_nos

def firstone(seq):

	"""
	Fast, ordered uniquify.
	"""

	seen = set()
	seen_add = seen.add
	return [ x for x in seq if not (x in seen or seen_add(x))]
	
#---MAIN
#-------------------------------------------------------------------------------------------------------------

#---load the file
filename_base = re.findall('^(.+)\.md$',os.path.basename(sys.argv[1]))[0]
with open(sys.argv[1],'r') as fp: lines = fp.readlines()

#---get the header data
if len(linesnip(lines,'^-+\s+?$')) != 2: raise Exception('cannot identify header bracketed by "---" lines')
header_text = [lines[l].strip() for l in range(*tuple(linesnip(lines,'^-+\s+?$')))]

#---get the title
find_title = [re.findall('title:\s?(.+)',l) for l in header_text]
if any(find_title): title = [i for i in find_title if i!=[]].pop().pop()
else: raise Exception('cannot find title in the header')

#---get path to images
find_image_path = [re.findall('^images:\s?(.+)',l) for l in header_text]
if any(find_image_path): image_location = [i for i in find_image_path if i!=[]].pop().pop()

#---get the abstract (no error checking here)
if any([re.match('^abstract',r) for r in header_text]):
	abstract = header_text[slice(*linesnip(header_text,'^abstract:\s?','(^-{3}-*|^[a-z_]+:)'))]
else: abstract = None

#---get authors
if any([re.match('^author:',r) for r in header_text]):
	authors = header_text[slice(*linesnip(header_text,'^author:\s?','(^-{3}-*|^[a-z]+:)'))]
	authors = [a.strip('- ') for a in authors]
else: authors = None

#---get the document_class
try:
	document_class = re.findall('^documentclass:\s?(.+)',
		header_text[linesnip(header_text,'^documentclass:\s?').pop()]).pop()
except: document_class = 'article'

#---get the figpref which allows for e.g. figure S1 for the supplement
if any([re.match('^figpref:\s?(.+)',r) for r in header_text]):
	figpref = re.findall('^figpref:\s?(.+)',
		header_text[linesnip(header_text,'^figpref:\s?(.+)').pop()]).pop()
if any([re.match('^eqnpref:\s?(.+)',r) for r in header_text]):
	eqnpref = re.findall('^eqnpref:\s?(.+)',
		header_text[linesnip(header_text,'^eqnpref:\s?(.+)').pop()]).pop()

#---get the flag for new fonts
if any([re.match('^fonts:',r) for r in header_text]):
	new_fonts = re.findall('^fonts:\s?(.+)',
		header_text[linesnip(header_text,'^fonts:\s?').pop()]).pop()
else: new_fonts = None

#---get the flag for skipping latex
if any([re.match('^pdf:',r) for r in header_text]):
	html_only = re.findall('^pdf:\s?(.+)',
		header_text[linesnip(header_text,'^pdf:\s?').pop()]).pop()
	html_only = False if re.match('^(true|True)',html_only) else True
else: html_only = False
#---! HACK
html_only = True
if html_only: authors = ''

#---get the flag for live development which adds a refresh option
if any([re.match('^livewrite:',r) for r in header_text]):
	livewrite = re.findall('^livewrite:\s?(.+)',
		header_text[linesnip(header_text,'^livewrite:\s?').pop()]).pop()
	livewrite = True if re.match('^(true|True)',livewrite) else False
else: livewrite = False

#---turn all vectors into bold characters instead of drawing the vector on top
if any([re.match('^vectorbold:',r) for r in header_text]):
	vectorbold = re.findall('^vectorbold:\s?(.+)',
		header_text[linesnip(header_text,'^vectorbold:\s?').pop()]).pop()
	vectorbold = True if re.match('^(true|True)',vectorbold) else False
else: vectorbold = False

#---write images for all equations
if any([re.match('^teximages:',r) for r in header_text]):
	teximages = re.findall('^teximages:\s?(.+)',
		header_text[linesnip(header_text,'^teximages:\s?').pop()]).pop()
	teximages = True if re.match('^(true|True)',teximages) else False
else: teximages = False

#---get the bibliography (no error checking here)
if any([re.match('^bibliography',r) for r in header_text]):
	bibfile = re.findall('^bibliography:\s?(.+)',
		header_text[linesnip(header_text,'^bibliography:\s?').pop()]).pop()
else: bibfile = None

#---get the latex header file
with open('./cas/sources/header-article.tex','r') as fp: latex_header = fp.readlines()
with open('./cas/sources/header.html','r') as fp: html_header = fp.readlines()

#---document class is substituted immediately
for ll,line in enumerate(latex_header): latex_header[ll] = re.sub('DOCCLASS',document_class,line)

#---vectors changed to bold
if vectorbold:
	latex_header.append(r'%---all vectors are bold'+'\n')
	latex_header.append(r'\renewcommand{\vec}[1]{\mathbf{#1}}'+'\n')
	if eqnpref != '':
		latex_header.append(r"\renewcommand{\theequation}{%s.\arabic{equation}}"%eqnpref)

if livewrite: html_header.insert([ii for ii,i in enumerate(html_header) 
	if re.match('\s*<meta',i)][0]+1,'<meta http-equiv="refresh" content="20">\n')

if authors == None: authorsub = ''
else: authorsub = ''.join(['%s;'%a for a in authors])
for ll,l in enumerate(latex_header):
	latex_header[ll] = re.sub('@AUTHORS',authorsub,l)
out = list(latex_header)

#---add title and abstract
out.append('\n'+r'\title{%s}'%title+'\n')
if authors != None: out.append(r'\author{%s}'%r' \and '.join(authors)+'\n')

#---add extra css files
if new_fonts == None: extra_css = "\n"
else: 
	extra_css = \
		"""<link rel="stylesheet" href="./cas/sources/fonts-%s.css" type="text/css" />"""%new_fonts

#---replace title in html header
for ll,l in enumerate(html_header):
	if re.search('@TITLE',l) != None:
		html_header[ll] = re.sub('@TITLE',title,l)
	if re.search('@EXTRA_CSS',l) != None:
		html_header[ll] = re.sub('@EXTRA_CSS',extra_css,l)
html = list(html_header)

if authors not in [None,'']: 
	html.append('\n<br><h3>Authors</h1><ul>\n')
	for a in authors: html.append('<li> %s'%a)
	html.append('</ul>\n')
if abstract != None:
	html.append('<h3>Abstract</h1>\n')
	for line in abstract: html.append(line+'\n')
out.append(r'\begin{document}'+'\n')
out.append(r'\maketitle'+'\n')
if abstract != None:
	out.append(r'\begin{abstract}'+'\n')
	for line in abstract: out.append(line+'\n')
	out.append(r'\end{abstract}'+'\n')

#---LOOP
#-------------------------------------------------------------------------------------------------------------

#---all remaining text
inside_equation = False
inside_equation_html = False
inside_codeblock = False
inside_figure = False
state,reforder = 'normal',[]
current_equation = ''
for line in lines[linesnip(lines,'^-+\s+?$')[-1]+1:]: 

	htmlline = str(line)
	matches = [r for r in rules if re.match(r,line)]
	matches_html = [r for r in rules_html if re.match(r,htmlline)]

	#---use re.split and re.findall to iteratively replace references in groups
	if bibfile != None and re.search('(\[?@[a-zA-Z]+-[0-9]{4}[a-z]?\s?;?\s?)+\]?',line)!=None:

		refs = re.findall('\[?@(%s)(?:\s|\])?'%bibkey,line)
		notrefs = re.split('@%s'%bibkey,line)
		reforder.extend(refs)
		#---cannot start a line with a reference
		newline = list([notrefs[0].rstrip('[')])
		inside_reference = False
		for ii,i in enumerate(notrefs[1:]):
			if inside_reference == False: 
				newline.append('\%s{'%citation_type)
				inside_reference = True
			newline.append(refs[ii])
			if re.match('^\s*;?\s*$',i): newline.append(',')
			elif inside_reference: 
				newline.append('}'+i.lstrip(']'))
				inside_reference = False
			else: newline.append(i.rstrip('['))
		line = ''.join(newline)	

	#---special regex substitutions according to rules dictionary
	if any(matches):

		#---special behavior depending on the match
		r = matches.pop()

		#---if no equation label
		if r == '^\$\$\s+?$' and inside_equation:
			r = '^\$\$\s+{#(eq:.+)}'
			line = rules['^\$\$\s+{#(eq:.+)}']('')			
		elif r == '^\$\$\s+{#(eq:.+)}':
			line = rules[r](re.findall(r,line).pop())
			#---added to extract equation
			current_equation += line +'\n'
			if teximages: write_tex_png(current_equation,filename_base,total_equations_written)
			total_equations_written += 1
			current_equation = ''
		else: 
			line = rules[r](re.findall(r,line).pop())
			current_equation += line +'\n'
		if r in ['^\$\$\s+?$','^\$\$\s+{#(eq:.+)}']: 
			#---added to extract equation
			current_equation = ''
			inside_equation = not inside_equation
	#---added to extract equation
	if inside_equation: current_equation += line +'\n'

	#---handle special rules to html
	if any(matches_html):

		#---special behavior depending on the match
		r = matches_html.pop()

		#---handle ordered lists
		if r == '^[0-9]+\.\s?(.+)' and state == 'normal':
			html.append('<ol>\n')
			state = 'inside_ol'

		#---handle equations with and without labels
		if r == '^\$\$\s+?$' and inside_equation_html:
			r = '^\$\$\s+{#(eq:%s+)}'%labelchars
			htmlline = rules_html['^\$\$\s+{#(eq:%s+)}'%labelchars]('')			
		elif r == '^\$\$\s+{#(eq:%s+)}'%labelchars:
			htmlline = rules_html[r](re.findall(r,htmlline).pop())
		elif r == '^>+\s*$':
			htmlline = ''
			if not inside_codeblock:
				html.append('<blockquote><code>')
				inside_codeblock = True
			else:
				html.append('</code></blockquote>')
				inside_codeblock = False

		#---regular substitutions via rules_html
		#---in the else case we previous popped off the only findall result but now we allow more than one
		else: 
			finds = re.findall(r,htmlline)
			if len(finds) == 1: htmlline = rules_html[r](finds.pop())
			else: htmlline = rules_html[r](finds)

		#---leave equation
		if r in ['^\$\$\s+?$','^\$\$\s+{#(eq:%s+)}'%labelchars]:
			inside_equation_html = not inside_equation_html

	#---ending an ol happens by inference
	if state in ['inside_ol','trailing_ol']:
		if not re.match('^\s*$',htmlline) and r != '^[0-9]+\.\s?(.+)':
			html.append('</ol>\n')
			state = 'normal'
		elif re.match('^\s*$',htmlline): state = 'trailing_ol'

	#---special latex characters
	for a,b in specsubs.items(): line = re.sub(a,b,line)
	for a,b in htmlspecsubs.items(): htmlline = re.sub(a,b,htmlline)

	#---group-extracting rules
	for rule in rules2:
		line = re.sub(rule,rules2[rule],line)
	#---group-extracting rules
	for rule in rules2_html:
		htmlline = re.sub(rule,rules2_html[rule],htmlline)

	#---items in a list 
	if state == 'inside_ol' and re.match('^[0-9]+\.\s?',htmlline): 
		htmlline = '<li>%s</li>\n'%re.search('\s?[0-9]+\.\s?(.+)',htmlline).group(1)

	#---add line breaks to html to match latex standard
	if re.match('^\s*$',htmlline) and not inside_codeblock and state == 'normal': 
		htmlline = '<p>\n'

	#---iteratively construct the file
	html.append(htmlline)
	out.append(line)

#---WRITE
#-------------------------------------------------------------------------------------------------------------

if bibfile != None:
	try: bibfile_expanded = os.readlink(os.path.expanduser(os.path.abspath(bibfile)))
	except:  bibfile_expanded = os.path.expanduser(os.path.abspath(bibfile))
	out.append(r'\bibliography{%s}'%re.findall('^([^.]+)\.bib',bibfile_expanded).pop()+'\n')
out.append(r'\end{document}'+'\n')

#---replace numbered figure captions first
for lineno,line in enumerate(html):
	if re.search('<strong>@fig:(%s+)</strong>'%labelchars,line) != None:
		figlabel = re.findall('<strong>@fig:(%s+)</strong>'%labelchars,line).pop()
		html[lineno] = re.sub('<strong>@fig:%s</strong>'%figlabel,
			'<strong>Figure %s%d.</strong>'%(figpref,figlist.index(figlabel)+1),line)

#---link to figure captions
for lineno,line in enumerate(html):
	if re.search('@fig',line) != None:
		for figlabel in re.findall('@fig:(%s+)'%labelchars,html[lineno]):
			if re.search('@fig:%s([%s])'%(figlabel,spacing_chars),html[lineno]):
				html[lineno] = re.sub('@fig:%s([%s])'%(figlabel,spacing_chars),
					r'figure (<a href="#fig:%s">%s%s</a>)\1'%(figlabel,figpref,figlist.index(figlabel)+1),
					html[lineno])
			else:
				#---! this might be necessary to have the figure link in parentheses
				html[lineno] = re.sub('@fig:%s()'%figlabel,
					r'figure (<a href="#fig:%s">%s%s</a>)\1'%(figlabel,figpref,figlist.index(figlabel)+1),
					html[lineno])

#---capitalize the word figure in the html and tex files
#import pdb;pdb.set_trace()
for lineno,line in enumerate(html):
	html[lineno] = re.sub(r'\. figure',r'. Figure',html[lineno])
	html[lineno] = re.sub('^figure','Figure',html[lineno])
for lineno,line in enumerate(out):
	out[lineno] = re.sub(r'\. figure',r'. Figure',out[lineno])
	out[lineno] = re.sub('^figure','Figure',out[lineno])
#---write the tex file
#---! removed text/ from below
outname = re.findall('^(.+)\.md$',sys.argv[1]).pop()

#with open('cas/hold/%s.tex'%outname,'w') as fp:
#	for line in out: fp.write(line)

#---BIB
#-------------------------------------------------------------------------------------------------------------

if bibfile != None:

	with open(bibfile_expanded,'r') as fp: biblines = fp.readlines()

	#---entry starting line numbers
	lnos = linesnip(lines,'@')
	bibkeys = [re.findall('@[A-Za-z]+\s?\{([^,]+),',biblines[ll]).pop() for ll in linesnip(biblines,'@')]
	reforderno = [bibkeys.index(i) for i in reforder]
	ords = firstone(reforderno)
	ordlookup = dict([(bibkeys[i],ords.index(i)) for i in ords])
	html.append('<br><h2>References</h2><br>\n')
	html.append('<ol>\n')
	
	#---replace references with numbers
	for lineno,line in enumerate(html):
		if re.search('@%s'%bibkey,line) != None:
			for found in re.findall('@(%s)+'%bibkey,line):
				html[lineno] = re.sub('@%s'%found,
					'[<a href="#refno%d">%d</a>]'%(ordlookup[found]+1,ordlookup[found]+1),html[lineno])

	details = {}
	for key in ordlookup.keys():
		#---extract data from bibtex
		dat = ''.join(biblines[slice(*linesnip(biblines,'@[A-Za-z]+\{%s'%key,'@'))])
		authors = ''.join(re.findall('Author\s*=\s*\{([^\}]+)',dat))
		year = int(re.findall('Year\s*=\s*\{([^\}]+)',dat)[0])
		title = re.findall('Title\s*=\s*\{([^\}]+)',dat)[0]
		try: journal = re.findall('Journal\s*=\s*\{([^\}]+)',dat)[0]
		except: journal = ''
		url = re.findall('Url\s*=\s*\{([^\}]+)',dat)[0]
		if journal != '':
			entry = '%s.<br><a href="%s">%s</a>.<br><em>%s</em>, %d.'%(authors,url,title,journal,year)
		else:
			#---! probably a book?
			entry = '%s.<br><a href="%s">%s</a>, %d.'%(authors,url,title,year)
		details[key] = entry

	#---loop over references at the end
	for refno,refkey in enumerate(ords):
		html.append('<li><a name="refno%d"></a>%s</li>'%(refno+1,details[bibkeys[refkey]]))

#---terminate the HTML file
html.append(r'<br><br></div></div></div></body>'+'\n')

#---write the html file
#---! removed text/ from below
with open(re.findall('^(.+)\.md$',sys.argv[1]).pop()+'.html','w') as fp:
	for line in html: fp.write(line)

#---COMPILE
#-------------------------------------------------------------------------------------------------------------

if 'dev' not in sys.argv and not html_only:
	
	os.system(pdflatex+' -halt-on-error --output-directory=cas/hold/ %s.tex'%outname)
	if bibfile != None:
		os.system('bibtex cas/hold/%s'%outname)
		os.system(pdflatex+' -halt-on-error --output-directory=cas/hold/ %s.tex'%outname)
	os.system(pdflatex+' -halt-on-error --output-directory=cas/hold/ %s.tex'%outname)
