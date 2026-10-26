from pathlib import Path
import json,os,csv
os.environ.setdefault('MPLCONFIGDIR','E:/Codex/cache/matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results';ASSET=ROOT/'assets'
cases=['vertical_20N','spread_10N_each','opposed_500Nmm']
labels=['V / Vertical','S / Spread','M / Bending couple']
rows=[];conv=[]
for name in ['baseline','pocket_1p8']:
 a=json.loads((OUT/'fea'/(name+'_p2_3.0.json')).read_text())
 b=json.loads((OUT/'fea'/(name+'_p2_2.4.json')).read_text())
 for case in cases:
  conv.append({'variant':name,'case':case,'coarse_tets':a['tetrahedra'],'fine_tets':b['tetrahedra'],'compliance_change_percent':100*(b['cases'][case]['compliance_Nmm']/a['cases'][case]['compliance_Nmm']-1),'corner_displacement_change_percent':100*(b['cases'][case]['max_displacement_mm']/a['cases'][case]['max_displacement_mm']-1)})
base=json.loads((OUT/'fea'/'baseline_p2_2.4.json').read_text());new=json.loads((OUT/'fea'/'pocket_1p8_p2_2.4.json').read_text())
for case in cases:
 b=base['cases'][case];n=new['cases'][case]
 rows.append({'case':case,'baseline_corner_max_mm':b['max_displacement_mm'],'modified_corner_max_mm':n['max_displacement_mm'],'baseline_compliance_Nmm':b['compliance_Nmm'],'modified_compliance_Nmm':n['compliance_Nmm'],'compliance_increase_percent':100*(n['compliance_Nmm']/b['compliance_Nmm']-1),'equivalent_stiffness_change_percent':100*(b['compliance_Nmm']/n['compliance_Nmm']-1),'baseline_p95_vm_MPa':b['volume_weighted_p95_vm_MPa'],'modified_p95_vm_MPa':n['volume_weighted_p95_vm_MPa']})
cad=json.loads((OUT/'cad_metrics.json').read_text());verify=json.loads((OUT/'solver_verification.json').read_text())
summary={'selected':'pocket_1p8','scope':'component-level reference FE cases, isotropic linear elasticity, no prototype','cad':cad,'comparison':rows,'mesh_convergence':conv,'solver_verification':verify,'selection_pass':max(r['compliance_increase_percent'] for r in rows)<=10 and cad['pocket_1p8']['manufacturing_rule_pass'],'convergence_pass':max(abs(r['compliance_change_percent']) for r in conv)<5}
assert summary['selection_pass'] and summary['convergence_pass']
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
with (OUT/'comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fig,axes=plt.subplots(1,2,figsize=(12,4.3),layout='constrained')
x=np.arange(3)
axes[0].bar(x-.18,[r['baseline_corner_max_mm'] for r in rows],.36,label='Baseline',color='#74889b')
axes[0].bar(x+.18,[r['modified_corner_max_mm'] for r in rows],.36,label='Rev A',color='#147f88')
axes[0].set_xticks(x,labels);axes[0].set_ylabel('Corner-node max displacement / mm');axes[0].legend();axes[0].grid(axis='y',alpha=.2)
bars=axes[1].bar(x,[r['compliance_increase_percent'] for r in rows],color='#147f88')
axes[1].bar_label(bars,fmt='%.2f%%');axes[1].axhline(10,ls='--',color='#b24b42',label='Design screening limit 10%');axes[1].set_ylim(0,12);axes[1].set_xticks(x,labels);axes[1].set_ylabel('Compliance increase / %');axes[1].legend();axes[1].grid(axis='y',alpha=.2)
fig.suptitle('5.53% less solid volume / stiffness trade-off under identical reference loads',fontweight='bold');fig.savefig(ASSET/'fea_comparison.png',dpi=180);plt.close(fig)

data=[]
for name in ['baseline','pocket_1p8']:
 d=np.load(OUT/'fea'/(name+'_p2_2.4_opposed_500Nmm.npz'));data.append(d)
vmax=max(np.linalg.norm(d['displacement'],axis=1).max() for d in data);norm=Normalize(0,vmax)
fig=plt.figure(figsize=(12,5))
for k,d in enumerate(data):
 v=d['points'];tri=d['triangles'];u=np.linalg.norm(d['displacement'],axis=1);fc=plt.cm.viridis(norm(u[tri].mean(1)))
 ax=fig.add_subplot(1,2,k+1,projection='3d');ax.add_collection3d(Poly3DCollection(v[tri],facecolors=fc,edgecolors='none',rasterized=True));ax.set_xlim(-55,55);ax.set_ylim(-45,45);ax.set_zlim(-3,7);ax.set_box_aspect([110,90,10]);ax.view_init(-55,-55);ax.set_axis_off();ax.set_title(['Baseline','Rev A'][k])
cax=fig.add_axes([.3,.13,.4,.025]);fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap='viridis'),cax=cax,orientation='horizontal',label='Displacement magnitude / mm (undeformed geometry)')
fig.suptitle('Reference opposed bending couples / common color scale',fontweight='bold');fig.subplots_adjust(0,.18,1,.9);fig.savefig(ASSET/'displacement_field.png',dpi=180);plt.close(fig)

# Source geometry plus explicit supports and loaded ledges.
d=data[1];v=d['points'];tri=d['triangles'];fig=plt.figure(figsize=(10,5));ax=fig.add_subplot(projection='3d')
ax.add_collection3d(Poly3DCollection(v[tri],facecolors='#d4e0e8',edgecolors='none',alpha=.5,rasterized=True))
fixed=v[d['fixed_nodes']];ax.scatter(*fixed.T,s=5,c='#cf5447',label='Clamped hole walls')
for side in [-1,1]:
 for xx in [18.85,43.75]:
  x=side*xx;ax.plot([x,x],[-15,15],[.003,.003],lw=6,c='#147f88')
  ax.quiver(x,0,10,0,0,-8,color='#147f88',arrow_length_ratio=.25)
ax.set_xlim(-55,55);ax.set_ylim(-45,45);ax.set_zlim(-3,15);ax.set_box_aspect([110,90,30]);ax.view_init(65,-55);ax.set_axis_off();ax.legend(loc='lower left');ax.set_title('Boundary definition / load-bearing ledges in teal / ideal clamp in red')
fig.savefig(ASSET/'boundary_conditions.png',dpi=180,bbox_inches='tight');plt.close(fig)
print(json.dumps(summary,indent=2))
