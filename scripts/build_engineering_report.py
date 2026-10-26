"""Build the nine-page revision B portfolio, concise resume and evidence index."""
from pathlib import Path
import json,math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle

ROOT=Path(__file__).resolve().parents[1];S=json.loads((ROOT/'results/engineering/summary.json').read_text())
M=S['mechanism'];R=S['comparison'];FE=S['fe_cases'];B=FE['baseline_h2.4_fixed'];N=FE['revB_h2.4_fixed']
OUT=ROOT/'output/pdf';OUT.mkdir(exist_ok=True,parents=True)
pdfmetrics.registerFont(TTFont('SimHei','C:/Windows/Fonts/simhei.ttf'))
W,H=595.28,841.89;L=43;CW=W-2*L
navy=HexColor('#18334a');teal=HexColor('#147f88');gray=HexColor('#526274')
c=canvas.Canvas(str(OUT/'T42-结构设计作品集.pdf'),pagesize=(W,H))
c.setTitle('欠驱动夹爪结构分析与轻量化设计 - Rev B');c.setAuthor('Mechanical design study')
style=ParagraphStyle('body',fontName='SimHei',fontSize=10,leading=16,textColor=navy,wordWrap='CJK')
small=ParagraphStyle('cell',parent=style,fontSize=9,leading=14)
def para(text,y,size=10):
    st=ParagraphStyle('p',parent=style,fontSize=size,leading=size*1.6)
    p=Paragraph(text,st);_,h=p.wrap(CW,1000);p.drawOn(c,L,y-h);return y-h-9
def table(rows,y,widths=None):
    t=Table([[Paragraph(str(v),small) for v in row] for row in rows],colWidths=widths or [CW/len(rows[0])]*len(rows[0]))
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e2eff0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.5,teal),('LINEBELOW',(0,1),(-1,-1),.3,HexColor('#dbe4ea'))]))
    _,h=t.wrap(CW,1000);t.drawOn(c,L,y-h);return y-h-12
def pic(name,y,width=CW):
    im=ImageReader(str(ROOT/'assets'/name));iw,ih=im.getSize();height=width*ih/iw
    c.drawImage(im,L+(CW-width)/2,y-height,width,height,mask='auto');return y-height-10
def header(n,title,subtitle):
    c.setFillColor(teal);c.rect(0,H-12,W,12,fill=1,stroke=0)
    c.setFillColor(gray);c.setFont('Helvetica',9);c.drawString(L,H-39,'MECHANICAL DESIGN PORTFOLIO / REV B')
    c.setFillColor(navy);c.setFont('SimHei',22);c.drawString(L,H-78,title)
    c.setFillColor(gray);c.setFont('SimHei',9.5);c.drawString(L,H-101,subtitle)
    c.setStrokeColor(HexColor('#dbe4ea'));c.line(L,47,W-L,47)
    c.setFont('SimHei',8);c.drawString(L,32,'数字设计与验证 | 未打样、未进行抓取实测 | 2026-10-26')
    c.setFont('Helvetica',8);c.drawRightString(W-L,32,f'{n:02d} / 09')
    return H-125
def end(y):
    assert y>55,f'Page overflow: {y}'
    c.showPage()

capabilities=[['能力','本版已有证据','仍需实物或进一步模型'],
 ['机构分析','自由度、运动学、分段准静态闭合','真实物体接触搜索与动力学'],
 ['传动受力','张力、接触力、驱动需求及候选核对','弹簧、摩擦与持续输出标定'],
 ['零件设计','顶板、支座、销孔改型及尺寸图','工艺验证后的生产放行'],
 ['装配配合','3 类尺寸链、39 姿态刚体检查','整机附件、实测装配与连续扫掠'],
 ['材料工艺','PETG/PA12 比较、孔径试块与工序','实测材料、打印补偿与过程能力'],
 ['结构验证','等效载荷刚度、网格与支承敏感性','真实接触分载、峰值强度及疲劳']]

