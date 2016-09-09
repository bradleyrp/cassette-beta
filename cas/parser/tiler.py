#!/usr/bin/python

"""
LIBRARY TILER [v2]
Create a nice tiled web page from a yaml spec file.
supercedes (and derived from) the tiler in the cassette
each brick entry needs at least a path
default type is "file"
devnotes:
	need to stop annoying refresh on touch devices
	need to clear thumbnail folders when files are deleted
	synchronize with the actual cassette code
"""

import re,sys,glob,subprocess,shutil,os
import yaml

#---parse the incoming yaml file
spec_file = sys.argv[1]
assert os.path.isfile(spec_file)
if re.match('^.+\.yaml$',spec_file):
	#---allow tab characters in the yaml file
	with open(spec_file) as fp: maps = yaml.load(re.sub('\t','  ',fp.read()))
else:
	#---assume a python-formatted dictionary is available in the incoming file
	with open(spec_file) as fp: maps = eval(fp.read())
print("[STATUS] running tiler according to %s"%spec_file)

###---SETTINGS

#---valid movie formats
movie_formats = ['mp4','webm','mpg','mpeg']

#---category list (and ordering)
category_list = ['drafts','videos','all']

#---brick dimensions
layout = {
	'brick_width':300,
	'brick_image_width':250,
	}

#---protected keywords
protected_keywords = ['deprecated','path']

#---incoming paths have defaults so this script has multiple uses
index_fn = 'index.html' if 'dropfile' not in maps['path'] else maps['path']['dropfile']
dropdir = './' if 'dropdir' not in maps['path'] else maps['path']['dropdir']
dropdir = os.path.expanduser(dropdir)
subdir = maps['path'].get('tile-files','index-tiles')
subdir_thumbs = maps['path'].get('thumb-files',os.path.join(subdir,'thumbs'))
#---brick settings are overridden by the maps
if 'brick_width' in maps: layout['brick_width'] = maps.pop('brick_width')
if 'brick_image_width' in maps: layout['brick_image_width'] = maps.pop('brick_image_width')

###---CONSTANTS

