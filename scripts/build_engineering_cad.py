"""Manufacturing-aware revision B and a pin-fit process coupon."""
from pathlib import Path
import json, math
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from engineering_geometry import data

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/engineering';OUT.mkdir(exist_ok=True,parents=True)
C=json.loads((ROOT/'design.json').read_text())
E=json.loads((ROOT/'engineering.json').read_text())
tol=E['tolerance_proposals_mm'];depth=tol['revised_pocket_depth'][1]
retained=sum(tol['finished_retained_hole'])/2
rotating=sum(tol['finished_rotating_hole'])/2
bracket_width=sum(tol['finished_bracket_width'])/2
base=cq.importers.importStep(str(ROOT/'cad/upstream/a1_p_t42.STEP'))
modified=base
for x,y in C['pocket_centers_mm']:
    tool=(cq.Workplane('XY',origin=(x,y,C['bottom_z_mm']-.1)).sketch()
          .rect(C['pocket_width_mm'],C['pocket_length_mm']).vertices().fillet(C['pocket_corner_radius_mm']).finalize().extrude(depth+.1))
    modified=modified.cut(tool)
plate=modified.val()
assert plate.isValid() and len(plate.Solids())==1
parts=data();bracket=parts[2]
def finish_bores(shape, diameters):
    """Replace complete, split cylindrical bores; reject partial-cylinder features."""
    groups={}
    for f in shape.Faces():
        if f.geomType()!='CYLINDER':continue
        cy=BRepAdaptor_Surface(f.wrapped).Cylinder();radius=cy.Radius()
        target=next((v for key,v in diameters.items() if abs(radius-key)<1e-6),None)
        if target is None:continue
        assert abs(cy.Axis().Direction().Z())>1-1e-6
        bb=f.BoundingBox();x,y,_=cy.Location().Coord()
        key=tuple(round(v,7) for v in [x,y,radius,bb.zmin,bb.zmax,target])
        groups[key]=groups.get(key,0)+f.Area()
    assert groups
    for (x,y,radius,zlo,zhi,target),area in groups.items():
        assert abs(area/(2*math.pi*radius*(zhi-zlo))-1)<1e-5
        ring=(cq.Workplane('XY',origin=(x,y,zlo)).circle(radius).circle(target/2).extrude(zhi-zlo)).val()
        shape=shape.fuse(ring).clean()
    assert shape.isValid() and len(shape.Solids())==1
    return shape

# Final-size CAD represents post-processed bores; it must not be printed
# directly using the upstream shrink compensation without a coupon trial.
raw_c=cq.importers.importStep(str(ROOT/'cad/upstream/c1_t42.STEP')).val()
raw_c=finish_bores(raw_c,{3.25:retained})
bb=raw_c.BoundingBox();meta=parts[-1]
bracket=(raw_c.translate((0,0,-(bb.zmin+bb.zmax)/2)).rotate((0,0,0),(1,0,0),-90)
         .translate(tuple(meta['bracket_translation_mm'])))
trim=cq.Workplane('XY').box(200,bracket_width,200).val()
bracket=bracket.intersect(trim)
assert bracket.isValid() and len(bracket.Solids())==1
raw_a=cq.importers.importStep(str(ROOT/'cad/upstream/finger_pp_ext_A_t42.STEP')).val()
raw_b=cq.importers.importStep(str(ROOT/'cad/upstream/finger_pp_B_t42.STEP')).val()
finished_a=finish_bores(raw_a,{3.525:rotating,3.25:retained})
finished_b=finish_bores(raw_b,{3.525:rotating})
# Hole coupon uses CAD diameters, not guaranteed printed hole sizes.
coupon=cq.Workplane('XY').box(70,36,8,centered=(True,True,False))
holes=[]
for row,diameters in enumerate([[6.15,6.25,6.35,6.45,6.55],[3.00,3.10,3.20,3.30,3.40]]):
    for col,d in enumerate(diameters):
        x=-26+13*col;y=9-18*row
        cutter=cq.Workplane('XY',origin=(x,y,-1)).circle(d/2).extrude(10)
        coupon=coupon.cut(cutter);holes.append(dict(x_mm=x,y_mm=y,CAD_diameter_mm=d))
# A corner notch gives an unambiguous orientation without text embossing.
coupon=coupon.cut(cq.Workplane('XY',origin=(-35,18,-1)).box(5,5,10,centered=(True,True,False)))
for name,obj in [('top_plate_revB',plate),('bracket_revB',bracket),('finger_A_finished',finished_a),
                 ('finger_B_finished',finished_b),('pin_fit_coupon',coupon.val())]:
    cq.exporters.export(obj,str(OUT/(name+'.step')))
    cq.exporters.export(obj,str(OUT/(name+'.stl')),tolerance=.08,angularTolerance=.1)
    back=cq.importers.importStep(str(OUT/(name+'.step'))).val()
    assert back.isValid() and abs(back.Volume()-obj.Volume())<.001
removed=base.val().cut(plate)
region=cq.Workplane('XY',origin=(0,0,-5)).box(26,58,20,centered=(True,True,False)).val()
outside=removed.cut(region)
assert sum(abs(s.Volume()) for s in outside.Solids())<.001
metrics=dict(revision='B',pocket_depth_nominal_mm=depth,nominal_floor_mm=C['nominal_central_floor_mm']-depth,
             worst_case_floor_mm=tol['blank_floor'][0]-depth,baseline_volume_mm3=base.val().Volume(),volume_mm3=plate.Volume(),
             volume_reduction_percent=100*(1-plate.Volume()/base.val().Volume()),
             original_bracket_width_mm=31.75,finished_bracket_width_mm=bracket_width,
             source_bracket_volume_mm3=parts[2].Volume(),finished_bracket_volume_mm3=bracket.Volume(),
             original_plate_interface_preserved=True,
             finished_retained_bore_nominal_mm=retained,finished_rotating_bore_nominal_mm=rotating,
             final_bore_status='Post-processing target geometry; coupon calibration and reaming required, not raw print compensation',
             removed_outside_design_region_mm3=sum(abs(s.Volume()) for s in outside.Solids()),
             coupon=dict(size_mm=[70,36,8],holes=holes,notch_corner='X-, Y+',status='Calibration coupon; not measured'))
(ROOT/'results/engineering/cad_revB.json').write_text(json.dumps(metrics,indent=2))
print(json.dumps(metrics,indent=2))
