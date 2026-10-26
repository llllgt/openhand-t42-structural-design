"""3D linear elasticity on the actual STEP solid. Units: mm, N, MPa.

Reference boundary cases only: no actuator/tendon/contact assembly model.
"""
from pathlib import Path
import os, json, argparse, time
os.environ.setdefault('MPLCONFIGDIR','E:/Codex/cache/matplotlib')
import numpy as np
import gmsh
from scipy.sparse.linalg import splu
from skfem import MeshTet, Basis, FacetBasis, LinearForm, ElementVector, ElementTetP2, asm
from skfem.models.elasticity import linear_elasticity, lame_parameters
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'design.json').read_text())
OUT=ROOT/'results'/'fea';OUT.mkdir(parents=True,exist_ok=True)

def make_mesh(step,h):
 gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
 gmsh.model.add('top_plate');gmsh.model.occ.importShapes(str(step));gmsh.model.occ.synchronize()
 gmsh.option.setNumber('Mesh.MeshSizeMax',h);gmsh.option.setNumber('Mesh.MeshSizeMin',h*.35)
 gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',20)
 gmsh.option.setNumber('Mesh.Algorithm3D',1);gmsh.option.setNumber('Mesh.Optimize',1)
 gmsh.model.mesh.generate(3)
 tags,xyz,_=gmsh.model.mesh.getNodes(); xyz=np.array(xyz).reshape(-1,3)
 kinds,_,conn=gmsh.model.mesh.getElements(3)
 tet=np.array(conn[list(kinds).index(4)]).reshape(-1,4)
 order=np.argsort(tags); inv=np.empty(int(max(tags))+1,dtype=int); inv[np.array(tags,dtype=int)]=np.arange(len(tags))
 tet=inv[tet];gmsh.finalize()
 return MeshTet(xyz.T,tet.T)

def solve_case(name,h):
 start=time.time();mesh=make_mesh(ROOT/'cad'/'variants'/(name+'.step'),h)
 element=ElementVector(ElementTetP2())
 basis=Basis(mesh,element)
 material=C['material_assumption'];lam,mu=lame_parameters(material['E_MPa'],material['nu'])
 K=asm(linear_elasticity(lam,mu),basis).tocsc()
 points=mesh.p.T
 fixed_mask=np.zeros(len(points),dtype=bool)
 for x in [-23.,23.]:
  for y in [-35.,35.]:
   rr=np.sqrt((points[:,0]-x)**2+(points[:,1]-y)**2)
   fixed_mask|=(np.abs(rr-2.2479)<1e-5)&(points[:,2]>-1.4)&(points[:,2]<3.01)
 fixed_nodes=np.where(fixed_mask)[0];assert len(fixed_nodes)>30, len(fixed_nodes)
 boundary_ids=mesh.boundary_facets()
 boundary=mesh.facets[:,boundary_ids].T
 fixed_facets=boundary_ids[np.all(fixed_mask[boundary],axis=1)]
 fixed=basis.get_dofs(facets=fixed_facets).all();free=np.setdiff1d(np.arange(basis.N),fixed)
 tri=points[boundary];cent=tri.mean(axis=1)
 area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
 pads={}
 for side in [-1,1]:
  for pos,x in [('inner',18.85),('outer',43.75)]:
   mask=(np.max(np.abs(tri[:,:,2]-.003),axis=1)<1e-5)&(np.abs(cent[:,0]-side*x)<2.00001)&(np.abs(cent[:,1])<15.95001)
   ids=np.where(mask)[0];assert len(ids)>0
   fb=FacetBasis(mesh,element,facets=boundary_ids[ids])
   vectors=[]
   for axis in range(3):
    @LinearForm
    def traction(v,w):return v[axis]
    vector=asm(traction,fb);vector/=area[ids].sum();vectors.append(vector)
   pads[(side,pos)]=vectors
 loads=np.zeros((basis.N,3))
 def add(col,pad,axis,force):loads[:,col]+=pads[pad][axis]*force
 for side in [-1,1]:
  for pos in ['inner','outer']:
   add(0,(side,pos),2,-5.)
   add(1,(side,pos),0,side*5.)
  add(2,(side,'inner'),2,500./24.9)
  add(2,(side,'outer'),2,-500./24.9)
 lu=splu(K[free][:,free]);u=np.zeros_like(loads);u[free]=lu.solve(loads[free])
 reactions=K@u-loads
 names=['vertical_20N','spread_10N_each','opposed_500Nmm']
 records={}
 volumes=np.abs(np.linalg.det(np.stack([points[mesh.t[1]]-points[mesh.t[0]],points[mesh.t[2]]-points[mesh.t[0]],points[mesh.t[3]]-points[mesh.t[0]]],axis=2)))/6
 for k,case in enumerate(names):
  U=u[basis.nodal_dofs,k].T
  g=basis.interpolate(u[:,k]).grad
  strain=(g+g.swapaxes(0,1))/2;trace=np.trace(strain,axis1=0,axis2=1)
  stress=2*mu*strain+lam*np.eye(3)[:,:,None,None]*trace
  dev=stress-np.eye(3)[:,:,None,None]*np.trace(stress,axis1=0,axis2=1)/3
  vm_q=np.sqrt(1.5*np.sum(dev*dev,axis=(0,1)))
  vm=np.sum(vm_q*basis.dx,axis=1)/basis.dx.sum(axis=1)
  components=np.array(basis.split_indices())
  allpoints=basis.doflocs[:,components[0]].T
  force=loads[components,k].T;reaction=reactions[components,k].T
  netforce=(force+reaction).sum(axis=0);netmoment=np.cross(allpoints,force+reaction).sum(axis=0)
  assert np.linalg.norm(netforce)<1e-6 and np.linalg.norm(netmoment)<1e-4
  free_res=np.linalg.norm(reactions[free,k])/max(np.linalg.norm(loads[free,k]),1e-12)
  assert free_res<1e-8
  order=np.argsort(vm); cum=np.cumsum(volumes[order])/volumes.sum();p95=vm[order[np.searchsorted(cum,.95)]]
  records[case]={'max_displacement_mm':float(np.linalg.norm(U,axis=1).max()),'compliance_Nmm':float(loads[:,k]@u[:,k]),'max_element_vm_MPa':float(vm.max()),'volume_weighted_p95_vm_MPa':float(p95),'applied_force_N':force.sum(0).tolist(),'force_balance_error_N':float(np.linalg.norm(netforce)),'moment_balance_error_Nmm':float(np.linalg.norm(netmoment)),'relative_free_residual':float(free_res),'strain_energy_Nmm':float(u[:,k]@K@u[:,k]/2)}
  np.savez_compressed(OUT/(name+'_p2_'+str(h)+'_'+case+'.npz'),points=points,tets=mesh.t.T,triangles=boundary,displacement=U,element_vm=vm,fixed_nodes=fixed_nodes,force=force)
 record={'variant':name,'element':'quadratic tetrahedron P2 on linear geometry','mesh_size_mm':h,'nodes':len(points),'dofs':int(basis.N),'tetrahedra':mesh.nelements,'fixed_nodes':len(fixed_nodes),'mesh_volume_mm3':float(volumes.sum()),'runtime_s':time.time()-start,'cases':records}
 (OUT/(name+'_p2_'+str(h)+'.json')).write_text(json.dumps(record,indent=2))
 print(json.dumps(record),flush=True)
 return record

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--variant',default='baseline');p.add_argument('--size',type=float,default=2.0);a=p.parse_args();solve_case(a.variant,a.size)