y=header(1,'欠驱动夹爪结构设计','机构与传力分析、装配公差修订、支承顶板轻量化与刚度复核')
y=para('基于 Yale OpenHand T42 双转轴方案开展二次设计。保留上游机构来源，新增可复现计算、关键配合修订、上部装配及数值验证；与四自由度机械臂项目独立维护。',y)
y=table([['Rev B 顶板体积减少','刚性支承下柔度增加','闭合路径刚体检查'],[f'{R["volume_reduction_percent"]:.2f}%',f'{R["compliance_increase_percent"]:.2f}%','39 姿态 / 351 对']],y)
y=pic('engineering_assembly.png',y)
y=table(capabilities,y,[75,215,CW-290])
y=para('取舍：为覆盖底板尺寸偏差，将凹槽从 1.8 mm 修订为 1.65 mm。体积收益由旧版 5.53% 调整为 5.07%，优先满足拟定的最小底厚要求。',y,9)
end(y)

y=header(2,'自由度与欠驱动闭合','双指 4 个几何自由度 / 2 个执行器；单指 2 个转轴、1 根驱动腱绳')
y=para('近端杆长由 STEP 两销轴中心提取为 62.5 mm；远端名义长度 37.5 mm、关节传动半径 8 mm 采用官方参数并作常半径近似。弹簧不减少几何自由度，接触与回位力共同决定欠驱动构型。',y)
y=table([['模型','表达式与意义'],['末端运动学','x = L1 cos(q1) + L2 cos(q1+q2)<br/>z = L1 sin(q1) + L2 sin(q1+q2)'],['收绳量','s = r1(q1-q10) + r2(q2-q20)，角度单位 rad'],['回位模型','等效 K1=20、K2=40 N·mm/rad；研究输入，非原装弹簧实测值']],y,[110,CW-110])
y=pic('mechanism_analysis.png',y)
y=para('闭合顺序：15°/15° 零位起动；自由闭合到 55°/35°；规定近端接触后，远端继续到 90°；双接触后增加张力。该路径是规定接触约束下的准静态研究，未模拟实际物体碰撞搜索。',y)
y=para('对末端雅可比和接触力矩矩阵分别做中心差分核对；101 个载荷步均检查关节力矩平衡及接触力非负。脚本、原始路径 CSV 和误差记录随仓库交付。',y)
end(y)

y=header(3,'接触力与驱动需求','从腱绳张力推导关节力矩、接触力，再构造结构等效载荷')
y=para('接触点距近、远端轴心分别为 35、25 mm，法向垂直于各指节。以远端接触力 5 N、姿态 55°/90° 为一个研究点，求解 A·N + Ks(q-q0) = r·T，并要求两接触力均非负。',y)
y=table([['计算项','结果','适用条件'],['腱绳张力',f'{M["tension_N"]:.2f} N','理想关节、等效弹簧、常传动半径'],['近端 / 远端接触力',f'{M["contact_normal_N"][0]:.2f} / 5.00 N','不是夹爪额定抓取力'],['设计转矩需求',f'{M["drive"]["design_torque_Nm"]:.3f} N·m','效率 0.75，载荷系数 1.5'],['收绳 / 输出轴转角',f'{M["drive"]["tendon_stroke_mm"]:.2f} mm / {M["drive"]["motor_stroke_deg"]:.2f}°','单层有效卷线半径 10.75 mm'],['平均转速',f'{M["drive"]["average_motor_rpm"]:.2f} rpm','目标闭合时间 1 s']],y,[140,125,CW-265])
y=para('候选核对：兼容原安装方案的 MX-28，官方 12 V 参数为堵转转矩 2.5 N·m、空载转速 55 rpm。仅可作为候选；不能把这两个极限值组合成持续工作能力，尚需带载速度与温升验证。',y)
y=para('传给上部组件的外力必须包含入口腱绳向下的拉力。右侧座面中心处乘 1.5 后：Fx=+5.650 N、Fz=-28.055 N、My=+640.079 N·mm。左侧 Fx 与 My 镜像反号。',y)
y=para('新增有限元将该合力/合矩映射到顶板座面，形成一个等效牵引场景。上下板实际分载和接触压力尚未求解，不把场景载荷称为已经验证的实物载荷。',y)
y=para('单边接触筛查会排除负法向力：相同研究条件下，q1=55° 时，q2 的 1° 采样从约 84° 起满足双接触非负条件。未满足的姿态不计作稳定抓取。',y,9)
end(y)

y=header(4,'顶板改型与底厚尺寸链','制造偏差改变了方案选择；新版数据与旧版分开保留')
y=pic('revB_modification_drawing.png',y,width=470)
y=table([['版本','凹槽深度','名义底厚','最不利底厚','体积减少'],['A','1.80','1.20','1.05','5.53%'],['B','1.65','1.35','1.20',f'{R["volume_reduction_percent"]:.2f}%']],y,[60,110,110,110,CW-390])
y=para('尺寸链按底板 3.00±0.15、凹槽深度 +0/-0.15 计算。Rev B：2.85-1.65=1.20 mm。四凹槽均保留 10×24、R2 和原中心位置，顶板安装接口区域没有去料。实际底厚仍需逐槽测量。',y,9.5)
end(y)

