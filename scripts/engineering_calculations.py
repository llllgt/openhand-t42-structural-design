"""Planar kinematics, unilateral two-contact statics, drive and tolerance study.

No fitting to the old arbitrary FE cases. All assumed inputs are in engineering.json.
"""
from pathlib import Path
import json, math, csv, os
import numpy as np
os.environ.setdefault('MPLCONFIGDIR','E:/Codex/cache/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'engineering';OUT.mkdir(exist_ok=True,parents=True)
C=json.loads((ROOT/'engineering.json').read_text())
G=json.loads((OUT/'geometry.json').read_text())
L1=G['proximal_length_mm'];L2=G['distal_nominal_length_mm']
r=np.array(C['joint_moment_arms_mm']);k=np.array(C['equivalent_spring_rates_Nmm_per_rad'])
q0=np.radians(C['rest_angles_deg']);q=np.radians(C['target_angles_deg'])
c1,c2=C['contact_distances_mm'];h=C['contact_pad_offset_mm']


def endpoint(q):
    a,b=q
    return np.array([L1*np.cos(a)+L2*np.cos(a+b), L1*np.sin(a)+L2*np.sin(a+b)])


def jacobian(q):
    a,b=q
    return np.array([[-L1*np.sin(a)-L2*np.sin(a+b),-L2*np.sin(a+b)],
                     [L1*np.cos(a)+L2*np.cos(a+b),L2*np.cos(a+b)]])


def contacts(q):
    e1=np.array([np.cos(q[0]),np.sin(q[0])]);e2=np.array([np.cos(sum(q)),np.sin(sum(q))])
    n1=np.array([-e1[1],e1[0]]);n2=np.array([-e2[1],e2[0]])
    return np.array([c1*e1+h*n1,L1*e1+c2*e2+h*n2]), -np.array([n1,n2])


def contact_matrix(q):
    return np.array([[c1,c2+L1*np.cos(q[1])],[0.,c2]])


def forces(q,T,radii=r,rates=k):
    spring=rates*(q-q0)
    normal=np.linalg.solve(contact_matrix(q),radii*T-spring)
    return normal,spring


def wrench(q,T,normal):
    points,directions=contacts(q)
    j0=np.array(G['right_proximal_axis_world_mm'])[[0,2]]
    seat=np.array([31.3,.003]);points=points+j0
    f=normal[:,None]*directions
    relative=points-seat
    # Positive moment about global Y: z*Fx - x*Fz.
    M=np.sum(relative[:,1]*f[:,0]-relative[:,0]*f[:,1])
    M+=(G['tendon_inlet_x_mm']-seat[0])*T
    F=f.sum(0)+np.array([0.,-T])
    return dict(Fx_N=float(F[0]),Fz_N=float(F[1]),My_Nmm=float(M),
                contact_points_world_xz_mm=points.tolist(),contact_forces_xz_N=f.tolist(),
                incoming_tendon_force_xz_N=[0.,-float(T)],
                note='Upper-subassembly resultant, not a solved distribution among top plate, bracket and lower plate')


def main():
    T=(c2*C['target_distal_normal_force_N']+k[1]*(q[1]-q0[1]))/r[1]
    normal,spring=forces(q,T)
    assert np.all(normal>0)
    residual=contact_matrix(q)@normal+spring-r*T
    # Independent finite differences of positions validate moment-arm matrix.
    eps=1e-6
    points,directions=contacts(q)
    numeric=np.empty((2,2))
    for j in range(2):
        dq=np.eye(2)[j]*eps
        dp=(contacts(q+dq)[0]-contacts(q-dq)[0])/(2*eps)
        numeric[j]= -np.sum(dp*directions,axis=1)
    assert np.max(np.abs(numeric-contact_matrix(q)))<1e-6
    Jn=np.column_stack([(endpoint(q+np.eye(2)[j]*eps)-endpoint(q-np.eye(2)[j]*eps))/(2*eps) for j in range(2)])
    assert np.max(np.abs(Jn-jacobian(q)))<1e-6
    # Staged closure: energy-minimizing free motion, then proximal contact,
    # then both contacts. Contact poses are imposed; no simulated object claim.
    Tfirst=k[0]*(q[0]-q0[0])/r[0]
    Tsecond=k[1]*(q[1]-q0[1])/r[1]
    path=[]
    for t in np.linspace(0,T,101):
        if t<=Tfirst:
            qi=q0+r*t/k;fn=np.zeros(2);stage='free'
        elif t<=Tsecond:
            qi=np.array([q[0],q0[1]+r[1]*t/k[1]])
            fn=np.array([(r[0]*t-k[0]*(qi[0]-q0[0]))/c1,0.]);stage='proximal_contact'
        else:qi=q;fn,_=forces(qi,t);stage='two_contacts'
        assert np.all(fn>=-1e-9)
        eq=contact_matrix(qi)@fn+k*(qi-q0)-r*t
        assert np.max(np.abs(eq))<1e-8
        path.append(dict(tension_N=float(t),q1_deg=float(np.degrees(qi[0])),q2_deg=float(np.degrees(qi[1])),
                         N1_N=float(fn[0]),N2_N=float(fn[1]),stage=stage,
                         tendon_take_up_mm=float(r@(qi-q0))))
    with (OUT/'closure_path.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(path[0]));w.writeheader();w.writerows(path)
    sensitivity=[]
    posture_screen=[]
    for q2deg in range(15,96):
        qi=np.radians([55.,float(q2deg)])
        t=(c2*5+k[1]*(qi[1]-q0[1]))/r[1]
        fn,_=forces(qi,t)
        posture_screen.append(dict(q1_deg=55.,q2_deg=q2deg,T_N=float(t),N1_N=float(fn[0]),N2_N=float(fn[1]),
                                   unilateral_admissible=bool(np.all(fn>=0))))
    assert any(not row['unilateral_admissible'] for row in posture_screen)
    for kd in [20.,30.,40.,50.,60.]:
        rates=np.array([20.,kd]);t=(c2*5+rates[1]*(q[1]-q0[1]))/r[1]
        fn,_=forces(q,t,rates=rates)
        sensitivity.append(dict(kd_Nmm_per_rad=kd,T_N=float(t),N1_N=float(fn[0]),N2_N=float(fn[1]),
                                admissible=bool(np.all(fn>=0))))
    for rd in [7.,8.,9.]:
        radii=np.array([8.,rd]);t=(c2*5+spring[1])/rd
        fn,_=forces(q,t,radii=radii)
        sensitivity.append(dict(rd_mm=rd,T_N=float(t),N1_N=float(fn[0]),N2_N=float(fn[1]),
                                admissible=bool(np.all(fn>=0))))
    eta=C['drive_efficiency_assumption'];rm=C['drum_effective_radius_mm'];mult=C['load_multiplier']
    stroke=r@(q-q0);angle=stroke/rm
    tol=C['tolerance_proposals_mm']
    def difference(a,b):return [tol[a][0]-tol[b][1],tol[a][1]-tol[b][0]]
    thickness=difference('blank_floor','old_pocket_depth')
    revised=difference('blank_floor','revised_pocket_depth')
    assert revised[0]>=1.2-1e-8
    pin=C['tolerance_proposals_mm']['measured_joint_pin'][0]
    # Screening envelope for equivalent-couple spring model. Real extension
    # spring end forces need adding after selection of anchors and spring SKU.
    P=mult*(3*T+normal.sum());span=27.6;ear=4.15
    shear=P/(2*np.pi*pin**2/4);bending=(P*span/4)/(np.pi*pin**3/32)
    bearing=P/(2*pin*ear)
    out=dict(study_inputs=C,geometric_DOF=4,actuators=2,
             tendon_constraints_per_finger=1,uncontrolled_configuration_DOF_per_finger_at_fixed_tendon=1,
             tension_N=float(T),contact_normal_N=normal.tolist(),spring_torque_Nmm=spring.tolist(),
             target_wrench_right=wrench(q,T,normal),
             first_contact_tension_N=float(Tfirst),second_contact_tension_N=float(Tsecond),
             drive=dict(effective_radius_mm=rm,torque_Nm=float(T*rm/eta/1000),
                        design_torque_Nm=float(T*rm/eta*mult/1000),tendon_stroke_mm=float(stroke),
                        motor_stroke_deg=float(np.degrees(angle)),
                        average_motor_rpm=float(np.degrees(angle)/360*60/C['closure_time_target_s']),
                        efficiency_cases=[dict(eta=e,design_torque_Nm=float(T*rm/e*mult/1000)) for e in [.65,.75,.85]],
                        candidate='2 x MX-28 at 12 V, preliminary compatibility candidate',
                        manufacturer_stall_Nm=2.5,manufacturer_no_load_rpm=55,
                        continuous_duty_qualified=False),
             tolerances=dict(old_floor_range_mm=thickness,revised_floor_range_mm=revised,
                             slot_bracket_clearance_mm=difference('finished_slot_length','finished_bracket_width'),
                             retained_hole_interference_mm=difference('measured_joint_pin','finished_retained_hole'),
                             rotating_hole_clearance_mm=difference('finished_rotating_hole','measured_joint_pin')),
             pin_screen=dict(load_envelope_N=float(P),span_mm=span,ear_thickness_mm=ear,
                             double_shear_MPa=float(shear),central_load_bending_MPa=float(bending),
                             bearing_MPa=float(bearing),
                             minimum_required_yield_MPa_at_factor2=float(2*np.sqrt(bending*bending+3*shear*shear)),
                             minimum_required_bearing_allowable_MPa_at_factor2=float(2*bearing),
                             status='Demand calculation only, no supplied pin material certificate; spring end forces excluded'),
             sensitivity=sensitivity,posture_screen=posture_screen,
             verification=dict(equilibrium_residual_Nmm=float(np.max(np.abs(residual))),
                               contact_matrix_finite_difference_error_mm=float(np.max(np.abs(numeric-contact_matrix(q)))),
                               endpoint_Jacobian_error_mm=float(np.max(np.abs(Jn-jacobian(q))))))
    (OUT/'mechanism.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    # Plot mechanical results, not illustrative AI images.
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig,axs=plt.subplots(1,3,figsize=(14,4.1),layout='constrained')
    for i in [1,2]:axs[0].plot([v['tension_N'] for v in path],[v[f'q{i}_deg'] for v in path],label=f'q{i}')
    axs[0].set(xlabel='Tendon tension / N',ylabel='Joint angle / deg',title='Prescribed contact closure');axs[0].legend()
    for i in [1,2]:axs[1].plot([v['tension_N'] for v in path],[v[f'N{i}_N'] for v in path],label=f'Contact {i}')
    axs[1].set(xlabel='Tendon tension / N',ylabel='Normal force / N',title='Unilateral contact forces');axs[1].legend()
    j0=np.array(G['right_proximal_axis_world_mm'])[[0,2]]
    for deg,color in [([15,15],'#b9c5cd'),([55,35],'#6ba6ad'),([55,90],'#147f88')]:
        qr=np.radians(deg);j1=j0+L1*np.array([np.cos(qr[0]),np.sin(qr[0])]);tip=j0+endpoint(qr)
        for side in [-1,1]:
            pp=np.array([j0,j1,tip]);pp[:,0]*=side;axs[2].plot(pp[:,0],pp[:,1],'-o',color=color,lw=2)
    axs[2].set(xlabel='X / mm',ylabel='Z / mm',title='Centerline poses (no object model)');axs[2].set_aspect('equal')
    for ax in axs:ax.grid(alpha=.2)
    fig.savefig(ROOT/'assets/mechanism_analysis.png',dpi=170);plt.close(fig)
    print(json.dumps({key:out[key] for key in ['tension_N','contact_normal_N','target_wrench_right','drive','tolerances','verification']},indent=2))


if __name__=='__main__':main()
