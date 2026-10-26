"""CAD-derived figures and review drawings for the engineering extension."""
from pathlib import Path
import os,json
os.environ.setdefault('MPLCONFIGDIR','E:/Codex/cache/matplotlib')
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from engineering_geometry import data,pose

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','figure.facecolor':'white'})


def draw(ax,s,color):
    v,t=s.tessellate(.18);v=np.array([p.toTuple() for p in v]);t=np.array(t);tri=v[t]
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
    light=np.array([.3,-.5,.8]);shade=.35+.65*np.abs(n@light)
    colors=np.clip(shade[:,None]*np.array(color)[None,:],0,1)
    ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,edgecolors='none',rasterized=True))


def main():
    parts=list(data(use_finished=True));parts[2]=cq.importers.importStep(str(ROOT/'cad/engineering/bracket_revB.step')).val()
    plate=cq.importers.importStep(str(ROOT/'cad/engineering/top_plate_revB.step')).val()
    fig=plt.figure(figsize=(14,5))
    for i,(a,b) in enumerate([(15,15),(55,35),(55,90)]):
        ax=fig.add_subplot(1,3,i+1,projection='3d')
        for name,s in (pose(a,b,parts)|{'plate':plate}).items():
            color=([.20,.60,.65] if 'proximal' in name else [.85,.57,.23] if 'distal' in name
                   else [.58,.66,.72] if 'mount' in name else [.25,.34,.43])
            draw(ax,s,color)
        ax.set(xlim=(-140,140),ylim=(-55,55),zlim=(-10,115))
        ax.set_box_aspect([280,110,125]);ax.view_init(22,-64);ax.set_axis_off()
        ax.set_title(f'q1 = {a} deg / q2 = {b} deg',fontsize=12)
    fig.text(.5,.06,'Revision B upper subassembly | actual STEP surfaces | actuator, springs, tendon and cast pads omitted',ha='center',color='#526274')
    fig.subplots_adjust(0,.09,1,.95,wspace=0);fig.savefig(OUT/'engineering_assembly.png',dpi=180);plt.close(fig)

    fig,ax=plt.subplots(figsize=(11,8))
    for e in plate.Edges():
        pts=np.array([p.toTuple() for p in e.sample(30)[0]])
        if pts[:,2].max()<-1.19:ax.plot(pts[:,0],pts[:,1],color='#9aaab5',lw=.7)
    for x in [-7,7]:
        for y in [-16,16]:
            ax.add_patch(FancyBboxPatch((x-5,y-12),10,24,boxstyle='round,pad=0,rounding_size=2',facecolor='#c9e9eb',edgecolor='#147c86',lw=1.5))
    ax.axhline(0,color='#7990a4',ls='-.',lw=.7);ax.axvline(0,color='#7990a4',ls='-.',lw=.7)
    for a,b,text,xy in [((-7,32),(7,32),'14',(0,34)),((16,-16),(16,16),'32',(19,0)),
                        ((-12,-32),(-2,-32),'10',(-7,-34)),((-17,4),(-17,28),'24',(-21,16))]:
        ax.annotate('',xy=a,xytext=b,arrowprops={'arrowstyle':'<->','lw':.8});ax.text(*xy,text,ha='center',va='center',bbox={'fc':'white','ec':'none','pad':1})
    ax.annotate('R2 all corners',xy=(10.6,27.6),xytext=(27,29),arrowprops={'arrowstyle':'->'})
    ax.set(xlim=(-60,60),ylim=(-48,48));ax.set_aspect('equal');ax.set_axis_off()
    fig.text(.08,.96,'TOP PLATE / REV B / MODIFICATION DRAWING',fontsize=17,fontweight='bold')
    fig.text(.08,.925,'Underside | mm | 4 pockets 10 x 24 | depth 1.65 (+0/-0.15)',fontsize=11)
    fig.text(.08,.09,'Centers (+/-7, +/-16). Original floor 3.00 +/-0.15. Worst-case remaining floor >=1.20.',fontsize=10)
    fig.text(.08,.062,'Other pocket dimensions +/-0.15. Original interfaces unchanged. Inspect actual floor at each pocket.',fontsize=10)
    fig.text(.08,.034,'Design review drawing. Final process capability and material properties require physical verification.',fontsize=9,color='#526274')
    fig.subplots_adjust(top=.88,bottom=.13)
    fig.savefig(OUT/'revB_modification_drawing.png',dpi=180);fig.savefig(OUT/'revB_modification_drawing.svg');plt.close(fig)

    fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    ax=axs[0]
    ax.barh(['Rev A: depth 1.80','Rev B: depth 1.65'],[.45,.45],left=[1.05,1.20],color=['#d69373','#147f88'],height=.45)
    ax.axvline(1.2,color='#233b50',ls='--',label='Required minimum 1.20')
    ax.set(xlim=(.95,1.8),xlabel='Remaining floor range / mm',title='Worst-case dimensional chain');ax.legend(fontsize=9)
    ax=axs[1];coupon=json.loads((ROOT/'results/engineering/cad_revB.json').read_text())['coupon']
    ax.plot([-35,35,35,-35,-35],[-18,-18,18,18,-18],color='#233b50')
    for row in coupon['holes']:
        x,y,d=row['x_mm'],row['y_mm'],row['CAD_diameter_mm']
        ax.add_patch(plt.Circle((x,y),d/2,facecolor='#c9e9eb',edgecolor='#147f88'))
        ax.text(x,y-5,f'{d:.2f}',ha='center',va='top',fontsize=9)
    ax.plot([-35,-32.5,-32.5,-35],[15.5,15.5,18,18],color='#c26d48',lw=2)
    ax.set(xlim=(-40,40),ylim=(-23,23),title='70 x 36 x 8 pin-fit coupon (CAD diameters)');ax.set_aspect('equal');ax.axis('off')
    fig.savefig(OUT/'engineering_tolerances.png',dpi=180);plt.close(fig)

    # Dimensioned inspection sheet for the finished bracket and joint bores.
    fig,axs=plt.subplots(1,2,figsize=(11,7))
    for i,n in enumerate(['bracket_revB','finger_A_finished']):
        s=cq.importers.importStep(str(ROOT/f'cad/engineering/{n}.step')).val();ax=axs[i]
        for edge in s.Edges():
            p=np.array([v.toTuple() for v in edge.sample(20)[0]])
            if i==0:ax.plot(p[:,0],p[:,2],color='#526274',lw=.65)
            else:ax.plot(p[:,0],p[:,1],color='#526274',lw=.65)
        ax.set_aspect('equal');ax.axis('off');ax.set_title('FINISHED BRACKET' if i==0 else 'FINISHED PROXIMAL LINK')
    fig.text(.07,.96,'JOINT & BRACKET / REV B / INSPECTION REQUIREMENTS',fontsize=15,fontweight='bold')
    fig.text(.07,.17,'Bracket width: 31.60 +/-0.05. Mating slot acceptance: 31.90 +/-0.05. Total gap: 0.20-0.40.',fontsize=10)
    fig.text(.07,.125,'Retained holes: diameter 6.325-6.340. Rotating holes: diameter 6.375-6.400. Pins: 6.344-6.350.',fontsize=10)
    fig.text(.07,.08,'C1 both 1/4 in holes: retained. Proximal link: base rotating, distal retained. Distal link: rotating.',fontsize=10)
    fig.text(.07,.035,'mm | Post-processing target CAD; calibrate pilot bores with coupon. Other geometry governed by STEP.',fontsize=9,color='#526274')
    fig.subplots_adjust(top=.85,bottom=.23)
    fig.savefig(OUT/'joint_inspection_drawing.png',dpi=180);fig.savefig(OUT/'joint_inspection_drawing.svg');plt.close(fig)
    print('Engineering figures complete')


if __name__=='__main__':main()
