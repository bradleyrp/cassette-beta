#!/usr/bin/python

import os,sys,re,subprocess
from collections import OrderedDict as odict

#---CONSTANTS
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

figpref = '' #---!
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
		#---! hack for testing
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

#---CLASSES
#-------------------------------------------------------------------------------------------------------------

class MDHeaderText:

	def __init__(self,lines):

		if len(linesnip(lines,'^-+\s+?$')) != 2: 
			raise Exception('cannot identify header bracketed by "---" lines')
		self.text = [lines[l].strip() for l in range(*tuple(linesnip(lines,'^-+\s+?$')))]

	def spec(self,key):

		"""
		Return a single-line specification
		"""

		find_spec = [re.findall('%s:\s?(.+)'%key,l) for l in self.text]
		#---! double pop?
		if any(find_spec): return [i for i in find_spec if i!=[]].pop().pop()
		else: return False

	def specblock(self,key):

		"""
		Read a spec from the header until the next item or the end.
		"""

		try: return self.text[slice(*linesnip(self.text,'^%s:\s?'%key,'(^-{3}-*|^[a-z_]+:)'))]
		except: return False

class TexDocument:

	"""
	Holds a LaTeX document for rendering.
	"""

	package_prefix = 'pack'
	citation_type = 'cite'
	latex_sectioner = '^%---REPLACE\s*(.+)\s*$'
	markup_regex = "\\\pdfmarkupcomment\\[markup=[A-Za-z]+,color=[A-Za-z]+\\]\{([^\}]+)\}\{[^\}]*\}"
	vector_bold_command = r'%---all vectors are bold'+'\n'+r'\renewcommand{\vec}[1]{\mathbf{#1}}'+'\n'

	rules = {
		'^(#+)\s(.+)$':lambda s : '\%ssection{%s}\label{%s}'%((len(s[0])-1)*'sub',s[1],s[1].lower()),
		'^\$\$\s+?$':lambda s : r'\begin{equation}'+'\n',
		'^\$\$\s+{#(eq:.+)}':lambda s : '%s\end{equation}'%('' if s=='' else '\label{%s}\n'%s)+'\n',
		}

	#---note that order matters in the following dictionary
	subs = odict([
		('@(eq:%s+)'%labelchars,r"equation \\eqref{\1}"),
		#---! self.figpref defined below
		('@fig:(%s+)'%labelchars,r"""figure (%s\\ref{\1})"""%''),
		('\[\[([^\]]+)\]\]',r"\pdfmarkupcomment[markup=Highlight,color=yellow]{\1}{}"),
		('\:\:([^\>]+)\:\:',r""),
		('\<\<([^\>]+)\>\>',
			r"\\textcolor{babypink}{\pdfmarkupcomment[markup=Highlight,color=aliceblue]{\1}{}}"),
		('\$([^\$]+)\$',r"$\mathrm{\1}$"),
		('\*\*([^\*]+)\*\*',r'\\textbf{\1}'),
		('\*([^\*]+)\*',r'\emph{\1}'),
		#---note that we blank the backtick syntax used in HTML
		('`([^`]+)`',r'\1'),
		])

	#---order matters
	special_subs = odict([
		(r'%',r'\%'),
		(r' "',r' ``'),
		(r'" ',"'' "),
		(r' \'',r' `'),
		(r'\' ',"' "),
		(r'~',r'$\sim$'),
		(r'\.\.\.',r'\ldots'),
		])
	
	def __init__(self,fn,**kwargs):

		if type(fn)==list: raise Exception('expecting a file name')
		else: 
			with open(fn) as fp: self.raw = fp.readlines()
			self.name = re.findall('([^\/]+)\.md$',fn)[0]
		newrules = {'^\!\[(.*)\]\((.+)\)\s?{?(?:#fig:([^\s=}]+))*\s?(.+=[^}]+)?}*':self.figure_convert}
		self.rules.update(**newrules)
		self.specs = MDHeaderText(self.raw)
		self.refs = []
		package = kwargs.pop('package',False)
		if kwargs: raise TypeError('unexpected **kwargs: %r'%kwargs)
		#---previously used one header_type = self.specs.spec('documentclass')
		render_types = ['revtex','article','pnas'][:2]
		for rt in render_types:
			self.style = rt
			if self.header_true(self.specs.spec(rt)):
				
				self.parts = odict()
				with open('./cas/sources/header-%s.tex'%rt) as fp: self.parts['header'] = fp.readlines()
				self.sections = odict([(re.findall(self.latex_sectioner,i)[0],ii) 
					for ii,i in enumerate(self.parts['header']) if re.match(self.latex_sectioner,i)])
				self.image_location = self.specs.spec('images')
				self.bibfile = self.specs.spec('bibliography')
				
				#---cancel if nrecessary
				if not self.header_true(self.specs.spec('avoid')): 
					print "[STATUS] rendering to PDF in %s format"%rt
					self.figpref = ''
					self.direct()
					self.proc()
					self.bib()
					self.blanker()

					#---extras
					if self.header_true(self.specs.spec('vectorbold')): self.header_more(self.vector_bold_command)

					#---output
					if package:
						self.package_dir = self.package_prefix+'-'+rt+'-'+self.name
						if not os.path.isdir(self.package_dir): os.mkdir(self.package_dir)
					else: self.package_dir = './'
					self.write('%s/%s.tex'%(self.package_dir,self.name))
					self.render('%s/%s.tex'%(self.package_dir,self.name),directory=self.package_dir)

	def header_true(self,text):

		"""
		Interpret true, false, yes, and no from the header text.
		"""

		if type(text)==bool and not text: return False
		return True if re.match('(true|True|yes|Yes)',text) else False

	def header_more(self,line):

		"""
		Add a line to the header.
		"""

		lastline = next(ii for ii,i in enumerate(self['header']) if re.match('^\s*\%-+END HEADER',i))
		self['header'].insert(lastline,line)

	def direct(self):

		"""
		For each section of the ...
		"""

		author_affiliation_pointer = '^([^@]+)\s*@(.+)$'
		instructions = {
			'end':r'\end{document}',
			'maketitle':'\\maketitle',
			'title':r'\title{%s}'%self.specs.spec('title'),
			'abstract':('\n\\begin{abstract}\n'+'\n'.join(self.specs.specblock('abstract'))+'\n\\end{abstract}'
				if self.specs.specblock('abstract')!=['---'] else ''),
			'body':self.body(),
			'bbl':'\\bibliography{%s}\n'%os.path.abspath(self.specs.spec('bibliography')),
			}

		print [(i.lower(),j) for i,j in self.sections.items()]
		for placeholder,header_lineno in [(i.lower(),j) for i,j in self.sections.items()]: 
			if placeholder in instructions:
				self.add(**{placeholder.lower():instructions[placeholder]})
			else:

				#---! no authors is broken
				if placeholder == 'authors' and self.specs.specblock('author')!=['---']:

					authorlines = []
					self.institutions = dict([re.findall('^\s*(\w+)\s*=\s*(.+)\s*$',i)[0] 
						for i in self.specs.specblock('institutions')])
					self.authors = odict()
					for auth in self.specs.specblock('author'):
						if re.match(author_affiliation_pointer,auth):
							authdat = re.findall(author_affiliation_pointer,auth)[0]
							self.authors[authdat[0].strip()] = [i.strip() for i in authdat[1].split(',')]
						else: self.authors[auth] = None
					#---! hack
					if self.style != 'article':
						for author,institutions in self.authors.items():
							authorlines.append('\\author{%s}\n'%author)
							if institutions != None:
								for i in institutions:
									authorlines.append('\\affiliation{%s}\n'%self.institutions[i])
						self.add(authors=authorlines)
				elif placeholder == 'authors' and self.specs.specblock('author')==['---']:
					print '[STATUS] no authors for this document'
				else: 
					raise Exception('dev %s'%placeholder)
			self.parts['header'][header_lineno] = ''

	def __getitem__(self,index): return self.parts[index]

	def body(self):

		"""
		Extract the body of the text, separating it from the header.
		"""

		return self.raw[linesnip(self.raw,'^-+\s+?$')[-1]+1:]

	def add(self,**kwargs):

		"""
		Add a component of the document.
		"""

		for key,val in kwargs.items(): self.parts[key] = val

	def write(self,fn):

		"""
		Write the document to tex formation.
		"""

		with open(fn,'w') as fp:
			for key,val in self.parts.items():
				if type(val)==str: fp.write(val)
				elif type(val)==list:
					for line in val: fp.write(line)
				else: raise Exception('\n[ERROR] cannot understand this part of the document: %s'%key)
				fp.write('\n')


	def render(self,filename,directory='./'):

		"""
		Render the LaTeX document to pdf.
		"""

		outname = re.findall('([^\/]+)\.tex$','%s/%s.tex'%(self.package_dir,self.name))[0]
		os.system('pdflatex --output-directory=%s %s'%(directory,filename))
		print outname
		if self.bibfile != None:
			subprocess.check_call('bibtex '+outname,cwd=directory,shell=True)
			os.system('pdflatex --output-directory=%s %s'%(directory,filename))
			os.system('pdflatex --output-directory=%s %s'%(directory,filename))

	def figure_convert(self,extracts):

		"""
		Convert markdown figure to latex figure. 
		Handles optional caption, height, width (in linewidth) etc.
		"""

		args = [(key,re.findall('^%s=(.+)'%key,r).pop()) 
			for key in ['width','height'] 
			for r in extracts[3:] 
			if re.match('^%s=(.+)'%key,r)]
		graphics_args_rules = {'height':r'height=%s\textheight','width':'width=%s\linewidth'}
		figure_text_order = ['graphics_args','path','caption','label']
		figure_text_dictionary = {
			#---! hack for testing
			'path':self.image_location+extracts[1],
			'caption':extracts[0],
			'label':' \label{%s}'%extracts[2] if extracts[2]!='' else '',
			'graphics_args':('[width=1.0\linewidth]' if args == [] else (
				'['+','.join([graphics_args_rules[arg[0]]%arg[1] for arg in args])+']'))}
		return figure_text%tuple([figure_text_dictionary[f] for f in figure_text_order])

	def proc(self,part='body'):

		"""
		Perform all text transformations for the body of a document.
		"""

		#---entire-line replacements in the body
		for lineno,line in enumerate(self.parts[part]):
			for rule in self.rules:
				if re.match(rule,line):
					#---! might not be the best way to write the rules
					self.parts[part][lineno] = self.rules[rule](re.findall(rule,line)[0])

		#---substitution rules
		for lineno,line in enumerate(self.parts[part]):
			for rule,convert in self.subs.items():
				self.parts[part][lineno] = re.sub(rule,convert,self.parts[part][lineno])

		#---special latex substitutions
		for lineno,line in enumerate(self.parts[part]):
			for a,b in self.special_subs.items(): 
				self.parts[part][lineno] = re.sub(a,b,self.parts[part][lineno])

		#---capitalize figures
		for lineno,line in enumerate(self.parts[part]):
			self.parts[part][lineno] = re.sub(r'\. figure',r'. Figure',self.parts[part][lineno])
			self.parts[part][lineno] = re.sub('^figure','Figure',self.parts[part][lineno])


	def blanker(self,part='body'):

		"""
		Remove anything in the pattern.
		HACKED to only remove markups.
		"""

		#---substitution rules
		for lineno,line in enumerate(self.parts[part]):
			for rule,convert in self.subs.items():
				self.parts['body'][lineno] = re.sub(self.markup_regex,'',self.parts['body'][lineno])

	def bib(self,part='body'):

		"""
		Replace markdown citations with LaTeX citations.
		"""

		#---use re.split and re.findall to iteratively replace references in groups
		for lineno,line in enumerate(self.parts[part]):
			if re.search('(\[?@[a-zA-Z]+-[0-9]{4}[a-z]?\s?;?\s?)+\]?',line)!=None:
				refs = re.findall('\[?@(%s)(?:\s|\])?'%bibkey,line)
				notrefs = re.split('@%s'%bibkey,line)
				self.refs.extend(refs)
				#---! cannot start a line with a reference
				newline = list([notrefs[0].rstrip('[')])
				inside_reference = False
				for ii,i in enumerate(notrefs[1:]):
					if inside_reference == False: 
						newline.append('\%s{'%self.citation_type)
						inside_reference = True
					newline.append(refs[ii])
					if re.match('^\s*;?\s*$',i): newline.append(',')
					elif inside_reference: 
						newline.append('}'+i.lstrip(']'))
						inside_reference = False
					else: newline.append(i.rstrip('['))
				self.parts[part][lineno] = ''.join(newline)	
