"""Build the current portfolio; delegate to Rev B when engineering results exist."""
from pathlib import Path
import runpy,sys
if (Path(__file__).resolve().parents[1]/'results/engineering/summary.json').exists():
 runpy.run_path(str(Path(__file__).with_name('build_engineering_report.py')),run_name='__main__')
 sys.exit(0)
import json,math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
ROOT=Path(__file__).resolve().parents[1]
S=json.loads((ROOT/'results'/'summary.json').read_text())
OUT=ROOT/'output'/'pdf';OUT.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('SimHei','C:/Windows/Fonts/simhei.ttf'))
FONT='SimHei';W,H=595.28,841.89;M=43;CW=W-2*M
navy=HexColor('#18334a');teal=HexColor('#147f88');gray=HexColor('#526274')
c=canvas.Canvas(str(OUT/'T42-结构设计作品集.pdf'),pagesize=(W,H));c.setTitle('OpenHand T42 支承顶板轻量化与刚度校核');c.setAuthor('Project portfolio')
style=ParagraphStyle('body',fontName=FONT,fontSize=10.5,leading=17,textColor=navy,wordWrap='CJK',spaceAfter=8)
small=ParagraphStyle('small',parent=style,fontSize=9,leading=14)
def para(text,y,size=None):
 st=style if size is None else ParagraphStyle('temp',parent=style,fontSize=size,leading=size*1.55)
 p=Paragraph(text,st);_,h=p.wrap(CW,900);p.drawOn(c,M,y-h);return y-h-10
def header(n,title,subtitle):
 c.setFillColor(teal);c.rect(0,H-12,W,12,fill=1,stroke=0)
 c.setFont('Helvetica',9);c.setFillColor(gray);c.drawString(M,H-39,'MECHANICAL DESIGN PORTFOLIO / OPENHAND T42 / REV A')
 c.setFont(FONT,23);c.setFillColor(navy);c.drawString(M,H-79,title)
 c.setFont(FONT,10);c.setFillColor(gray);c.drawString(M,H-102,subtitle)
 c.setStrokeColor(HexColor('#dbe4ea'));c.line(M,47,W-M,47)
 c.setFont(FONT,8);c.drawString(M,32,'设计与数值验证项目 | 未制作实物 | 2026-10-26')
 c.setFont('Helvetica',8);c.drawRightString(W-M,32,f'{n:02d} / 06')
 return H-128
def pic(path,y,width=CW):
 im=ImageReader(str(ROOT/'assets'/path));iw,ih=im.getSize();height=width*ih/iw
 c.drawImage(im,M+(CW-width)/2,y-height,width,height,mask='auto');return y-height-12
