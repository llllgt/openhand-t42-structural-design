"""Recover datums from source B-reps; reconstruct a nominal upper subassembly.

Units mm. This is a separately constrained STEP reconstruction, not a recovered
SolidWorks mate tree. Raw source mold features remain in the interference check.
"""
from pathlib import Path
import json, math, shutil, hashlib
import numpy as np
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'engineering'
OUT.mkdir(parents=True, exist_ok=True)
CAD = ROOT / 'cad' / 'engineering'
CAD.mkdir(parents=True, exist_ok=True)
SRC = ROOT / 'cad' / 'upstream'


def cylinders(s):
    rows = []
    for i, f in enumerate(s.Faces()):
        if f.geomType() == 'CYLINDER':
            cy = BRepAdaptor_Surface(f.wrapped).Cylinder()
            rows.append(dict(face=i, radius=cy.Radius(), origin=list(cy.Location().Coord()),
                             axis=list(cy.Axis().Direction().Coord())))
    return rows


def joint(s, radius):
    rows = [r for r in cylinders(s) if abs(r['radius'] - radius) < 1e-6]
    xy = np.array([r['origin'][:2] for r in rows])
    assert len(xy) and np.max(np.linalg.norm(xy - xy[0], axis=1)) < 1e-5
    b = s.BoundingBox()
    return np.r_[xy.mean(0), (b.zmin + b.zmax) / 2]


def data(use_finished=False):
    a = cq.importers.importStep(str(SRC / 'finger_pp_ext_A_t42.STEP')).val()
    b = cq.importers.importStep(str(SRC / 'finger_pp_B_t42.STEP')).val()
    c = cq.importers.importStep(str(SRC / 'c1_t42.STEP')).val()
    p0, p1, p2 = joint(a, 3.525), joint(a, 3.25), joint(b, 3.525)
    L = np.linalg.norm(p1 - p0)
    assert abs(L - 62.5) < 1e-4
    theta_a = math.degrees(math.atan2(*(p1-p0)[1::-1]))
    # The largest longitudinal pad plane normal determines distal centerline.
    planes = [f for f in b.Faces() if f.geomType() == 'PLANE'
              and abs(f.normalAt().z) < .1]
    pad = max(planes, key=lambda f: f.Area())
    n = np.array(pad.normalAt().toTuple())
    e = np.array([n[1], -n[0], 0.])
    assert e[1] < 0
    theta_b = math.degrees(math.atan2(e[1], e[0]))
    if use_finished:
        a=cq.importers.importStep(str(CAD/'finger_A_finished.step')).val()
        b=cq.importers.importStep(str(CAD/'finger_B_finished.step')).val()
    # Pads face +Z in both canonical parts. Width is parallel to world Y.
    a = a.translate(tuple(-p0)).rotate((0,0,0),(0,0,1),-theta_a).rotate((0,0,0),(1,0,0),-90)
    b = b.translate(tuple(-p2)).rotate((0,0,0),(0,0,1),-theta_b).rotate((0,0,0),(1,0,0),90)
    cb = c.BoundingBox()
    dx = 31.3 - (cb.xmin + cb.xmax)/2
    dz = -5.997 + cb.ymax
    zmid = (cb.zmin + cb.zmax)/2
    c = c.translate((0,0,-zmid)).rotate((0,0,0),(1,0,0),-90).translate((dx,0,dz))
    # Higher 6.5 mm pin hole is the proximal finger pivot.
    raw_c = cq.importers.importStep(str(SRC / 'c1_t42.STEP')).val()
    base = min([r for r in cylinders(raw_c) if abs(r['radius']-3.25)<1e-6],
               key=lambda r:r['origin'][1])['origin']
    j0 = np.array([base[0]+dx, 0., -base[1]+dz])
    lower = max([r for r in cylinders(raw_c) if abs(r['radius']-3.25)<1e-6],
                key=lambda r:r['origin'][1])['origin']
    # Incoming vertical tendon tangent on outer side of lower routing pin.
    inlet_x = lower[0] + dx + 3.175 + .25
    return a,b,c,j0,float(L),dict(
        proximal_axis_source_mm=p0.tolist(), distal_axis_source_mm=p1.tolist(),
        distal_link_axis_source_mm=p2.tolist(), proximal_length_mm=float(L),
        distal_nominal_length_mm=37.5, distal_length_source='Yale CAD Guide p.8 (PDF p.9); nominal contact datum',
        canonical_proximal_rotation_deg=theta_a, canonical_distal_rotation_deg=theta_b,
        right_proximal_axis_world_mm=j0.tolist(),
        bracket_translation_mm=[dx,0,dz], bracket_width_mm=cb.zmax-cb.zmin,
        bracket_flange_width_mm=cb.xmax-cb.xmin,
        mounting_slot_width_mm=20.9, mounting_slot_length_mm=31.9,
        joint_pin_nominal_mm=6.35, raw_retained_bore_mm=6.5, raw_rotating_bore_mm=7.05,
        tendon_inlet_x_mm=inlet_x,
        assumptions=['Bracket flange upper face mated to plate underside Z=-2.997',
                     'Bracket centered at X=31.3, Y=0; mirrored by 180 deg about Z',
                     'Distal datum uses longitudinal pad plane; no native assembly mates recovered',
                     'Incoming tendon diameter 0.5 mm is a study assumption',
                     'Motor, springs, tendon and cast pads not included in solid collision model'])