y=header(5,'装配与精配合修订','完成成品尺寸 CAD；打印补偿必须由试块确定')
y=pic('joint_inspection_drawing.png',y,width=440)
y=table([['尺寸链','拟定成品要求','最不利结果'],['支座插入','槽 31.90±0.05；支座 31.60±0.05','总间隙 0.20-0.40'],['固定侧销孔','销 6.344-6.350；孔 6.325-6.340','直径过盈 0.004-0.025'],['转动侧销孔','销 6.344-6.350；孔 6.375-6.400','直径间隙 0.025-0.056']],y,[95,260,CW-355])
y=para('近、远指节与支座的成品孔径已写入 STEP；原始打印补偿孔与成品精配合明确分开。先做孔径试块，保证毛坯孔小于最终孔，再后加工；过大的孔不能靠铰孔缩小。',y,9.5)
y=para('几何发现：远端 95° 样点发生相交，双指过度内收也会互撞。Rev B 指定闭合路径的 39 个姿态、351 对刚体求交为零；不包括未采样运动、弹簧、绳和下部执行器。',y,9.5)
end(y)

y=header(6,'材料、工艺与强度需求','工艺规划和强度筛查已准备；性能与配合需样件确认')
y=pic('engineering_tolerances.png',y)
y=table([['路线','选用依据','本项目定位'],['PETG / FFF','厂商试样模量约 1.5/1.6 GPa，密度 1.27','装配样件和孔径补偿试块'],['PA 2200 / SLS','E=1650 MPa，密度 0.93；干态强度有方向差异','功能样件候选，新增 FE 的材料参考']],y,[100,230,CW-330])
y=para('工序：试块校准 → 零件成形 → 槽与基准检查 → 分类后加工销孔 → 实测销选配 → 干装配 → 安装回位与走线 → 分级加载。所有公差均为验收目标，尚无过程能力证明。',y)
p=M['pin_screen']
y=table([['销轴/耳板筛查','计算结果'],['研究载荷包络',f'{p["load_envelope_N"]:.2f} N，等效弹簧力偶假设'],['双剪 / 弯曲应力',f'{p["double_shear_MPa"]:.2f} / {p["central_load_bending_MPa"]:.2f} MPa'],['两倍裕量的材料需求',f'销材屈服依据 ≥{p["minimum_required_yield_MPa_at_factor2"]:.2f} MPa；耳板承压依据 ≥{p["minimum_required_bearing_allowable_MPa_at_factor2"]:.2f} MPa']],y,[160,CW-160])
y=para('这是一份材料与结构的需求筛查，不是强度放行。具体拉簧端力、缺口、压入应力、蠕变和疲劳未纳入；厂商试样强度也不直接作为零件许用值。',y,9.5)
end(y)

y=header(7,'等效载荷有限元复核','二次四面体、E=1650 MPa、泊松比假设 0.35；同载荷比较原始与新版')
y=pic('engineering_fea.png',y)
y=table([['模型','P2 节点位移采样最大值','柔度 F^T u'],['原始顶板',f'{B["all_nodal_max_displacement_mm"]:.5f} mm',f'{B["compliance_Nmm"]:.4f} N·mm'],['Rev B',f'{N["all_nodal_max_displacement_mm"]:.5f} mm',f'{N["compliance_Nmm"]:.4f} N·mm']],y,[100,220,CW-320])
y=pic('engineering_displacement.png',y,width=450)
y=para(f'刚性孔壁支承下，体积减少 {R["volume_reduction_percent"]:.2f}%，柔度增加 {R["compliance_increase_percent"]:.2f}%；两档网格柔度变化 ≤{R["mesh_change_upper_bound_percent"]:.2f}%。检查了每侧合力/合矩、总平衡、残差和能量。',y,9.5)
y=para('支承柔性显著影响绝对位移：本研究的两档弹性支承刚度为假设值，不能当成实测连接参数。局部应力峰值仍对网格敏感，因此不据此给出安全系数或额定抓取载荷。',y,9.5)
end(y)

