"""Fresh PMX workflow for the pinned Morningstar/Festivity baseline. Run in background Blender."""
import bpy, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if len(args) != 1:
 raise SystemExit('Usage: blender -b --python-exit-code 1 --python build_character.py -- config.json')
config_path = Path(args[0]).resolve()
config = json.loads(config_path.read_text(encoding='utf-8-sig'))
def path(key):
 p = Path(config[key]).expanduser()
 return p.resolve() if p.is_absolute() else (config_path.parent/p).resolve()
for item in config['python_paths']:
 p = Path(item).expanduser()
 sys.path.insert(0, str(p if p.is_absolute() else (config_path.parent/p).resolve()))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from input_manifest import manifest
import mmd_tools
import festivity_genshin_addon as addon
pmx = str(path('pmx')); aux = str(path('aux')); face_type = config['face_type']
out = path('output')
if out.exists() and any(out.iterdir()):
 raise RuntimeError('Output directory must be empty; preserve previous scenes and audits')
out.mkdir(parents=True, exist_ok=True)
inputs = manifest(Path(aux))
inputs['pmx_package'] = manifest(Path(pmx).parent)
inputs['addon'] = manifest(Path(addon.__file__).parent)
inputs['mmd_tools'] = manifest(Path(mmd_tools.__file__).parent)
(out/'inputs.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2),encoding='utf8')
bpy.ops.wm.read_factory_settings(use_empty=True)
mmd_tools.register(); addon.register()
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'
bpy.ops.mmd_tools.import_model(filepath=pmx,scale=.08,types={'MESH','ARMATURE','MORPHS'})
arm=next(o for o in sc.objects if o.type=='ARMATURE')
meshes=[o for o in sc.objects if o.type=='MESH']
def stats():
 return {o.name:{'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'materials':[m.name if m else '' for m in o.data.materials]} for o in meshes}
audit={'source':pmx,'source_sha256':hashlib.sha256(Path(pmx).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'addon_version':addon.bl_info['version'],'before':stats(),'operators':[]}
def select():
 bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm
def run(op,**kwargs):
 select();result=getattr(bpy.ops.festivity,op)(**kwargs)
 audit['operators'].append({'operator':op,'result':sorted(result)})
 print('AUTHOR_STEP',op,result,flush=True)
 if result!={'FINISHED'}:raise RuntimeError('Author operator failed '+op)
select()
# Same sequence as the author's sidebar: import, convert, environment, assign,
# auxiliary maps, light vectors, native SDF, expression overlays, post, head, lines.
for obj in meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.mmd_tools.convert_materials(use_principled=True,clean_nodes=True,subsurface=.001)

uv_report = []
for obj in meshes:
 for index, material in enumerate(obj.data.materials):
  if not material or material.name not in config['face_materials']:
   continue
  loops = [i for p in obj.data.polygons if p.material_index == index for i in p.loop_indices]
  if not loops: continue
  layers = {}
  for layer in obj.data.uv_layers:
   coords = [layer.data[i].uv for i in loops]
   lo = [min(v[k] for v in coords) for k in range(2)]
   hi = [max(v[k] for v in coords) for k in range(2)]
   layers[layer.name] = {'min':lo, 'max':hi, 'nondegenerate':all(hi[k]-lo[k]>1e-6 for k in range(2))}
  uv_report.append({'object':obj.name,'material':material.name,'layers':layers})
if not uv_report: raise RuntimeError('No face polygons matched face_materials; inspect source PMX material names')
audit['face_uv'] = uv_report
skip_uv = config.get('skip_native_face_uv', False)
required_layers = ['UVMap'] if skip_uv else ['UVMap', 'UV1']
for record in uv_report:
 for layer in required_layers:
  if not record['layers'].get(layer,{}).get('nondegenerate',False):
   raise RuntimeError('Face UV preflight failed: '+record['material']+' / '+layer)
run('setup_genshin_environment')

sc.festivity_face_character_type=face_type
run('assign_genshin_materials')
sc.festivity_texture_directory=aux
run('assign_auxiliary_textures')
run('setup_light_vectors')
if not config.get('skip_native_face_uv',False):run('native_face_uv')
if config.get('explicit_shadow_ramps', True):
 # Author's matcher also recognises Packed_Ramp as a candidate. This shader's
 # existing ramp sampler expects the 20-row Shadow_Ramp, not the packed data.
 for mat in addon.characters.materials():
  if not mat.use_nodes:continue
  lm=mat.node_tree.nodes.get('Body_Lightmap_UV0')
  if not lm or not lm.image:continue
  ramp_path=Path(aux)/(Path(lm.image.filepath).name.replace('_Lightmap','_Shadow_Ramp'))
  ramp_node=mat.node_tree.nodes.get('Shadow Ramp')
  if not (ramp_path.exists() and ramp_node and ramp_node.node_tree):
   raise RuntimeError('Missing matching Shadow Ramp for '+mat.name+' / '+str(ramp_path))
  if ramp_path.exists() and ramp_node and ramp_node.node_tree:
   image=bpy.data.images.load(str(ramp_path),check_existing=True)
   if tuple(image.size) != (256,20):raise RuntimeError('Expected 256x20 Shadow_Ramp: '+str(ramp_path))
   image.colorspace_settings.name='sRGB';image.alpha_mode='CHANNEL_PACKED'
   ramp_node.node_tree = ramp_node.node_tree.copy()
   for node in ramp_node.node_tree.nodes:
    if node.type=='TEX_IMAGE':node.image=image
   audit.setdefault('explicit_ramps',[]).append({'material':mat.name,'image':str(ramp_path)})
if config.get('skip_native_face_uv',False):
 audit['face_uv_decision']='Native UV mixer skipped by measured configuration; retain valid UVMap.'
else:sc.festivity_face_uv_split=config.get('uv_split',sc.festivity_face_uv_split)
run('expression_layers',restore=False)
run('import_post_processing')
run('attach_head_origin')
run('setup_outlines')
sc.festivity_outline_thickness=config.get('author_outline_thickness', .15)
if config.get('outline', 'mmd') == 'mmd':
 disabled = []
 for mesh in meshes:
  for mod in mesh.modifiers:
   if mod.type=='NODES' and mod.node_group and addon.characters.source(mod.node_group)=='HoYoverse - Genshin Impact Outlines':
    mod.show_viewport=False;mod.show_render=False;disabled.append(mesh.name+'/'+mod.name)
  for m in mesh.data.materials:
   if not m or m.name.startswith('Outline '):continue
   m.mmd_material.enabled_toon_edge=not bool(m.get('morningstar_eye_mode'))
   m.mmd_material.edge_color=tuple(config.get('edge_color',[.12,.08,.13,1]))
   m.mmd_material.edge_weight=config.get('edge_weight', .45)
 select()
 if bpy.ops.mmd_tools.edge_preview_setup(action='CREATE') != {'FINISHED'}:
  raise RuntimeError('Native MMD outline failed')
 mods = [m for mesh in meshes for m in mesh.modifiers if m.name=='mmd_edge_preview']
 if not mods: raise RuntimeError('Native MMD outline modifier missing')
 audit['native_outline']={'disabled_author_modifiers':disabled,'vertex_groups':[m.vertex_group for m in mods]}
elif config['outline'] != 'author':
 raise ValueError('outline must be mmd or author')

audit['after']=stats()
audit['engine']=sc.render.engine
audit['mmd_tools_version']=str(getattr(mmd_tools,'bl_info',{}).get('version','unknown'))
audit['config']=config
def material_record(m):
 return {'name':m.name,'eye_mode':m.get('morningstar_eye_mode'),'render_method':getattr(m,'surface_render_method',None),'textures':{n.name:n.image.filepath if n.image else None for n in m.node_tree.nodes if n.type=='TEX_IMAGE'}}
audit['materials']=[material_record(m) for m in addon.characters.materials() if m.use_nodes]
audit['face_uv_split']=sc.festivity_face_uv_split
audit['face_type']=sc.festivity_face_character_type
audit['compositing']=sc.render.use_compositing
(out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
coords=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=Vector(tuple(min(p[i] for p in coords) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in coords) for i in range(3)))
center=(lo+hi)*.5
head=arm.matrix_world@arm.pose.bones['頭'].matrix.translation
camdata=bpy.data.cameras.new('Review Camera');cam=bpy.data.objects.new('Review Camera',camdata);sc.collection.objects.link(cam);sc.camera=cam
sc.render.resolution_percentage=config.get('resolution_scale',100)
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.render.film_transparent=False
if hasattr(sc,'eevee'):sc.eevee.taa_render_samples=config.get('samples',48)
light=addon.characters.helper('Light Direction')
audit['default_light_rotation']=list(light.rotation_euler)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'review.blend'))
for angle,label in [(0,'front'),(55,'side'),(280,'opposite')]:
 if angle not in config.get('light_angles',[0,55,280]):continue
 light.rotation_euler=(-math.pi/2,0,math.radians(angle))
 bpy.context.view_layer.update()
 for shot in ['fullbody','face']:
  if shot=='fullbody':
   sc.render.resolution_x=900;sc.render.resolution_y=1400
   camdata.type='ORTHO';camdata.ortho_scale=max((hi.z-lo.z)*1.12,(hi.x-lo.x)*1400/900*1.12)
   target=center;cam.location=target+Vector((0,-6,0))
  else:
   sc.render.resolution_x=1000;sc.render.resolution_y=1000
   camdata.type='ORTHO';camdata.ortho_scale=config.get('face_frame_height',.58)
   target=head+Vector((0,0,.015));cam.location=target+Vector((0,-3,0))
  cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
  sc.render.filepath=str(out/(shot+'_'+label+'.png'))
  bpy.ops.render.render(write_still=True)
audit['bounds']={'min':list(lo),'max':list(hi)}
(out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
light.rotation_euler=(-math.pi/2,0,0)
sc.render.resolution_x=900;sc.render.resolution_y=1400
camdata.type='ORTHO';camdata.ortho_scale=max((hi.z-lo.z)*1.12,(hi.x-lo.x)*1400/900*1.12)
cam.location=center+Vector((0,-6,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=str(out/'fullbody_front.png')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'review.blend'))
