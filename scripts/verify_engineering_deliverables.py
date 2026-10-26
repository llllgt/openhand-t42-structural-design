"""Audit delivered STEP dimensions, upstream attribution, arrays and document links."""
from pathlib import Path
import json,hashlib,zipfile,csv,re,io
import numpy as np
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/engineering'
C=json.loads((ROOT/'engineering.json').read_text());S=json.loads((OUT/'summary.json').read_text())
manifest=json.loads((ROOT/'source_manifest.json').read_text())
source_hashes={r['path']:r['sha'] for r in manifest['files']}
verified_source=[]
for p in (ROOT/'cad/upstream').glob('*.STEP'):
    b=p.read_bytes();sha=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
    assert sha==source_hashes['model t42/step/'+p.name],p.name
    verified_source.append(p.name)
dimensions={}
for p in sorted((ROOT/'cad/engineering').glob('*.step')):
    if p.name.startswith('upper_q'):continue
    shape=cq.importers.importStep(str(p)).val()
    assert shape.isValid(),p.name
    count=len(shape.Solids())
    assert count==(7 if p.name.startswith('revB_upper') else 1),(p.name,count)
    dimensions[p.name]=dict(solids=count,volume_mm3=shape.Volume())
    if p.name=='bracket_revB.step':assert abs(shape.BoundingBox().ylen-31.60)<1e-6
    if p.name=='top_plate_revB.step':assert abs(shape.Volume()-S['cad']['volume_mm3'])<.001
    if p.name in ['bracket_revB.step','finger_A_finished.step','finger_B_finished.step']:
        radii=[BRepAdaptor_Surface(f.wrapped).Cylinder().Radius() for f in shape.Faces() if f.geomType()=='CYLINDER']
        expected=[6.3325] if p.name=='bracket_revB.step' else [6.3325,6.3875] if p.name=='finger_A_finished.step' else [6.3875]
        for d in expected:assert any(abs(r-d/2)<1e-6 for r in radii),(p.name,d)
drum=cq.importers.importStep(str(ROOT/'cad/upstream/b1_dynamixel_t42.STEP')).val()
tori=[BRepAdaptor_Surface(f.wrapped).Torus() for f in drum.Faces() if f.geomType()=='TORUS']
roots=[t.MajorRadius()-t.MinorRadius() for t in tori]
assert any(abs(r-C['drum_groove_root_mm'])<1e-6 for r in roots)
assert abs(C['drum_effective_radius_mm']-C['drum_groove_root_mm']-C['tendon_diameter_assumption_mm']/2)<1e-9
hashes=json.loads((OUT/'fea/raw_checksums.json').read_text())
with zipfile.ZipFile(OUT/'fea/raw-revB.zip') as z:
    assert set(z.namelist())==set(hashes)
    for n,sha in hashes.items():
        b=z.read(n);assert hashlib.sha256(b).hexdigest()==sha
        d=np.load(io.BytesIO(b));assert d['displacement'].shape==d['points'].shape
        assert np.all(np.isfinite(d['displacement'])) and np.all(d['element_vm']>=0)
        assert len(d['element_vm'])==len(d['tets'])
for r in S['fe_cases'].values():
    assert r['force_error_N']<1e-5 and r['moment_error_Nmm']<1e-3 and r['relative_residual']<1e-7
    assert abs(r['compliance_Nmm']/2-r['strain_energy_Nmm']-r['support_energy_Nmm'])<1e-6
with (OUT/'test_record_template.csv').open(encoding='utf-8',newline='') as f:
    records=list(csv.reader(f));assert all(len(row)==len(records[0]) for row in records)
    measured=records[0].index('measured_value');assert all(not row[measured] for row in records[1:])
links=[]
for p in [ROOT/'README.md',*list((ROOT/'docs').glob('*.md'))]:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):continue
        target=target.split('#')[0]
        assert (p.parent/target).exists(),(p.name,target)
        links.append(target)
result=dict(source_STEP_files_verified=verified_source,delivered_STEP_checks=dimensions,
            drum_groove_roots_mm=roots,raw_FE_archives_verified=len(hashes),local_document_links_checked=len(links),
            empty_test_template_verified=True,force_moment_residual_energy_checks='passed',
            status='Delivered digital evidence checked; no physical validation implied')
(OUT/'delivery_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