y=header(8,'证据边界与打样验收','先确认孔配合与回位件，再校准模型和评估耐久')
y=table([['验证步骤','已准备的工作','执行后才能得到的结论'],['尺寸与孔径','校准试块、尺寸图、三类尺寸链、记录 CSV','实际补偿值、配合合格率'],['回位与传动','弹簧力矩及张力测量方案','真实闭合次序与传动效率'],['静载位移','同夹具原始/改型对照；25%-100% 分级加载','实际柔度、残余变形及模型误差'],['持续载荷','记录 1/10/30/60 min 温度与位移','该时长及工况下的蠕变/热表现'],['初步耐久','100 次调试后做 1,000 次筛查，记录磨损与松动','仅筛查结果，不是额定寿命']],y,[85,215,CW-300])
y=para('当前能支持的表述',y,15)
y=para('完成机构与传力建模、设计条件下的驱动需求分析、上部装配重建、零件与配合修订、公差链、材料工艺规划，以及等效载荷刚度对照和敏感性计算。',y)
y=para('当前不能支持的表述',y,15)
y=para('整套夹爪自主原创；整机全行程无干涉；电机持续选型已验证；局部强度/疲劳达标；实际抓取成功率、称重减重或寿命数据。图纸仍为设计评审版。',y)
y=para('工具与可复现性',y,15)
y=para('实际使用 CadQuery/OpenCascade、Gmsh、scikit-fem、SciPy 与 Python。提供 STEP/STL、公式、参数、原始数组和复现脚本。STEP 可导入 SolidWorks/Workbench，但没有把其他求解器结果标成 Workbench。',y)
y=para('已有的悬臂梁独立算例误差约 1.93%，用于求解方法检查；它不是实物测量误差。新载荷模型和制造公差仍需按试验计划验证。',y,9.5)
end(y)

bullets=[
'针对双转轴欠驱动夹爪建立运动与传力模型，分析腱绳张力、关节力矩及接触力，计算驱动需求，完成上部装配重建与闭合路径刚体干涉检查。',
'完成支承顶板、支座及销孔的参数化改型，校核最小底厚、插入间隙与销孔配合尺寸链，输出三维模型、改制尺寸图及孔径校准试块。',
f'基于推导载荷开展顶板等效载荷有限元对照，实体体积减少 {R["volume_reduction_percent"]:.2f}%，刚性支承下柔度增加 {R["compliance_increase_percent"]:.2f}%；完成网格与支承敏感性分析，并制定材料工艺及试验方案。']
y=header(9,'简历表达与成果索引','独立项目：欠驱动夹爪结构分析与轻量化设计')
for i,b in enumerate(bullets,1):y=para(f'{i}. {b}',y,10)
y=table([['成果','仓库位置'],['成品尺寸零件 / 三姿态装配','cad/engineering/*.step；*.stl'],['运动、受力与尺寸链','engineering.json；scripts/engineering_*.py'],['原始计算与碰撞记录','results/engineering；fea/raw-revB.zip'],['专题说明与试验计划','docs/机构与传力分析.md；装配公差与工艺.md；试验与验收计划.md'],['简历及能力证据表','docs/简历与证据.md']],y,[155,CW-155])
y=para('来源与许可',y,15)
y=para('原机构与源模型：Yale OpenHand / grablab/openhand-hardware，固定提交 b10197dcd79e7bcfa92c6d5a0bfa479e6a789fba。原始及派生 CAD 保留 CC BY-NC 3.0 署名和非商业许可要求；见仓库许可文件。',y,9)
y=para('<link href="https://www.eng.yale.edu/grablab/openhand/model_t42.html" color="#147f88">Yale T42 / 官方模型与装配资料</link><br/><link href="https://www.eng.yale.edu/grablab/openhand/OpenHand%20CAD%20Guide.pdf" color="#147f88">Yale CAD Guide / 名义杆长与传动半径</link><br/><link href="https://emanual.robotis.com/docs/en/dxl/mx/mx-28/" color="#147f88">ROBOTIS MX-28 / 候选执行器参数</link><br/><link href="https://www.eos.info/polymer-solutions/data-sheets/pds-pa-2200-balance" color="#147f88">EOS PA 2200 Balance / 材料数据</link><br/><link href="https://prusament.com/materials/prusament-petg/" color="#147f88">Prusament PETG / 工艺与材料数据</link>',y,9)
end(y);c.save()

