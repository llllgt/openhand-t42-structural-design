from pathlib import Path
import json, os
os.environ.setdefault('MPLCONFIGDIR','E:/Codex/cache/matplotlib')
import cadquery as cq
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=Path(__file__).resolve().parents[1]
sha=json.loads((ROOT/'source_manifest.json').read_text())['commit']
SRC=Path('E:/Codex/downloads/openhand-hardware')/sha/'model t42'/'step'
OUT=ROOT/'results'/'inspection'; OUT.mkdir(parents=True,exist_ok=True)
names=['a1_p_t42','c1_t42','finger_pp_ext_A_t42','finger_pp_B_t42','a4_blank_t42','a4_coupling_t42']
fig=plt.figure(figsize=(16,10))
stats={}
for k,name in enumerate(names):
 s=cq.importers.importStep(str(SRC/(name+'.STEP'))).val()
 bb=s.BoundingBox(); vertices,faces=s.tessellate(.12)
 v=np.array([x.toTuple() for x in vertices]); f=np.array(faces)
 ax=fig.add_subplot(2,3,k+1,projection='3d'); ax.add_collection3d(Poly3DCollection(v[f],facecolor='#69bac0',edgecolor='#223d4c',linewidth=.12,alpha=1))
 center=(v.max(0)+v.min(0))/2; r=max(v.max(0)-v.min(0))*.57
 ax.set_xlim(center[0]-r,center[0]+r);ax.set_ylim(center[1]-r,center[1]+r);ax.set_zlim(center[2]-r,center[2]+r);ax.set_box_aspect([1,1,1]);ax.view_init(25,-50)
 ax.set_title(name);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm')
 fs=[]
 for i,face in enumerate(s.Faces()):
  entry={'id':i,'type':face.geomType(),'area':face.Area(),'center':face.Center().toTuple()}
  if face.geomType()=='PLANE':entry['normal']=face.normalAt().toTuple()
  if face.geomType()=='CYLINDER':
   from OCP.BRepAdaptor import BRepAdaptor_Surface
   cy=BRepAdaptor_Surface(face.wrapped).Cylinder();entry.update(radius=cy.Radius(),axis=tuple(cy.Axis().Direction().Coord()))
  fs.append(entry)
 stats[name]={'valid':s.isValid(),'solids':len(s.Solids()),'volume':s.Volume(),'bounds':{'min':[bb.xmin,bb.ymin,bb.zmin],'max':[bb.xmax,bb.ymax,bb.zmax]},'faces':fs}
fig.tight_layout();fig.savefig(OUT/'upstream_parts.png',dpi=140);plt.close(fig)
(OUT/'geometry.json').write_text(json.dumps(stats,indent=2))
print(json.dumps({k:{a:b for a,b in v.items() if a!='faces'} for k,v in stats.items()},indent=2))
