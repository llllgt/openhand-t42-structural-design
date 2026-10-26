"""Independent cantilever verification of the elasticity element and unit convention."""
from pathlib import Path
import json
import numpy as np
from scipy.sparse.linalg import spsolve
from skfem import MeshTet, Basis, FacetBasis, LinearForm, ElementVector, ElementTetP2, asm
from skfem.models.elasticity import linear_elasticity,lame_parameters
ROOT=Path(__file__).resolve().parents[1]
E=2000.;nu=.35;L=20.;w=4.;t=2.;P=1.
I=w*t**3/12;G=E/(2*(1+nu));theory=P*L**3/(3*E*I)+P*L/((5/6)*G*w*t)
rows=[]
for h in [1.,.5]:
 mesh=MeshTet.init_tensor(np.linspace(0,L,round(L/h)+1),np.linspace(0,w,round(w/h)+1),np.linspace(0,t,round(t/h)+1))
 elem=ElementVector(ElementTetP2());b=Basis(mesh,elem);K=asm(linear_elasticity(*lame_parameters(E,nu)),b).tocsc()
 fixed=b.get_dofs(lambda x:np.isclose(x[0],0)).all();free=np.setdiff1d(np.arange(b.N),fixed)
 fb=FacetBasis(mesh,elem,facets=mesh.facets_satisfying(lambda x:np.isclose(x[0],L)))
 @LinearForm
 def load(v,ww):return -P/(w*t)*v[2]
 f=asm(load,fb)
 u=np.zeros(b.N);u[free]=spsolve(K[free][:,free],f[free]);compliance=float(u@f);delta=compliance/P
 rows.append({'h_mm':h,'elements':mesh.nelements,'loaded_face_mean_deflection_mm':delta,'Timoshenko_reference_mm':theory,'relative_error':abs(delta/theory-1)})
 print(json.dumps(rows[-1]),flush=True)
(ROOT/'results'/'solver_verification.json').write_text(json.dumps(rows,indent=2))
assert rows[-1]['relative_error']<.05
assert rows[-1]['relative_error']<rows[0]['relative_error']
(ROOT/'results'/'solver_verification.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
