"""Revision B equivalent-resultant FE + ideal clamp / elastic support sensitivity.

Actual upper mechanism load sharing requires assembly contact; this study puts
100% of the derived wrench into the top plate as a defined interface scenario.
"""
from pathlib import Path
import json, argparse, time
import numpy as np
from scipy.sparse.linalg import splu
from skfem import Basis, FacetBasis, ElementVector, ElementTetP2, LinearForm, BilinearForm, asm
from skfem.models.elasticity import linear_elasticity, lame_parameters
from analyze import make_mesh

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/engineering/fea';OUT.mkdir(exist_ok=True,parents=True)
C=json.loads((ROOT/'engineering.json').read_text());M=json.loads((ROOT/'results/engineering/mechanism.json').read_text())


def solve(name,h,elastic_support=None):
    started=time.time()
    step=ROOT/('cad/variants/baseline.step' if name=='baseline' else 'cad/engineering/top_plate_revB.step')
    mesh=make_mesh(step,h);el=ElementVector(ElementTetP2());basis=Basis(mesh,el)
    lam,mu=lame_parameters(C['material_fe']['E_MPa'],C['material_fe']['nu_assumption'])
    K=asm(linear_elasticity(lam,mu),basis).tocsc();p=mesh.p.T
    bf=mesh.boundary_facets();tri=p[mesh.facets[:,bf].T];cent=tri.mean(1)
    areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    mask=np.zeros(len(p),bool)
    for x in [-23,23]:
        for y in [-35,35]:mask|=(abs(np.linalg.norm(p[:,:2]-[x,y],axis=1)-2.2479)<1e-5)&(p[:,2]>-1.4)&(p[:,2]<3.01)
    on_wall=np.all(mask[mesh.facets[:,bf].T],axis=1)
    wall=bf[on_wall];assert len(wall)>0
    loads=np.zeros((basis.N,3))
    for side in [-1,1]:
        for pos,x in [('inner',18.85),('outer',43.75)]:
            on=(np.max(abs(tri[:,:,2]-.003),axis=1)<1e-5)&(abs(cent[:,0]-side*x)<2.00001)&(abs(cent[:,1])<15.95001)
            assert on.any()
            fb=FacetBasis(mesh,el,facets=bf[on])
            for axis in [0,2]:
                @LinearForm
                def load(v,w):return v[axis]
                unit=asm(load,fb)/areas[on].sum()
                if axis==0:loads[:,1]+=side*5*unit
                else:
                    loads[:,0]-=5*unit
                    loads[:,2]+=(1 if pos=='inner' else -1)*500/24.9*unit
    wr=M['target_wrench_right']
    coefficients=np.array([-wr['Fz_N']/10,wr['Fx_N']/10,wr['My_Nmm']/500])*C['load_multiplier']
    F=loads@coefficients
    support_area=float(areas[on_wall].sum())
    if elastic_support is None:
        fixed=basis.get_dofs(facets=wall).all();free=np.setdiff1d(np.arange(basis.N),fixed)
        U=np.zeros(basis.N);U[free]=splu(K[free][:,free]).solve(F[free])
        reactions=K@U-F
        residual=np.linalg.norm(reactions[free])/np.linalg.norm(F[free])
        support_energy=0.
    else:
        @BilinearForm
        def foundation(u,v,w):return elastic_support*np.sum(u*v,axis=0)
        Ks=asm(foundation,FacetBasis(mesh,el,facets=wall)).tocsc()
        U=splu(K+Ks).solve(F)
        reactions=-Ks@U
        residual=np.linalg.norm(K@U-F-reactions)/np.linalg.norm(F)
        support_energy=float(U@Ks@U/2)
    comps=np.array(basis.split_indices());xyz=basis.doflocs[:,comps[0]].T
    fv=F[comps].T;rv=reactions[comps].T
    errF=np.linalg.norm((fv+rv).sum(0));errM=np.linalg.norm(np.cross(xyz,fv+rv).sum(0))
    assert residual<1e-7 and errF<1e-5 and errM<1e-3,(residual,errF,errM)
    # Independently check the imposed resultant on each side.
    applied=[]
    for side in [-1,1]:
        ids=xyz[:,0]*side>0
        moment=np.cross(xyz[ids]-[side*31.3,0,.003],fv[ids]).sum(0)
        force=fv[ids].sum(0)
        expected=np.array([side*wr['Fx_N'],0,wr['Fz_N']])*C['load_multiplier']
        assert np.linalg.norm(force-expected)<1e-8
        assert abs(moment[1]-side*wr['My_Nmm']*C['load_multiplier'])<1e-7
        applied.append(dict(side=side,force_N=force.tolist(),moment_Nmm=moment.tolist()))
    g=basis.interpolate(U).grad;strain=(g+g.swapaxes(0,1))/2
    stress=2*mu*strain+lam*np.eye(3)[:,:,None,None]*np.trace(strain,axis1=0,axis2=1)
    dev=stress-np.eye(3)[:,:,None,None]*np.trace(stress,axis1=0,axis2=1)/3
    vmq=np.sqrt(1.5*np.sum(dev*dev,axis=(0,1)))
    vm=(vmq*basis.dx).sum(1)/basis.dx.sum(1)
    average=(stress*basis.dx[None,None,:,:]).sum(3)/basis.dx.sum(1)[None,None,:]
    principal=np.linalg.eigvalsh(np.moveaxis(average,2,0))[:,-1]
    tc=p[mesh.t.T].mean(1);region=(abs(tc[:,0])<13)&(abs(tc[:,1])<29)
    disp=U[basis.nodal_dofs].T
    dof_vectors=U[comps].T
    volumes=basis.dx.sum(1);order=np.argsort(vm);cdf=np.cumsum(volumes[order])/volumes.sum()
    p95=float(vm[order[np.searchsorted(cdf,.95)]])
    key=f'{name}_h{h}_'+('fixed' if elastic_support is None else f'k{elastic_support:g}')
    rec=dict(variant=name,h_mm=h,elements=int(mesh.nelements),dofs=int(basis.N),
             material=C['material_fe'],load_multiplier=C['load_multiplier'],load_coefficients=coefficients.tolist(),
             support='fixed hole walls' if elastic_support is None else 'uniform 3D elastic foundation on hole walls',
             support_k_N_per_mm3=elastic_support,support_area_mm2=support_area,
             applied_per_side=applied,corner_max_displacement_mm=float(np.linalg.norm(disp,axis=1).max()),
             all_nodal_max_displacement_mm=float(np.linalg.norm(dof_vectors,axis=1).max()),
             compliance_Nmm=float(F@U),strain_energy_Nmm=float(U@K@U/2),support_energy_Nmm=support_energy,
             p95_element_vm_MPa=p95,max_element_vm_MPa=float(vm.max()),
             central_region_max_element_vm_MPa=float(vm[region].max()),
             central_region_max_element_principal_MPa=float(principal[region].max()),
             force_error_N=float(errF),moment_error_Nmm=float(errM),relative_residual=float(residual),runtime_s=time.time()-started)
    assert abs(rec['compliance_Nmm']/2-rec['strain_energy_Nmm']-support_energy)<1e-6
    (OUT/(key+'.json')).write_text(json.dumps(rec,indent=2))
    np.savez_compressed(OUT/(key+'.npz'),points=p,tets=mesh.t.T,triangles=mesh.facets[:,bf].T,
                        displacement=disp,element_vm=vm,element_principal=principal,central_region=region)
    print(json.dumps(rec),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--variant',choices=['baseline','revB'],default='revB')
    a.add_argument('--size',type=float,default=2.4);a.add_argument('--support',type=float)
    opt=a.parse_args();solve(opt.variant,opt.size,opt.support)