html_template = ["""

<!DOCTYPE html>
<html>
<head>
<title>DISPATCHER</title>
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
  <a name="HASHLABEL"></a>
  <img src="SRC"><br><code>CONTENT</code>
  </div></div>
"""

html_brick_sound = """
  <div class="brick CATEGORIES"><div class="inbrick">
  <strong>TITLE</strong><br><br>
  <a name="HASHLABEL"></a>
  <audio controls>
    <source src="SRC">
    Your browser does not support the audio element.
  </audio> 
  <br>CONTENT
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

###---TEMPLATING

def thumbnailer(src,dest,width=600):

	"""
	Render a thumbnail with a specific width.
	"""

	out_fn = os.path.join(dest,os.path.basename(src))
	if os.path.isfile(out_fn):
		thumb_time = os.path.getmtime(out_fn)
		src_time = os.path.getmtime(src)
		rerender = thumb_time<src_time
	else: rerender = True
	if rerender:
		print("[STATUS] making thumbnail %s"%os.path.basename(src))
		out_fn = os.path.join(dest,os.path.basename(src))
		subprocess.check_call('convert -resize %d %s %s'%(width,
			src,out_fn),shell=True)
	else: print("[STATUS] current thumbnail %s"%os.path.basename(src))
	return out_fn

def make_brick(name,spec,template='file'):

	"""
	Process a dictionary item into an HTML "brick".
	"""

	global new_bricks
	global master_categories
	global images_dn
	#---new list of substitutions
	route = {}
	#---copy the HTML brick
	template_reduced = {'video':'image'}
	new_brick = str(globals()['html_brick_%s'%template_reduced.get(template,template)])
	#---pathfinder
	path_raw = re.sub('^\+(\w+)\/(.+)',lambda x:maps['path'][x.group(1)]+x.group(2),spec['path'])
	path_rel = os.path.relpath(os.path.dirname(os.path.expanduser(path_raw)),os.path.expanduser(dropdir))
	path = os.path.join(path_rel,os.path.basename(path_raw))
	#---categories (default to 'none')
	categories = spec.get('categories',['none'])
	route['categories'] = ' '.join([i+'brick' for i in categories])
	#---description (default is blank)
	description = spec.get('description','')
	route['content'] = '<br><a href="%s"><strong>download high-resolution</strong></a><br>%s'%(
		path,'<br>'+description if description else '')
	#---title is provided via the 'name' key otherwise the name of the root dictionary in maps
	route['title'] = spec.get('name',name)
	#---videos get thumbnails and multiple formats
	if template == 'video':
		assocs = [os.path.abspath(i) for i in glob.glob(os.path.join(dropdir,path)+'*')]
		linked = [(ext,assoc) for assoc in assocs 
			for ext in movie_formats if re.match('^.+\.%s$'%ext,assoc)]	
		if linked == []: raise Exception('cannot find video! %s'%route['title'])
		#---name the video
		vidname = os.path.basename(path)
		#---make a snapshot from the first video
		if not os.path.isfile('%s/%s.jpg'%(images_dn,vidname)):
			proc = subprocess.Popen(
				'ffmpeg -ss 00:00:00 -i %s -frames:v 1 %s/%s.jpg'%(linked[0][1],images_dn,vidname),
				shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=dropdir_abs)
			proc.communicate()
		#---always point to the video file
		route['src'] = '%s/%s.jpg'%(os.path.relpath(images_dn,dropdir),vidname)
		#---videos override content to include multiple links
		route['content'] = description+'<br><strong>download:</strong> '
		for link in linked:
			this_path = os.path.join(os.path.dirname(path),os.path.basename(link[1]))
			route['content'] += '<a href="%s"><strong>+%s</strong></a> '%(
				this_path,link[0])
	#---! UNDER CONSTRUCTION NEEDS THUMBNAILER
	elif template == 'image':
		#---the src is a thumbnail while the "download high-resolution" above serves the full image
		route['src'] = os.path.relpath(thumbnailer(spec['path'],images_dn),dropdir)
		if 'content' in spec: route['content'] += spec['content']
	#---make substitutions in the HTML template
	for key,val in route.items(): new_brick = re.sub(key.upper(),val,new_brick)
	#---store results in the new_bricks list and the master categories
	new_bricks[template if template in new_bricks else 'all'] += [new_brick]
	master_categories.extend(categories)

def name_to_descriptor(fn):

	"""
	Extract useful information from a figure name.
	"""

	regex_version = '\.(v[0-9]+)\.[a-z]+$'
	regex_base = '^(?:fig\.)?(.+)\.?v?[0-9]*\.[a-z]+$'
	regex_floats = '\.([a-z]+\.[0-9]+\.[0-9]+)'
	descriptors = []
	if re.search(regex_version,fn): 
		version = re.findall(regex_version,fn)[0]
		descriptors.append(version)
		fn = re.sub('\.'+version,'',fn)
	#---get the base name
	base = re.findall(regex_base,fn)[0]
	#---get any floats
	if re.search(regex_floats,fn):
		floats = re.findall(regex_floats,base)
		descriptors.extend(floats)
		for f in floats: base = re.sub(re.escape('.'+f),'',base)
	descriptors.extend(base.split('.'))
	return '<br>'+'<br>'.join(descriptors)

###---MAIN

#---prepare directories
dropdir_abs = os.path.abspath(os.path.expanduser(dropdir))
if not os.path.isdir(dropdir_abs): os.mkdir(dropdir_abs)
tiler_dn = os.path.join(os.path.expanduser(dropdir),subdir)
if not os.path.isdir(tiler_dn): os.mkdir(tiler_dn)

#---if the tiler directory (holds supporting jquery files) is empty we must copy files there
if not glob.glob(tiler_dn+'/*'):
	#---tiler files are in the tiler subfolder but we may call tiler from elsewhere
	local_tiler = os.path.join(os.path.dirname(__file__),'tiler','')
	os.system('rsync -vari %s* %s/'%(local_tiler,tiler_dn))

#---prepare a folder for thumbnail images
images_dn = os.path.join(os.path.expanduser(dropdir),subdir_thumbs)
if not os.path.isdir(images_dn): os.mkdir(images_dn)

#---containers for adding bricks and tracking their categories
new_bricks,master_categories = dict([(i,[]) for i in category_list]),[]

#---identify bricks and determine their types
candidates = [(key,val) for key,val in maps.items() if key not in protected_keywords]
bricks = [(val.get('type','file'),key,val) 
	for key,val in candidates if key not in maps.get('deprecated',[])]
assert bricks or 'images' in maps['path'],'specify paths,images if you have no explicit bricks'
#---if there are no bricks and we have an images folder in paths then we simply tile all images there
if not bricks:
	images_from = maps['path']['images']
	#---collect all images and infer categories
	fn_break = '^(.+)\.([^\.]+)$'
	cwd = os.path.join(os.getcwd(),os.path.expanduser(images_from))
	for fn in glob.glob('%s/*'%cwd):
		base_fn = os.path.basename(fn)
		if re.match(fn_break,base_fn):
			name,suf = re.findall(fn_break,os.path.basename(fn))[0]
			if suf in ['png','gif','jpeg','jpg']:
				maps[name] = {'name':re.sub('_',' ',re.findall('^(?:fig\.)?([^\.]+)',name)[0]),
					'type':'image','path':os.path.relpath(fn,os.getcwd()),
					'categories':[re.findall('^(?:fig\.)?([^\.]+)\.',base_fn)[0]],
					'content':name_to_descriptor(base_fn)}
		else: print('[STATUS] skipping %s'%base_fn)
	#---after collecting all the images we add them to bricks previously empty
	candidates = [(key,val) for key,val in maps.items() if key not in protected_keywords]
	bricks = [(val.get('type','file'),key,val) 
		for key,val in candidates if key not in maps.get('deprecated',[])]
#---process the bricks
for template,name,item in bricks: make_brick(name,item,template=template)

###---RENDER

#---apply layout options to the html constants
for key,val in layout.items():
	for bnum,brick in enumerate(html_template):
		html_template[bnum] = re.sub(key.upper(),str(val),brick)

#---prepare the bricks
bricks = html_template[:1]
for category in list(set(master_categories)):
	bricks.append('<div class="filter-label" data-filter=".%sbrick">%s</div>'%
		(category,category))
bricks += html_template[1:2]
#---reorder the bricks to put drafts earlier
for key in ['drafts','videos','all']: bricks.extend(new_bricks[key])
bricks += html_template[-1:]

#---write the page
with open(os.path.join(os.path.expanduser(dropdir_abs),index_fn),'w') as fp:
	for brick in bricks: fp.write(re.sub('SUBDIR',subdir,brick))
