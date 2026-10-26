"""Finite pose sampling of the reconstructed upper mechanism; B-rep booleans."""
from pathlib import Path
import json
import numpy as np
import cadquery as cq
from engineering_geometry import data,pose,overlap

ROOT=Path(__file__).resolve().parents[1]
parts=list(data(use_finished=True));parts[2]=cq.importers.importStep(str(ROOT/'cad/engineering/bracket_revB.step')).val()
plate=cq.importers.importStep(str(ROOT/'cad/engineering/top_plate_revB.step')).val()
angles=[(float(a),float(15+(a-15)/2)) for a in np.linspace(15,55,17)]
angles += [(55.,float(b)) for b in np.linspace(35,90,23)[1:]]
pairs=[('proximal_R','distal_R'),('proximal_R','mount_R'),('proximal_R','plate'),
       ('distal_R','plate'),('distal_R','mount_R'),('proximal_R','proximal_L'),
       ('distal_R','distal_L'),('distal_R','proximal_L'),('proximal_R','distal_L')]
rows=[]
for i,(q1,q2) in enumerate(angles):
    shapes=pose(q1,q2,parts)|{'plate':plate}
    checks=[dict(parts=[a,b],intersection_mm3=overlap(shapes[a],shapes[b])) for a,b in pairs]
    rows.append(dict(q1_deg=q1,q2_deg=q2,checks=checks,clear=all(c['intersection_mm3']<1e-4 for c in checks)))
    if i%5==0:print(f'{i+1}/{len(angles)} checked',flush=True)
max_intersection=max(c['intersection_mm3'] for row in rows for c in row['checks'])
assert all(row['clear'] for row in rows),[(r['q1_deg'],r['q2_deg']) for r in rows if not r['clear']]
out=dict(pose_count=len(rows),pairs_per_pose=len(pairs),total_pair_checks=len(rows)*len(pairs),
         maximum_intersection_mm3=max_intersection,all_sampled_poses_clear=True,poses=rows,
         excluded=['actuator block','tendons','springs','cast pads','fastener heads','manufacturing errors','continuous unsampled motion'],
         description='Revision B nominal finished rigid bodies, plate and narrowed brackets; symmetric path; sampled collision screen only')
(ROOT/'results/engineering/closure_sweep.json').write_text(json.dumps(out,indent=2))
for a,b in [(15,15),(55,35),(55,90)]:
    assembly=cq.Assembly(name='revision_B_upper_mechanism')
    for name,shape in (pose(a,b,parts)|{'plate':plate}).items():assembly.add(shape,name=name)
    assembly.save(str(ROOT/f'cad/engineering/revB_upper_q{a}_{b}.step'))
print(json.dumps({k:v for k,v in out.items() if k!='poses'},indent=2))
