from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','E:/Codex/cache/matplotlib')
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import FancyBboxPatch,Rectangle
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f7fafc'})

def mesh_part(path):
 s=cq.importers.importStep(str(path)).val();v,t=s.tessellate(.12)
 return np.array([p.toTuple() for p in v]),np.array(t)
def view(ax,v,t,colors=None,underside=False):
 tri=v[t]
 if colors is None:
  n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
  light=np.array([.3,-.5,-.8 if underside else .8]);intensity=.35+.65*np.abs(n@light)
  colors=np.clip(intensity[:,None]*np.array([.18,.62,.67])[None,:],0,1)
 ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,edgecolors='none',rasterized=True))
 lo=v.min(0);hi=v.max(0);margin=(hi-lo)*.07
 ax.set_xlim(lo[0]-margin[0],hi[0]+margin[0]);ax.set_ylim(lo[1]-margin[1],hi[1]+margin[1]);ax.set_zlim(lo[2]-1,hi[2]+1)
 ax.set_box_aspect([hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2]+2]);ax.view_init(-55 if underside else 55,-55);ax.set_axis_off()

fig=plt.figure(figsize=(12,5))
for k,name in enumerate(['baseline','pocket_1p8']):
 v,t=mesh_part(ROOT/'cad'/'variants'/(name+'.step'));ax=fig.add_subplot(1,2,k+1,projection='3d');view(ax,v,t,underside=True)
 ax.set_title('UPSTREAM BASELINE' if k==0 else 'REV A / FOUR POCKETS',fontweight='bold',pad=-5)
fig.text(.5,.07,'Actual STEP geometry / underside view / interfaces outside the central region preserved',ha='center',color='#526274')
fig.subplots_adjust(0,0.08,1,.93,wspace=0);fig.savefig(OUT/'design_comparison.png',dpi=190);plt.close(fig)

# Modification drawing: unchanged features are governed by the supplied upstream STEP.
fig,ax=plt.subplots(figsize=(11,8));fig.patch.set_facecolor('white')
shape=cq.importers.importStep(str(ROOT/'cad'/'variants'/'pocket_1p8.step'))
cq.exporters.export(shape,str(OUT/'top_plate_isometric.svg'),exportType='SVG',opt={'width':900,'height':650,'showAxes':False,'projectionDir':(1,-1,-2),'showHidden':False})
v,t=mesh_part(ROOT/'cad'/'variants'/'baseline.step')
# Plot projected true boundary edges, sampled from CAD.
for e in shape.val().Edges():
 pts=np.array([p.toTuple() for p in e.sample(30)[0]])
 if np.max(pts[:,2])<-1.19:ax.plot(pts[:,0],pts[:,1],color='#a7b1ba',lw=.7)
for x in [-7,7]:
 for y in [-16,16]:
  ax.add_patch(FancyBboxPatch((x-5,y-12),10,24,boxstyle='round,pad=0,rounding_size=2',facecolor='#c9e9eb',edgecolor='#147c86',lw=1.5))
  ax.plot([x-2,x+2],[y,y],color='#147c86',lw=.6);ax.plot([x,x],[y-2,y+2],color='#147c86',lw=.6)
ax.axhline(0,color='#7990a4',lw=.7,ls='-.');ax.axvline(0,color='#7990a4',lw=.7,ls='-.')
def dimension(a,b,text,offset=(0,0)):
 ax.annotate('',xy=a,xytext=b,arrowprops={'arrowstyle':'<->','lw':.8,'color':'#233b50'})
 midpoint=(np.array(a)+np.array(b))/2+offset;ax.text(*midpoint,text,ha='center',va='center',fontsize=10,bbox={'fc':'white','ec':'none','pad':1})
dimension((-7,32),(7,32),'14',offset=(0,2))
dimension((16,-16),(16,16),'32',offset=(2,0))
dimension((-12,-32),(-2,-32),'10',offset=(0,-2))
dimension((-17,4),(-17,28),'24',offset=(-3,0))
ax.annotate('All pocket corners R2',xy=(10.6,27.6),xytext=(27,29),arrowprops={'arrowstyle':'->'},fontsize=9)
ax.set_xlim(-60,60);ax.set_ylim(-48,48);ax.set_aspect('equal');ax.set_axis_off()
fig.text(.08,.96,'T42 TOP PLATE / REV A MODIFICATION DRAWING',fontsize=17,fontweight='bold')
fig.text(.08,.925,'Underside view | mm | 4 pockets 10 x 24, R2, depth 1.8 | floor remaining 1.2',fontsize=11)
fig.text(.08,.09,'Pocket centers: (X,Y) = (+/-7, +/-16). Origin: original STEP X/Y center.',fontsize=10)
fig.text(.08,.062,'Depth 1.8 (+0/-0.15); inspect floor >= 1.2. Other pocket dimensions +/-0.15 mm (proposed).',fontsize=10)
fig.text(.08,.034,'Unchanged geometry: supplied baseline STEP. Design review only; process and material need physical validation.',fontsize=9,color='#526274')
fig.subplots_adjust(top=.88,bottom=.13);fig.savefig(OUT/'modification_drawing.png',dpi=210);fig.savefig(OUT/'modification_drawing.svg');plt.close(fig)
print(str(OUT))
