from pathlib import Path
import json, shutil, sys
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'design.json').read_text())
sha=json.loads((ROOT/'source_manifest.json').read_text())['commit']
SRC=Path('E:/Codex/downloads/openhand-hardware')/sha
OUT=ROOT/'cad';(OUT/'upstream').mkdir(parents=True,exist_ok=True)
baseline_path=OUT/'upstream'/C['upstream_part']
if not baseline_path.exists():shutil.copy2(SRC/'model t42'/'step'/C['upstream_part'],baseline_path)
for filename in ['c1_t42.STEP','finger_pp_ext_A_t42.STEP','finger_pp_B_t42.STEP']:
 if not (OUT/'upstream'/filename).exists():shutil.copy2(SRC/'model t42'/'step'/filename,OUT/'upstream'/filename)
if (SRC/'LICENSE.md').exists():shutil.copy2(SRC/'LICENSE.md',ROOT/'UPSTREAM_LICENSE.md')
base=cq.importers.importStep(str(baseline_path))
metrics={}
def save(name,wp,depth):
 s=wp.val(); assert s.isValid() and len(s.Solids())==1
 directory=OUT/'variants';directory.mkdir(exist_ok=True)
 cq.exporters.export(wp,str(directory/(name+'.step')))
 cq.exporters.export(wp,str(directory/(name+'.stl')),tolerance=.08,angularTolerance=.1)
 # Independent import check verifies delivered STEP, not only in-memory solid.
 delivered=cq.importers.importStep(str(directory/(name+'.step'))).val()
 assert delivered.isValid() and abs(delivered.Volume()-s.Volume())<.001
 removed=base.val().cut(s);added=s.cut(base.val())
 added_volume=abs(added.Volume()) if added.Solids() else 0.
 # Outside the central pocket region all original geometry must be identical.
 keepout=cq.Workplane('XY',origin=(0,0,-5)).box(26,58,20,centered=(True,True,False)).val()
 outside_removed=removed.cut(keepout) if removed.Solids() else removed
 outside_volume=abs(outside_removed.Volume()) if outside_removed.Solids() else 0.
 assert added_volume<.001 and outside_volume<.001
 metrics[name]={'volume_mm3':s.Volume(),'estimated_mass_g':s.Volume()*C['material_assumption']['density_g_cm3']/1000,'volume_reduction_percent':100*(1-s.Volume()/base.val().Volume()),'pocket_depth_mm':depth,'remaining_floor_mm':3-depth,'valid_single_solid':True,'step_roundtrip_volume_error_mm3':abs(delivered.Volume()-s.Volume()),'added_material_mm3':added_volume,'removed_outside_design_region_mm3':outside_volume,'manufacturing_rule_pass':3-depth>=C['minimum_floor_design_rule_mm']-1e-8}
save('baseline',base,0)
for depth in C['candidate_depths_mm']:
 modified=base
 for x,y in C['pocket_centers_mm']:
  cutter=cq.Workplane('XY',origin=(x,y,C['bottom_z_mm']-.1)).sketch().rect(C['pocket_width_mm'],C['pocket_length_mm']).vertices().fillet(C['pocket_corner_radius_mm']).finalize().extrude(depth+.1)
  modified=modified.cut(cutter)
 save('pocket_'+str(depth).replace('.','p'),modified,depth)
(ROOT/'results').mkdir(exist_ok=True)
(ROOT/'results'/'cad_metrics.json').write_text(json.dumps(metrics,indent=2))
print(json.dumps(metrics,indent=2))