evidence='# 简历与证据（Rev B）\n\n项目名：**欠驱动夹爪结构分析与轻量化设计**\n\n与四自由度机械臂项目独立列项。源机构为 Yale OpenHand T42；个人项目新增内容是分析、改型与验证，不是整机原创。\n\n## 简历三点版\n\n'+'\n'.join('- '+b for b in bullets)+'\n\n## 能力覆盖与边界\n\n'+'\n'.join('| '+' | '.join(row)+' |' for row in [capabilities[0],['---']*3]+capabilities[1:])
evidence+='''

## 主张对应证据

| 主张 | 可核对的文件 | 限定 |
|---|---|---|
| 运动与传力模型 | scripts/engineering_calculations.py；results/engineering/mechanism.json | 常传动半径、等效弹簧及规定接触条件 |
| 驱动需求与候选 | docs/机构与传力分析.md | 未验证持续转矩、带载速度和温升 |
| 39 姿态 / 351 对检查 | results/engineering/closure_sweep.json | 上部刚体、采样路径，不是整机连续无干涉证明 |
| 顶板、支座与销孔改型 | cad/engineering；results/engineering/cad_revB.json | 成品目标 CAD，尚未确定实际打印补偿 |
| 体积减少 5.07% | results/engineering/cad_revB.json | CAD 实体体积，不是称重或整机减重 |
| 柔度增加 3.63% | results/engineering/summary.json | 新推导等效载荷、孔壁刚性支承，非实际装配分载 |
| 网格变化 ≤0.66% | results/engineering/summary.json | 整体柔度复核，局部应力峰值仍网格敏感 |
| 工艺与验证计划 | docs/装配公差与工艺.md；docs/试验与验收计划.md | 计划已准备，实物测试尚未执行 |

## 面试应能解释的设计取舍

1. 为什么有 4 个关节自由度，却只有 2 个驱动？弹簧如何决定自由闭合顺序？
2. 张力为正时，为什么有些假设姿态仍算出负接触力？为什么必须排除？
3. 为什么把进入上部组件的腱绳拉力也计入顶板等效载荷？为什么这仍不等于实际接触分载？
4. 为什么原来的 1.8 mm 槽深改成 1.65 mm？能否写出最不利底厚尺寸链？
5. 为什么打印补偿孔不能直接当成标准配合？孔已经偏大时为什么不能靠铰孔修复？
6. 为什么整体柔度已基本稳定，却不能宣称局部峰值应力收敛？
7. 为什么孔壁全固定与弹性支承的绝对位移差很大？怎样通过试验确定实际边界？
8. 为什么不能使用电机堵转转矩证明连续运行？

实际工具为 CadQuery/OpenCascade、Gmsh、scikit-fem、SciPy。SolidWorks、Workbench 可按实际掌握程度放在个人技能栏，但本项目没有使用它们求解。简历内容须以自己理解和实际参与为准，不写实测抓取、寿命或量产结果。
'''
(ROOT/'docs/简历与证据.md').write_text(evidence,encoding='utf-8')

