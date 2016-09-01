#!/usr/bin/python

"""
Create a nice tiled web page from a yaml spec file.
"""

import re,sys,glob,subprocess,shutil,os
import yaml

spec_file = sys.argv[1]
assert os.path.isfile(spec_file)
if re.match('\.yaml$',spec_file):
	with open(spec_file) as fp: maps = yaml.load(re.sub('\t','  ',fp.read()))
else:
	#---assume a python-formatted dictionary is available in the incoming file
	with open(spec_file) as fp: maps = eval(fp.read())
print "[STATUS] running tiler according to %s"%spec_file

###---SETTINGS

#---! allow overrides
layout = {
	'brick_width':300,
	'brick_image_width':250,
	}

#---incoming paths
index_fn = 'index.html' if 'dropfile' not in maps['path'] else maps['path']['dropfile']
dropdir = './' if 'dropdir' not in maps['path'] else maps['path']['dropdir']
subdir = 'index-tiles' if 'tile-files' not in maps['path'] else maps['path']['tile-files']

###---CONSTANTS

html_template = ["""

<!DOCTYPE html>
<html>
<head>
<title>gallery</title>
<meta content="text/html; charset=utf-8" http-equiv="content-type">
<meta name="description" content="DISPATCHER" />
<meta name="keywords" content="much content"/>
<script type="text/javascript" src="SUBDIR/jquery-1.10.2.min.js"></script>
<script type="text/javascript" src="SUBDIR/freewall.js"></script>
<link rel="stylesheet" type="text/css" href="SUBDIR/style.css"/>

<style>
body {
  background: #e8e8e8;
  font-family: 'Helvetica Neue', Helvetica, Arial;
}
#container {
  width: 90%;
  margin: 0 0 50px 50px;
}
.brick {
  background: white;
  /*box-shadow: 0 1px 5px 0 rgba(0, 0, 0, 0.33);*/
  border-radius: 5px;
  color: #333;
  border: solid #666699 2px ;
  width: BRICK_WIDTHpx;
  margin: 0px;
  padding: 0px;
}
.brick .inbrick { padding 0px; margin: 20px; }
.brick .inbrick img { 
  max-width: BRICK_IMAGE_WIDTHpx; 
}
</style>
</head>
<body>

<div class="container">
<div class="filter-items">
<div class="filter-label active">all</div>
""",
"""
</div>

<div id="container">
""",
"""
</div>

<script type="text/javascript">
$(window).on("load",function() {
  var wall = new Freewall("#container");
  wall.reset({
    selector: '.brick',
    animate: true,
    cellW: BRICK_WIDTH,
    cellH: 'auto',
    fixSize: 0,
    onResize: function() {
      wall.refresh();
    }
  });
  $(".filter-label").click(function() {
    $(".filter-label").removeClass("active");
    var filter = $(this).addClass('active').data('filter');
    if (filter) {
      wall.filter(filter);
    } else {
      wall.unFilter();
    }
  });
  wall.fitWidth();
});
</script>

</body>
</html>
"""]

html_brick_image = """
  <div class="brick CATEGORIES"><div class="inbrick">
  <strong>TITLE</strong>
  <img src="SRC"><br><code>CONTENT</code>
  </div></div>
"""

html_brick_draft = """
  <div class="brick CATEGORIES"><div class="inbrick">
  <p style="color:gray"><img src="SUBDIR/cassette.png" width="50px"><br><strong>DRAFT</strong></p>
  <strong>TITLE</strong><br>
  <code>CONTENT</code>
  </div></div>
"""

html_brick_file = """
  <div class="brick CATEGORIES"><div class="inbrick">
  <p style="color:black"><img src="SUBDIR/file_icon.png" width="30px"><br><strong>FILE</strong></p>
  <strong>TITLE</strong><br>
  <code>CONTENT</code>
  </div></div>
"""

###---FUNCTIONS

def pathfinder(path):

	"""
	Figure out relative directory.
	"""

	global dropdir
	out = re.sub(dropdir+'/?','',path)
	out = re.sub(os.path.expanduser(dropdir)+'/?','',out)
	return out

def pointer(concept,symbol):

	"""
	Given a concept, use a symbol to look up the article or none.
	More specifically, look up another value in the dictionary.
	"""

	global maps
	article = None
	marker = '^\s*\+(.+)'
	if re.match(marker,symbol): symbol = re.findall(marker,symbol)[0]
	if concept in maps and symbol in maps[concept]: article = maps[concept][symbol]
	return article