def table(data,y,widths=None):
 cells=[[Paragraph(str(v),small) for v in row] for row in data]
 t=Table(cells,colWidths=widths or [CW/len(data[0])]*len(data[0]),hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e2eff0')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),.5,teal),('LINEBELOW',(0,1),(-1,-1),.3,HexColor('#dbe4ea'))]))
 _,hh=t.wrap(CW,800);t.drawOn(c,M,y-hh);return y-hh-14
def end(y):
 assert y>55, f'page overflow: {y}'
 c.showPage()

rows=S['comparison'];maxc=max(r['compliance_increase_percent'] for r in rows);maxmesh=math.ceil(100*max(abs(r['compliance_change_percent']) for r in S['mesh_convergence']))/100
y=header(1,'欠驱动夹爪支承顶板','基于 Yale OpenHand T42 的轻量化设计与刚度校核')
y=para('围绕原夹爪的手指支承顶板，在保留安装接口的前提下，比较凹槽深度对实体体积与变形的影响。项目包含源模型核验、参数化改型、改制图、三种载荷工况和网格复核。',y)
y=table([['实体体积减少','最不利柔度增加','网格复核变化'],['5.53%',f'{maxc:.2f}%',f'≤ {maxmesh:.2f}%']],y)
y=pic('design_comparison.png',y)
y=para('设计取舍',y,15)
y=para('第一版保留 1.8 mm 深的四凹槽方案，中央名义底厚为 1.2 mm。减重来自受控区域内去料，未添加新包络。该方案通过本次预设的 10% 柔度增加筛选规则，适合进入打样验证。',y)
y=para('原项目提供机构、顶板及其接口；本项目完成凹槽改型、方案参数、数值对照及证据整理。实际使用 CadQuery、Gmsh、scikit-fem 与 SciPy，未将计算标注为 Workbench 结果。',y)
end(y)

y=header(2,'几何改型与工艺要求','改制尺寸图；原有孔、配合槽和外周定位结构以基准 STEP 为准')
y=pic('modification_drawing.png',y)
y=table([['凹槽深度 / mm','剩余名义底厚 / mm','体积减少','处理'],['1.0','2.0','3.07%','保守备选'],['1.8','1.2','5.53%','进入有限元复核'],['2.4','0.6','7.38%','底厚规则不通过']],y,[105,135,100,CW-340])
y=para('深度初拟 1.8 mm（+0 / -0.15），其他非配合凹槽尺寸初拟 ±0.15 mm，并单独检验实际底厚 ≥ 1.2 mm。材料、打印方向和成形偏差尚未确定，因此这是一张设计评审图。',y,9.5)
end(y)

y=header(3,'载荷路径与模型边界','零件级参考工况；不等同于整手额定抓取力')
y=pic('boundary_conditions.png',y,width=470)
y=table([['工况','座面载荷','比较目的'],['V / 竖向','每侧合计 -10 N Z；总计 -20 N','竖向变形'],['S / 撑开','左侧 -10 N X；右侧 +10 N X','平面内刚度'],['M / 弯矩','每侧内外座面施加相反竖向力，力臂 24.9 mm；每侧 500 N·mm','弯曲柔度']],y,[75,285,CW-360])
y=para('四个安装孔的圆柱壁全固定。载荷通过实际座面面积积分施加。未建模螺钉预紧、接触间隙、支柱柔性以及完整腱绳-手指传力，因此不能用结果推导整手负载能力。',y)
y=para('统一材料假设：E = 2000 MPa，ν = 0.35，ρ = 1.20 g/cm³。均质各向同性、线弹性；未代表特定打印牌号或材料方向。',y)
end(y)

y=header(4,'轻量化收益与变形代价','最终比较使用二次四面体；最大位移为网格角点采样值')
y=pic('fea_comparison.png',y)
y=table([['工况','原始位移 / mm','改型位移 / mm','柔度增加'],*[[['V','S','M'][i],f"{r['baseline_corner_max_mm']:.5f}",f"{r['modified_corner_max_mm']:.5f}",f"{r['compliance_increase_percent']:.2f}%"] for i,r in enumerate(rows)]],y)
y=pic('displacement_field.png',y)
y=para('柔度 C = Fᵀu。柔度增加与刚度下降的百分比不相等；本报告比较的是同一工况下的整体变形代价。图示为未放大的原始几何，颜色表示位移，左右使用同一色标。',y,9)
end(y)

y=header(5,'数值检查与结果适用范围','保留独立梁算例、两档网格、平衡残差和原始数组')
y=para('求解方法检查',y,15)
v=S['solver_verification'];y=table([['梁算例网格 / mm','有限元平均挠度 / mm','与梁公式的差异'],*[[r['h_mm'],f"{r['loaded_face_mean_deflection_mm']:.6f}",f"{r['relative_error']*100:.2f}%"] for r in v]],y)
y=para('参考梁：20 × 4 × 2 mm，端面均布 1 N，总挠度参考值 0.50405 mm（弯曲 + 剪切）。三维固支端与一维梁理论仍有模型差异。',y,9)
y=para('顶板网格复核：目标网格尺寸 3.0 → 2.4 mm',y,15)
y=table([['模型 / 工况','V 柔度变化','S 柔度变化','M 柔度变化'],*[[name,*[f"{r['compliance_change_percent']:.2f}%" for r in S['mesh_convergence'] if r['variant']==name]] for name in ['baseline','pocket_1p8']]],y)
y=para('所有最终工况均通过总力、总力矩平衡和自由自由度残差检查。二次位移单元仍采用一阶直边几何；上述网格复核支持整体柔度对比，不证明局部峰值应力已收敛。',y)
y=para('解释边界',y,15)
y=para('体积变化来自 CAD；质量由同密度全实体估算。没有实物称重、抓取成功率、耐久试验或实际负载标定。应力数据为线弹性参考，未建立材料许用值，不给出安全系数。',y)
y=para('下一步实物验证应包括：同工艺原始/改型件称重、座面位移测试、接口尺寸检查，以及持续载荷和温升下的蠕变评估。',y)
end(y)

y=header(6,'成果索引与简历表达','与四自由度机械臂分开列项；突出机械零件设计与验证能力')
y=table([['交付物','证据位置'],['参数化模型与源数据','design.json；cad/upstream；cad/variants'],['改制图与可视化','assets/modification_drawing.svg；assets/*.png'],['实际求解与数值记录','scripts/analyze.py；results/summary.json；results/fea'],['完整设计边界','docs/设计与验证说明.md'],['可复现环境','requirements.txt；requirements-lock.txt；run.ps1']],y,[155,CW-155])
y=para('可用于简历的项目描述',y,15)
bullets=[
'针对 T42 手指支承顶板设计四处 10 × 24 mm、R2 圆角凹槽，比较 1.0/1.8/2.4 mm 三档深度；以剩余名义底厚 ≥ 1.2 mm 为约束筛选方案，通过布尔差集核验安装接口区域未去料，输出 STEP/STL 及改制尺寸图。',
'建立二次四面体线弹性有限元模型，固定四个安装孔壁，在支承座面施加总计 20 N 竖向力、每侧 10 N 撑开力及每侧 500 N·mm 弯矩三种参考工况，对照原始与改型顶板的位移和柔度。',
f'选取 1.8 mm 深凹槽方案，实现零件实体体积减少 5.53%；三工况最大柔度增幅为 {maxc:.2f}%，满足预设 ≤ 10% 的筛选条件，其中弯矩工况角点最大位移由 0.1933 mm 增至 0.2031 mm。',
f'将候选件网格由 21,231 加密至 32,642 个四面体，原始/改型件各工况柔度变化均 ≤ {maxmesh:.2f}%；独立悬臂梁细网格挠度与 Timoshenko 梁公式相差 {v[-1]["relative_error"]*100:.2f}%，并完成总力、总力矩及求解残差检查。']
for i,b in enumerate(bullets,1):y=para(str(i)+'. '+b,y,9.5)
y=para('来源与署名',y,15)
y=para('Yale OpenHand Project；R. R. Ma, L. U. Odhner, A. M. Dollar.<br/>A Modular, Open-Source 3D Printed Underactuated Hand, ICRA 2013.<br/>github.com/grablab/openhand-hardware<br/>固定版本 b10197dcd79e7bcfa92c6d5a0bfa479e6a789fba。<br/>上游及派生模型遵循 CC BY-NC 3.0；完整署名和许可见仓库。',y,9)
end(y);c.save()

readme=f'''# OpenHand T42 支承顶板轻量化与刚度校核

基于 Yale OpenHand T42 的**独立机械设计与数值验证项目**。研究对象为手指支承顶板，保留原有安装接口，比较中央凹槽深度与变形代价。与四自由度机械臂项目分开维护。

![原始与改型对比](assets/design_comparison.png)

## 已完成的结果

- 三种凹槽深度方案、有效 STEP/STL、参数化生成脚本及改制尺寸图。
- 候选方案：四个 10 × 24 mm、R2、深 1.8 mm 的凹槽，中央名义底厚 1.2 mm。
- 实体体积 **减少 5.53%**；统一密度 1.20 g/cm³ 下，全实体估算质量从 36.930 g 到 34.886 g。这不是实际打印重量。
- 最终三个参考载荷工况的最大柔度增加 **{maxc:.2f}%**；两档网格的柔度变化不超过 **{maxmesh:.2f}%**。
- 独立梁算例细网格挠度与含剪切的梁公式相差 **{v[-1]['relative_error']*100:.2f}%**。

![载荷定义](assets/boundary_conditions.png)

| 工况 | 原始角点最大位移 / mm | 改型角点最大位移 / mm | 柔度增加 |
|---|---:|---:|---:|
'''+''.join(f"| {r['case']} | {r['baseline_corner_max_mm']:.5f} | {r['modified_corner_max_mm']:.5f} | {r['compliance_increase_percent']:.2f}% |\n" for r in rows)+f'''
![工况结果](assets/fea_comparison.png)

## 交付文件

- [六页中文作品集](output/pdf/T42-结构设计作品集.pdf)
- [候选 STEP](cad/variants/pocket_1p8.step)、[候选 STL](cad/variants/pocket_1p8.stl)
- [改制尺寸图](assets/modification_drawing.svg)
- [设计与验证说明](docs/设计与验证说明.md)
- [结果摘要](results/summary.json)、[对照 CSV](results/comparison.csv)
- [简历与证据](docs/简历与证据.md)

## 模型假设

本版主要展示**参数化零件改型、轻量化方案取舍与有限元刚度验证**。装配配合仅保留原接口，材料与工艺仅完成初步约束；尚未完成整手机构运动学、腱绳传力和驱动选型。六类能力的逐项证据与缺项见 [简历与证据](docs/简历与证据.md#六类能力覆盖情况)。

均质各向同性线弹性材料，E=2000 MPa、ν=0.35；安装孔壁全固定；实际座面上分布载荷。三种工况是零件级参考，不是整手额定载荷。二次四面体位移单元在一阶直边几何上计算。柔度为 Fᵀu；应力输出是单元积分平均值，局部峰值不作强度结论。没有打样、耐久或抓取成功率实测。

实际工具为 CadQuery、Gmsh、scikit-fem 与 SciPy。STEP 可导入 SolidWorks / Workbench，但不附带其原生建模特征树，也不声称已在 Workbench 求解。

## 复现

Windows PowerShell，Python 3.12。环境、缓存和源文件默认放在 E 盘：

```powershell
./run.ps1 -Stage setup
./run.ps1 -Stage cad
./run.ps1 -Stage verify
./run.ps1 -Stage fea
./run.ps1 -Stage figures
```

全量依赖锁定见 requirements-lock.txt；直接运行依赖见 requirements.txt。报告脚本另依赖 reportlab。关键上游 STEP 已随仓库提供，不需要完整手模型即可复现；scripts/fetch_upstream.py 可获取固定版本的 188 个相关源文件并核验 Git blob 哈希，默认约 93 MB，放入 E:/Codex/downloads。

## 上游与许可

原始机构、顶板、手指及安装接口来自 [Yale OpenHand](https://github.com/grablab/openhand-hardware)，固定提交 b10197dcd79e7bcfa92c6d5a0bfa479e6a789fba。个人新增部分为四凹槽参数化改型、几何检查、数值模型、对照数据及文档。原始文件保留于 cad/upstream；派生文件位于 cad/variants。

The Yale OpenHand Project is an initiative to advance the design and use of robotic hands designed and built through rapid-prototyping techniques in order to encourage more variation and innovation in mechanical hardware. Please visit our site at www.eng.yale.edu/grablab/openhand for more details.

参考：R.R. Ma, L.U. Odhner, A.M. Dollar, “A Modular, Open-Source 3D Printed Underactuated Hand,” ICRA, 2013。上游与派生模型保留 CC BY-NC 3.0，见 [原许可](UPSTREAM_LICENSE.md) 和 [本仓库许可说明](LICENSE.md)。
'''
(ROOT/'README.md').write_text(readme.replace('\n+','\n'),encoding='utf-8')
evidence='# 简历与证据\n\n项目名：基于 OpenHand T42 的夹爪支承顶板轻量化与刚度校核\n\n'+ '\n'.join('- '+b for b in bullets)+'\n\n## 主张与证据\n\n| 表述 | 证据 | 边界 |\n|---|---|---|\n| 3种凹槽参数方案 | design.json，cad/variants | 2.4 mm方案因底厚规则排除 |\n| 实体体积减少5.53% | results/cad_metrics.json | 不等于实际称重、整手机构减重 |\n| 三工况刚度代价 | results/comparison.csv | 固定孔壁、等效线弹性材料 |\n| 梁算例与网格复核 | results/solver_verification.json，results/summary.json | 不代表材料或实物验证 |\n\n## 面试时需能解释\n\n1. 凹槽为什么选在中央，哪些接口保持不动？\n2. 为什么去料减少质量，却通常增加柔度？\n3. 四孔全固定会遗漏哪些实际装配因素？\n4. 为什么一阶四面体在粗网格下对弯曲偏硬？\n5. 为什么没有材料许用值时不能声称强度达标？\n6. 深度使用单向公差和剩余底厚检验，各解决什么问题？\n\n简历中按真实理解与实际参与选用上述内容，不写整手自主研发、Workbench求解、量产或实测抓取数据。\n'
evidence=evidence.replace('项目名：基于 OpenHand T42 的夹爪支承顶板轻量化与刚度校核\n\n', '项目名：基于 OpenHand T42 的夹爪支承顶板轻量化与刚度校核\n\n项目性质：开源模型二次设计与零件级数值验证；与四自由度机械臂项目独立列项。\n\n实际工具：CadQuery / OpenCascade、Gmsh、scikit-fem、SciPy。SolidWorks、Workbench 可写入个人技能栏，但本项目未使用它们建模或求解。\n\n## 简历技术版\n\n')
evidence+='''
## 六类能力覆盖情况

| 能力 | 当前完成程度 | 已有证据 | 尚缺的工作 |
|---|---|---|---|
| 机构分析 | 不足 | 识别顶板、手指与安装接口的作用 | 自由度、运动学、欠驱动闭合过程与抓取包络分析 |
| 传动受力 | 未完成整条传力链 | 顶板三种参考载荷及边界条件 | 腱绳张力到关节力矩、指端力的推导，驱动选型与损耗估算 |
| 零件设计 | 较充分，限一个零件 | 参数化四凹槽、三档深度、几何差集检查、STEP/STL 和改制图 | 扩展到其他关键零件；完成工艺确认后的正式图纸 |
| 装配配合 | 部分 | 原始安装接口区域保持不变 | 公差链、配合选取、整机运动干涉和装配检查 |
| 材料与工艺 | 初步 | 名义底厚约束、初拟尺寸公差、统一弹性材料假设 | 材料牌号比较、工艺和打印方向确定、实际成形偏差验证 |
| 结构仿真 | 较充分，限刚度对照 | 二次四面体、三工况、两档网格、独立梁算例和平衡检查 | 实测材料、螺栓与接触、局部应力收敛、强度和疲劳验证 |

因此本版适合突出“参数化零件改型、轻量化方案取舍、有限元刚度验证”，不能据此宣称完成整手结构设计或全部六类能力。

## 技术数字如何解释

- 四凹槽尺寸均为单槽尺寸；1.2 mm 为候选件的名义底厚。2.4 mm 深方案因剩余底厚仅 0.6 mm 被排除，未完成三方案全面有限元优化。
- 候选件实体体积由 30,774.924 mm³ 降至 29,071.647 mm³，减少 5.53%；这是 CAD 体积，不是实测质量或整手减重。
- 三种载荷为预设的零件级参考工况，尚未由完整手指及腱绳静力分析导出。弯矩工况每侧采用力臂 24.9 mm 的座面力偶，左右两侧力矩方向相反。
- 柔度 C = Fᵀu。最大柔度增幅 8.20% 对应同载荷模式下等效刚度下降约 7.58%，不能写成刚度提高或强度提高。
- 0.1933 / 0.2031 mm 是弯矩工况网格角点最大位移采样值，不是完整二次位移场的严格全局最大值。
- 网格目标尺寸由 3.0 mm 减至 2.4 mm；21,231 / 32,642 为候选件单元数。所有对照工况柔度变化最大约 0.650504%，向上取整报告为 ≤ 0.66%。
- 梁算例 1.93% 是数值结果与含剪切梁公式的差异，不是实物误差。两档网格复核不证明局部峰值应力收敛。
- 材料使用 E = 2000 MPa、ν = 0.35 的均质各向同性假设，尚未对应经实测标定的材料牌号。孔壁全固定会忽略连接与支承柔性。
- 改制图提出凹槽深度 1.8 +0/-0.15 mm、其他非配合凹槽尺寸 ±0.15 mm，并单独检验实际底厚 ≥ 1.2 mm；这些是待工艺验证的设计评审要求。

## 面试延伸追问

1. 为什么撑开工况的角点最大位移略降，整体柔度仍增加？两者衡量的对象有什么不同？
2. 为什么四孔全固定和各向同性材料假设可能影响预测精度？下一步如何用实物位移测试修正？
3. 10% 柔度增幅和 1.2 mm 名义底厚是本项目预设筛选规则，如何根据实际产品需求重新设定？
4. 当前设计中哪些来自 Yale OpenHand，哪些属于新增改型与验证工作？
'''
(ROOT/'docs'/'简历与证据.md').write_text(evidence,encoding='utf-8')
print(str(OUT/'T42-结构设计作品集.pdf'))