readme=f'''# 欠驱动夹爪结构分析与轻量化设计

基于 [Yale OpenHand T42](https://github.com/grablab/openhand-hardware) 双转轴方案的**独立二次设计项目**。当前为 **Rev B**：机构与传力计算、上部装配、关键配合与顶板改型、材料工艺规划、等效载荷有限元及试验方案。与四自由度机械臂项目分开维护。

![三阶段上部装配](assets/engineering_assembly.png)

## 已完成且有证据的工作

- 4 个关节几何自由度 / 2 个驱动的运动学和准静态传力模型，含非负接触筛查、驱动需求与 MX-28 候选核对。
- 修订顶板、支座及销孔成品尺寸，提供 STEP/STL、改制图、三类尺寸链与孔径试块；重建三姿态上部装配。
- 规定闭合路径 **39 个姿态、351 对零件** B-rep 求交检查，无实体相交。范围是上部刚体采样，不是整机连续扫掠。
- Rev B 顶板实体体积 **减少 {R['volume_reduction_percent']:.2f}%**；新推导的等效载荷、刚性孔壁支承下柔度 **增加 {R['compliance_increase_percent']:.2f}%**，两档网格柔度变化 **≤{R['mesh_change_upper_bound_percent']:.2f}%**。
- 弹性支承敏感性、销轴/耳板强度需求筛查、材料工艺路线和可填写的试验记录模板。

## 设计取舍

原 1.8 mm 深凹槽只有 1.2 mm **名义**底厚；考虑底板 ±0.15 mm 后，最不利仅 1.05 mm。Rev B 改为 1.65 mm 深，使拟定公差下的最小底厚达到 1.20 mm，因此体积收益从旧版 5.53% 调整为 5.07%。

![底厚尺寸链和孔径试块](assets/engineering_tolerances.png)

## 成果入口

- [九页中文作品集](output/pdf/T42-结构设计作品集.pdf)
- [简历三点版与能力证据](docs/简历与证据.md)
- [机构与传力分析](docs/机构与传力分析.md)
- [装配、公差与工艺](docs/装配公差与工艺.md)
- [上部组件机械件清单](docs/机械件清单.md)
- [新增结构验证](docs/新增结构验证.md)
- [试验与验收计划](docs/试验与验收计划.md)、[空白记录模板](results/engineering/test_record_template.csv)
- [顶板 STEP](cad/engineering/top_plate_revB.step)、[支座 STEP](cad/engineering/bracket_revB.step)、[近指节 STEP](cad/engineering/finger_A_finished.step)、[远指节 STEP](cad/engineering/finger_B_finished.step)
- [闭合装配 STEP](cad/engineering/revB_upper_q55_90.step)、[孔径试块 STEP](cad/engineering/pin_fit_coupon.step)
- [顶板改制图](assets/revB_modification_drawing.svg)、[关节与支座检验图](assets/joint_inspection_drawing.svg)
- [计算摘要](results/engineering/summary.json)、[有限元原始数组](results/engineering/fea/raw-revB.zip)

![机构计算](assets/mechanism_analysis.png)
![有限元与支承敏感性](assets/engineering_fea.png)

## 适用边界

研究接触点、等效弹簧刚度、传动效率均显式列在 [engineering.json](engineering.json)，未冒充实测参数。计算将上部组件合力和合矩映射为顶板的等效牵引，未求解上下板实际接触分载。弹性支承刚度是敏感性输入；绝对位移不能当作已标定实物预测。局部应力峰值仍网格敏感，不给出强度安全系数或额定抓取力。

没有打样、称重、抓取成功率或耐久实测。孔与槽公差是拟定验收目标，成品 CAD 必须配合工艺试块和后加工方案使用。当前图纸为设计评审版。六类能力的完成程度及限制见简历证据表。

## 复现

实际工具：CadQuery/OpenCascade、Gmsh、scikit-fem、SciPy、Python。PDF 另用 ReportLab。未声称使用 SolidWorks/Workbench 求解；STEP 可导入，但没有相应原生特征树或工程文件。

Windows PowerShell；环境、缓存与下载默认使用 E 盘：

```powershell
./run.ps1 -Stage setup
./run.ps1 -Stage engineering
./run.ps1 -Stage engineering-fea
./run.ps1 -Stage engineering-report -ReportPython 'your-python-with-reportlab.exe'
```

`engineering` 生成几何、机构计算、Rev B CAD、碰撞检查与图；`engineering-fea` 运行六个新有限元算例并汇总；报告读取已有结果，**不重新求解**。计算顺序与软件依赖详见脚本及 requirements 文件。全部 FE 算例在普通电脑上可能需要较长时间。也可直接运行单个 Python 脚本。

## 版本与来源

Rev A 的 `design.json`、`cad/variants`、`results/summary.json` 和 [初版说明](docs/设计与验证说明.md) 保留为历史。**现行结果在 `results/engineering`，新模型在 `cad/engineering`**；两版载荷、材料和槽深不同，不混用百分比或位移。

原机构、指节、支座与基准顶板来自 Yale OpenHand，固定提交 `b10197dcd79e7bcfa92c6d5a0bfa479e6a789fba`。本项目新增参数化改型、成品配合修订、运动与静力模型、数值验证及文档。原始 STEP 保留于 `cad/upstream`；引用清单见 [工程来源](docs/工程来源.md)。

The Yale OpenHand Project is an initiative to advance the design and use of robotic hands designed and built through rapid-prototyping techniques in order to encourage more variation and innovation in mechanical hardware. Please visit our site at www.eng.yale.edu/grablab/openhand for more details.

R.R. Ma, L.U. Odhner, A.M. Dollar, “A Modular, Open-Source 3D Printed Underactuated Hand,” ICRA, 2013。上游及派生 CAD 遵循 CC BY-NC 3.0，见 [原许可](UPSTREAM_LICENSE.md) 和 [本仓库许可说明](LICENSE.md)。
'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')

verification=f'''# Rev B 新增结构验证