#---valid movie formats
movie_formats = ['mp4','webm','mpg','mpeg']

###---MAIN
dropdir_abs = os.path.abspath(os.path.expanduser(dropdir))
images_dn = os.path.join(os.path.expanduser(dropdir),subdir)
if not os.path.isdir(images_dn): os.mkdir(images_dn)
for fn in glob.glob('cache/tiler/*'): shutil.copy(fn,images_dn)

new_bricks,master_categories = {'drafts':[],'videos':[]},[]
for key,item in maps.items():
	if 'type' not in item: continue
	route = {}
	if item['type'] == 'video':
		route['title'] = item['name']
		path = pointer('path',item['path'])
		path = os.path.join(os.path.abspath(os.path.expanduser(path)),'')
		assocs = glob.glob(path+key+'*')
		linked = [(ext,assoc) for assoc in assocs 
			for ext in movie_formats if re.match('^.+\.%s$'%ext,assoc)]	
		assert linked != []
		#---! take the first video and take a snapshot
		if not os.path.isfile('%s/%s.jpg'%(images_dn,key)):
			proc = subprocess.Popen(
				'ffmpeg -ss 00:00:00 -i %s -frames:v 1 %s/%s.jpg'%(linked[0][1],images_dn,key),
				shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=dropdir_abs)
			proc.communicate()
		route['src'] = '%s.jpg'%(os.path.join(pathfinder(images_dn),key))
		master_categories.extend(item['categories'])
		route['categories'] = ' '.join([i+'brick' for i in item['categories']])
		route['content'] = '<br>%s'%item['description']
		for link in linked:
			route['content'] += '<br><a href="%s"><strong>+%s</strong></a>'%(
				pathfinder(link[1]),link[0])
		new_brick = str(html_brick_image)
		for key,val in route.items(): new_brick = re.sub(key.upper(),val,new_brick)
		new_bricks['videos'] += [new_brick]
	elif item['type'] == 'draft':
		route['title'] = item['name']
		master_categories.extend(item['categories'])
		route['categories'] = ' '.join([i+'brick' for i in item['categories']])
		route['content'] = item['description']
		path = pathfinder(item['path'])
		route['content'] += '<br><a href="%s"><strong>contents</strong></a>'%path
		new_brick = str(html_brick_draft)
		for key,val in route.items(): new_brick = re.sub(key.upper(),val,new_brick)
		new_bricks['drafts'] += [new_brick]
	elif item['type'] == 'file':
		route['title'] = item['name']
		master_categories.extend(item['categories'])
		route['categories'] = ' '.join([i+'brick' for i in item['categories']])
		route['content'] = item['description']
		path = pathfinder(item['path'])
		route['content'] += '<br><a href="%s"><strong>download</strong></a>'%path
		new_brick = str(html_brick_file)
		for key,val in route.items(): new_brick = re.sub(key.upper(),val,new_brick)
		new_bricks['drafts'] += [new_brick]
	elif item['type'] == 'image':
		route['title'] = item['name']
		route['content'] = item['content']
		#---! this uses absolute paths probably from glob
		route['src'] = item['path']
		#---categorize by figure names
		route['categories'] = ['all']+item['categories']
		master_categories.extend(route['categories'])
		route['categories'] = ' '.join([i+'brick' for i in route['categories']])
		new_brick = str(html_brick_image)
		for key,val in route.items(): new_brick = re.sub(key.upper(),val,new_brick)
		new_bricks['drafts'] += [new_brick]
	else: raise Exception('unclear brick type')

for key,val in layout.items():
	for bnum,brick in enumerate(html_template):
		html_template[bnum] = re.sub(key.upper(),str(val),brick)

bricks = html_template[:1]
for category in list(set(master_categories)):
	bricks.append('<div class="filter-label" data-filter=".%sbrick">%s</div>'%
		(category,category))
bricks += html_template[1:2]
#---reorder the bricks to put drafts earlier
for key in ['drafts','videos']: bricks.extend(new_bricks[key])
bricks += html_template[-1:]

with open(os.path.join(os.path.expanduser(dropdir_abs),index_fn),'w') as fp:
	for brick in bricks: fp.write(re.sub('SUBDIR',subdir,brick))