def rotate(s, deg):
    return s.rotate((0,0,0),(0,1,0),-float(deg))


def pose(q1, q2, parts=None):
    a,b,c,j0,L,_ = parts or data()
    j1 = j0 + L*np.array([math.cos(math.radians(q1)),0,math.sin(math.radians(q1))])
    right = {'mount_R':c,'proximal_R':rotate(a,q1).translate(tuple(j0)),
             'distal_R':rotate(b,q1+q2).translate(tuple(j1))}
    return right | {k[:-1]+'L':s.rotate((0,0,0),(0,0,1),180) for k,s in right.items()}


def overlap(a,b):
    ba,bb=a.BoundingBox(),b.BoundingBox()
    if any(getattr(ba,k+'max') < getattr(bb,k+'min')-1e-6 or
           getattr(bb,k+'max') < getattr(ba,k+'min')-1e-6 for k in 'xyz'):
        return 0.
    c=a.intersect(b)
    return sum(abs(s.Volume()) for s in c.Solids())


def main():
    src=Path('E:/Codex/downloads/openhand-hardware')/json.loads((ROOT/'source_manifest.json').read_text())['commit']/'model t42'/'step'
    for name in ['b1_dynamixel_t42.STEP']:
        if not (SRC/name).exists():shutil.copy2(src/name,SRC/name)
    parts=data();a,b,c,j0,L,meta=parts
    plate=cq.importers.importStep(str(ROOT/'cad/variants/pocket_1p8.step')).val()
    meta['bracket_plate_overlap_mm3']=overlap(c,plate)
    meta['bracket_plate_distance_mm']=c.distance(plate)
    # Explicit sampling; no claim of a continuous collision proof.
    sweeps=[]
    for q in range(0,121,5):
        p=pose(45,q,parts)
        sweeps.append(dict(sweep='distal',angle_deg=q,
                           overlap_mm3=overlap(p['proximal_R'],p['distal_R'])))
    for q in range(0,111,5):
        p=pose(q,60,parts)
        sweeps.append(dict(sweep='proximal',angle_deg=q,
                           overlap_mm3=overlap(p['proximal_R'],c)+overlap(p['proximal_R'],plate)))
    checks=[]
    for q1,q2 in [(15,15),(30,30),(45,45),(55,75),(55,90),(55,100),(70,85),(85,90)]:
        p=pose(q1,q2,parts)|{'plate':plate}
        pairs=[('proximal_R','distal_R'),('proximal_R','mount_R'),('proximal_R','plate'),
               ('distal_R','plate'),('distal_R','mount_R'),('proximal_R','proximal_L'),
               ('distal_R','distal_L'),('distal_R','proximal_L'),('proximal_R','distal_L')]
        rows=[dict(parts=[x,y],overlap_mm3=overlap(p[x],p[y])) for x,y in pairs]
        checks.append(dict(q1_deg=q1,q2_deg=q2,pairs=rows,clear=all(r['overlap_mm3']<1e-4 for r in rows)))
        print(q1,q2,[(r['parts'],round(r['overlap_mm3'],4)) for r in rows if r['overlap_mm3']>1e-4],flush=True)
    meta['pose_checks']=checks;meta['joint_sweeps']=sweeps
    (OUT/'geometry.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    for q1,q2 in [(15,15),(55,90)]:
        p=pose(q1,q2,parts)|{'plate':plate}
        assembly=cq.Assembly(name='upper_mechanism_reconstruction')
        for name,s in p.items():assembly.add(s,name=name)
        assembly.save(str(CAD/f'upper_q{q1}_{q2}.step'))
    print(json.dumps(meta,indent=2),flush=True)


if __name__=='__main__':main()