本版的材料、载荷和凹槽深度与 Rev A 不同，结果不得交叉比较。使用二次四面体位移单元和一阶几何。研究输入为 PA2200 参考 E=1650 MPa、假设 ν=0.35；上部机构推导的合力/合矩乘 1.5 后，以四座面等效牵引加载。未求解真实上下板接触分载。

## 刚性支承对照

| 模型 | 体积 mm³ | P2 节点采样最大位移 mm | 柔度 N·mm |
|---|---:|---:|---:|
| 原始 | {S['cad']['baseline_volume_mm3']:.3f} | {B['all_nodal_max_displacement_mm']:.6f} | {B['compliance_Nmm']:.6f} |
| Rev B | {S['cad']['volume_mm3']:.3f} | {N['all_nodal_max_displacement_mm']:.6f} | {N['compliance_Nmm']:.6f} |

体积减少 **{R['volume_reduction_percent']:.2f}%**；柔度增加 **{R['compliance_increase_percent']:.2f}%**，对应本载荷模式等效刚度变化 **{R['equivalent_stiffness_change_percent']:.2f}%**。这不是整手减重或强度提高。

## 网格复核

| 模型 | 粗/细单元数 | 柔度变化 | 全域单元应力最大值变化 | 中央区域单元应力最大值变化 |
|---|---|---:|---:|---:|
'''+''.join(f"| {v['variant']} | {v['coarse_elements']} / {v['fine_elements']} | {v['compliance_change_percent']:.3f}% | {v['global_element_stress_change_percent']:.2f}% | {v['central_element_stress_change_percent']:.2f}% |\n" for v in S['mesh_convergence'])+f'''
目标网格尺寸 3.0→2.4 mm；柔度变化上限按百分比向上保留两位，报告为 **≤{R['mesh_change_upper_bound_percent']:.2f}%**。局部应力指标没有同等稳定，不能据此声称峰值应力收敛或强度已达标。保留应力数据用于定位和后续验证，不给安全系数。中央区域仅按单元中心 |X|<13、|Y|<29 定义，不是人为选出的“已通过”强度区域。

## 支承敏感性

| 支承 | P2 节点采样最大位移 mm | 柔度 N·mm | 相对刚性支承柔度增幅 |
|---|---:|---:|---:|
'''+''.join(f"| {'孔壁全固定' if v['k'] is None else '孔壁弹性支承 k='+str(v['k'])+' N/mm³'} | {v['displacement_mm']:.6f} | {v['compliance_Nmm']:.6f} | {v['compliance_increase_vs_fixed_percent']:.2f}% |\n" for v in S['support_sensitivity'])+'''
弹性支承采用孔壁三向分布弹簧：K_total=K_solid+∫k NᵀN dA。k=100/10 是探索边界敏感性的假设值，没有映射为某个真实螺钉或支柱。柔度差异说明支承模型对绝对变形影响很大；不能把全固定结果当成未经校准的实物预测。弹性支承工况只计算 Rev B，不把它与全固定原始件作改型优劣比较。

固定边界、相同泊松比下，线弹性位移随 1/E 缩放。E=1000–2200 MPa 的敏感性值也列入摘要；这个解析缩放只用于固定边界，不套用到材料与支承相对刚度同时改变的情形。

## 检查与数据定义

每个算例验证了：左右分区合力/合矩、总力与总力矩平衡、自由度残差，以及外力功/2=实体应变能+支承弹簧能。二次节点最大值包含顶点与边中点，仍是节点采样，不是连续位移场极值的严格证明。云图只绘制角点位移，明确标注。

应力值为单元积分平均值；圆角、凹槽交线、固定边界及载荷转换区可能产生强梯度。未建立完整材料许用值、螺栓预紧或疲劳模型。销轴/耳板另做解析需求筛查，见装配公差文档。

原始六组网格、位移和应力数组在 `results/engineering/fea/raw-revB.zip`，SHA-256 见同目录 `raw_checksums.json`。结果摘要与全部假设见 `results/engineering/summary.json`。该报告明确记录不确定性，而不是以应力云图代替验证结论。
'''
(ROOT/'docs/新增结构验证.md').write_text(verification,encoding='utf-8')
print(str(OUT/'T42-结构设计作品集.pdf'))
