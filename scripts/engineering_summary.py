"""Consolidate the checked revision B outputs, figures and raw-data archive."""
from pathlib import Path
import json,math,hashlib,zipfile,os
os.environ.setdefault('MPLCONFIGDIR','E:/Codex/cache/matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/engineering';FE=OUT/'fea'
def read(path):return json.loads(path.read_text())
files=['baseline_h3.0_fixed','baseline_h2.4_fixed','revB_h3.0_fixed','revB_h2.4_fixed','revB_h2.4_k100','revB_h2.4_k10']
records={n:read(FE/(n+'.json')) for n in files}
base=records['baseline_h2.4_fixed'];new=records['revB_h2.4_fixed']
mesh=[]
for name in ['baseline','revB']:
    coarse=records[name+'_h3.0_fixed'];fine=records[name+'_h2.4_fixed']
    mesh.append(dict(variant=name,coarse_elements=coarse['elements'],fine_elements=fine['elements'],
                     compliance_change_percent=100*(fine['compliance_Nmm']/coarse['compliance_Nmm']-1),
                     global_element_stress_change_percent=100*(fine['max_element_vm_MPa']/coarse['max_element_vm_MPa']-1),
                     central_element_stress_change_percent=100*(fine['central_region_max_element_vm_MPa']/coarse['central_region_max_element_vm_MPa']-1)))
soft=[]
for n in ['revB_h2.4_fixed','revB_h2.4_k100','revB_h2.4_k10']:
    r=records[n];soft.append(dict(support=r['support'],k=r['support_k_N_per_mm3'],
                                 displacement_mm=r['all_nodal_max_displacement_mm'],compliance_Nmm=r['compliance_Nmm'],
                                 compliance_increase_vs_fixed_percent=100*(r['compliance_Nmm']/new['compliance_Nmm']-1)))
change=100*(new['compliance_Nmm']/base['compliance_Nmm']-1)
maxmesh=math.ceil(max(abs(r['compliance_change_percent']) for r in mesh)*100)/100
assert maxmesh<1.0 and change<10
summary=dict(revision='B',cad=read(OUT/'cad_revB.json'),mechanism=read(OUT/'mechanism.json'),
             assembly= {k:v for k,v in read(OUT/'closure_sweep.json').items() if k!='poses'},
             comparison=dict(volume_reduction_percent=read(OUT/'cad_revB.json')['volume_reduction_percent'],
                             compliance_increase_percent=change,
                             equivalent_stiffness_change_percent=100*(base['compliance_Nmm']/new['compliance_Nmm']-1),
                             baseline_displacement_mm=base['all_nodal_max_displacement_mm'],
                             revised_displacement_mm=new['all_nodal_max_displacement_mm'],
                             mesh_change_upper_bound_percent=maxmesh),
             mesh_convergence=mesh,support_sensitivity=soft,
             fixed_boundary_E_sensitivity=[dict(E_MPa=e,displacement_mm=new['all_nodal_max_displacement_mm']*1650/e) for e in [1000,1500,1650,2000,2200]],
             strength_status='Element stress maxima are mesh sensitive; no peak-stress or strength certification',
             fe_cases=records)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,axs=plt.subplots(1,3,figsize=(13,4),layout='constrained')
axs[0].bar(['Baseline','Rev B'],[base['all_nodal_max_displacement_mm'],new['all_nodal_max_displacement_mm']],color=['#7e92a1','#147f88'])
axs[0].set(ylabel='P2 nodal max displacement / mm',title='Derived equivalent load, 1.5 x')
axs[1].bar(['Baseline','Rev B'],[base['compliance_Nmm'],new['compliance_Nmm']],color=['#7e92a1','#147f88'])
axs[1].set(ylabel='Compliance / N mm',title=f'Volume -5.07% / compliance +{change:.2f}%')
axs[2].bar(['Fixed','k=100','k=10'],[r['displacement_mm'] for r in soft],color=['#147f88','#659da5','#d69373'])
axs[2].set(ylabel='P2 nodal max displacement / mm',title='Support sensitivity; k in N/mm3')
for ax in axs:ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.savefig(ROOT/'assets/engineering_fea.png',dpi=180);plt.close(fig)

fig=plt.figure(figsize=(12,4.5));norm=plt.Normalize(0,new['all_nodal_max_displacement_mm'])
for i,n in enumerate(['baseline_h2.4_fixed','revB_h2.4_fixed']):
    d=np.load(FE/(n+'.npz'));p=d['points'];t=d['triangles'];u=np.linalg.norm(d['displacement'],axis=1)
    ax=fig.add_subplot(1,2,i+1,projection='3d');colors=plt.cm.viridis(norm(u[t].mean(1)))
    ax.add_collection3d(Poly3DCollection(p[t],facecolors=colors,edgecolors='none',rasterized=True))
    ax.set(xlim=(-56,56),ylim=(-46,46),zlim=(-4,8));ax.set_box_aspect([112,92,12]);ax.view_init(-50,-55);ax.axis('off')
    ax.set_title('BASELINE' if i==0 else 'REV B')
cax=fig.add_axes([.92,.2,.015,.55]);fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap='viridis'),cax=cax,label='Corner-sampled displacement / mm')
fig.text(.45,.04,'Original undeformed surfaces; same color scale; equivalent top-plate traction scenario',ha='center',fontsize=9)
fig.subplots_adjust(0,.09,.9,.95,wspace=0)
fig.savefig(ROOT/'assets/engineering_displacement.png',dpi=180);plt.close(fig)

hashes={}
with zipfile.ZipFile(FE/'raw-revB.zip','w',compression=zipfile.ZIP_STORED) as z:
    for n in files:
        p=FE/(n+'.npz');z.write(p,p.name);hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(FE/'raw_checksums.json').write_text(json.dumps(hashes,indent=2))
(FE/'README.md').write_text('''# Revision B raw finite-element results

`raw-revB.zip` contains the six compressed NumPy arrays referenced by the JSON records.
SHA-256 hashes are in `raw_checksums.json`. Units: mm, N, MPa.

- `points`, `tets`, `triangles`: linear geometric mesh and boundary facets.
- `displacement`: displacement at original mesh vertices only. JSON additionally reports the maximum over all quadratic element displacement nodes, including edge midpoints; it is still a sampled maximum.
- `element_vm`, `element_principal`: element-integrated averages, not converged local stress peaks.
- `central_region`: element-center region |X|<13, |Y|<29 used for the local diagnostic.

The applied resultant includes a factor 1.5. E=1650 MPa, nu=0.35; forces are distributed on the four reference seats. This is not a solved full assembly contact model. Foundation stiffness values 100 and 10 N/mm3 are sensitivity assumptions, not measured joint stiffnesses.
''',encoding='utf-8')
print(json.dumps(summary['comparison'],indent=2))
