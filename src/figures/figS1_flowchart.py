# -*- coding: utf-8 -*-
# --- GitHub-release path bootstrap (auto-generated) ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if not _os.path.exists(_os.path.join(_SRC, 'config.py')):
    _SRC = _os.path.dirname(_os.path.abspath(__file__))
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)
_PROJECT = _os.environ.get('UKB_PROJECT_ROOT', _os.path.dirname(_SRC))
# ------------------------------------------------------
"""
figS1_flowchart.py — FigS1 研究流程图 (v4: 编辑终审版)
=====================================================
按专业编辑意见实施:
  1) 七级字号体系(9.5/10.0/8.5/9.0/7.5/10.5/7.2),取代原先 13 种字号
  2) 数据域块改为「两列 × 4 行 标签/计数网格」(10.0 pt, 计数右对齐加粗),标题 10.5 bold
  3) 几何: 顶行左对齐网格(0.70/15.70), 融合/中介等宽对称(消除汇合干偏离中心 1.15 cm)
  4) 行距硬约束: pitch ≥ 1.20 × 最大字号; 画幅 16.4 × 19.0 cm, 底部无空白带
  5) 线宽 1.15/1.0, 箭头 mutation_scale 9.0, 圆角 0.16, 母线偏移 0.50 cm
  6) 内容精简: "First-year organ event only"; 结局行改 "six systems: heart, lung, liver, kidney, blood, brain";
     融合框加 "development 26,871 · validation 2,499"; PRS 脚注释义
  7) 印刷规范: pdf.fonttype=42 (Type 42 而非 Type 3), PNG 存 RGB, 灰阶可辨的浅底
输出: figures_supp/FigS1_flow.pdf / .png / .svg
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.path import Path
from PIL import Image

_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
plt.rcParams.update({'font.family': 'Arial', 'figure.dpi': 600,
                     'savefig.dpi': 600, 'savefig.bbox': 'tight',
                     'savefig.pad_inches': 0.03,
                     'pdf.fonttype': 42, 'ps.fonttype': 42})

OUT = _PROJECT + '/result/result906/figures_supp'
os.makedirs(OUT, exist_ok=True)

# ---------------- 版式常量 ----------------
W, H = 16.4, 19.0
ML = MR = 0.70
MAIN_FC, MAIN_EC = '#FFFFFF', '#3A3A3A'
EXCL_FC, EXCL_EC = '#DEDEDE', '#8A8A8A'
SUB_FC, SUB_EC = '#E3E9EF', '#4A6178'
TXT, ARR = '#1A1A1A', '#5A5A5A'
LW_BOX, LW_LINE = 1.15, 1.0
MS = 9.0
CX = W / 2                                   # 8.20
FS_LABEL, FS_KEY, FS_SEC = 9.5, 10.0, 8.5
FS_SUB, FS_SUBN = 8.5, 9.0
FS_EXH, FS_EXI = 9.0, 7.5
FS_DT, FS_DI = 10.5, 9.0      # 域块: 标题明显大于条目
FS_FN = 7.2

GAP = 1.10
H1, H2, HB, HD, HF, HO = 1.80, 1.80, 1.55, 2.70, 1.60, 1.95
TOP = 0.45
y1 = H - TOP - H1
y2 = y1 - GAP - H2
yb = y2 - GAP - HB
yd = yb - GAP - HD
yf = yd - GAP - HF
yo = yf - GAP - HO

fig = plt.figure(figsize=(W / 2.54, H / 2.54))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')


def box(x, y, w, h, lines, fc, ec, sizes, weights):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle='round,pad=0.08,rounding_size=0.16',
                                fc=fc, ec=ec, lw=LW_BOX, zorder=3))
    n = len(lines); pitch = h / (n + 1)
    for i, (ln, sz, wt) in enumerate(zip(lines, sizes, weights)):
        ax.text(x + w / 2, y + h - pitch * (i + 1), ln, ha='center', va='center',
                fontsize=sz, fontweight=wt, color=TXT, zorder=4)


def arr(x0, y0, x1, y1_):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1_), arrowstyle='-|>',
                                 mutation_scale=MS, lw=LW_LINE, color=ARR,
                                 zorder=2, shrinkA=0, shrinkB=0))


def line(x0, y0, x1, y1_):
    ax.plot([x0, x1], [y0, y1_], color=ARR, lw=LW_LINE, zorder=2,
            solid_capstyle='butt')


def elbow(x_from, y_bus, x_to, y_to, r=0.22):
    sx = 1 if x_to > x_from else -1
    verts = [(x_from, y_bus), (x_to - sx * r, y_bus), (x_to, y_bus),
             (x_to, y_bus - r), (x_to, y_to)]
    codes = [Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO]
    ax.add_patch(FancyArrowPatch(path=Path(verts, codes), arrowstyle='-|>',
                                 mutation_scale=MS, lw=LW_LINE, color=ARR,
                                 zorder=2, shrinkA=0, shrinkB=0))


def elbow_up(x_from, y_src, x_to, y_bus, r=0.22):
    sx = 1 if x_to > x_from else -1
    verts = [(x_from, y_src), (x_from, y_bus + r), (x_from, y_bus),
             (x_from + sx * r, y_bus), (x_to, y_bus)]
    codes = [Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO]
    ax.add_patch(FancyArrowPatch(path=Path(verts, codes), arrowstyle='-',
                                 mutation_scale=1, lw=LW_LINE, color=ARR,
                                 zorder=2, shrinkA=0, shrinkB=0))


# 1) 基线 + 排除
B1_X, B1_W = ML, 7.50          # 右缘 = CX(8.20), 干线自框角出发
box(B1_X, y1, B1_W, H1,
    ['UK Biobank participants at', 'baseline assessment (2006\u20132010)', 'n = 502,131'],
    MAIN_FC, MAIN_EC, [FS_LABEL, FS_LABEL, FS_KEY], ['normal', 'normal', 'bold'])
EX_X, EX_W = 9.05, 6.65
box(EX_X, y1, EX_W, H1,
    ['Excluded (n = 9,227)', 'Prevalent organ failure (7,791)',
     'First-year organ event only (1,436)'],
    EXCL_FC, EXCL_EC, [FS_EXH, FS_EXI, FS_EXI], ['bold', 'normal', 'normal'])
arr(B1_X + B1_W, y1 + H1 / 2, EX_X, y1 + H1 / 2)

# 2) 分析队列
A_X, A_W = 4.10, 8.20
box(A_X, y2, A_W, H2, ['Incident-only analysis cohort', 'n = 492,904',
                       'Median follow-up 13.7 years'],
    MAIN_FC, MAIN_EC, [FS_LABEL, FS_KEY, FS_SEC], ['normal', 'bold', 'normal'])
arr(CX, y1, CX, y2 + H2)

# 3) 分支
BR_W = 3.85
BL_X, BR_X = A_X, A_X + A_W - BR_W
box(BL_X, yb, BR_W, HB, ['Development cohort', '(England)', 'n = 437,461'],
    SUB_FC, SUB_EC, [FS_SUB, FS_SUB, FS_SUBN], ['normal', 'normal', 'bold'])
box(BR_X, yb, BR_W, HB, ['External validation', '(Scotland & Wales)', 'n = 55,443'],
    SUB_FC, SUB_EC, [FS_SUB, FS_SUB, FS_SUBN], ['normal', 'normal', 'bold'])
YBUS = yb + HB + 0.50
line(CX, y2, CX, YBUS)
elbow(CX, YBUS, BL_X + BR_W / 2, yb + HB)
elbow(CX, YBUS, BR_X + BR_W / 2, yb + HB)

# 4) 数据域: 两列网格
D_X, D_W = ML, W - ML - MR
box(D_X, yd, D_W, HD, [], MAIN_FC, MAIN_EC, [], [])          # 仅画框
ax.text(CX, yd + HD - 0.45, 'Seven data domains (participants with measurements)',
        ha='center', va='center', fontsize=FS_DT, fontweight='bold',
        color=TXT, zorder=4)
GRID = [('Proteomics', '51,619', 'Lifestyle', '492,901'),
        ('NMR metabolomics', '269,159', 'Family history', '492,904'),
        ('Blood biochemistry', '481,434', 'Psychosocial', '492,904'),
        ('Polygenic risk score', '492,901', '', '')]
y0 = yd + HD - 0.95
for i, (l1, c1, l2, c2) in enumerate(GRID):
    yy = y0 - 0.50 * i
    ax.text(2.65, yy, l1, ha='left', va='center', fontsize=FS_DI, color=TXT, zorder=4)
    ax.text(6.95, yy, c1, ha='right', va='center', fontsize=FS_DI,
            fontweight='bold', color=TXT, zorder=4)
    if l2:
        ax.text(9.45, yy, l2, ha='left', va='center', fontsize=FS_DI, color=TXT, zorder=4)
        ax.text(13.75, yy, c2, ha='right', va='center', fontsize=FS_DI,
                fontweight='bold', color=TXT, zorder=4)
YBUS2 = yb - 0.50
elbow_up(BL_X + BR_W / 2, yb, CX, YBUS2)
elbow_up(BR_X + BR_W / 2, yb, CX, YBUS2)
arr(CX, YBUS2, CX, yd + HD)

# 5) 融合 + 中介(等宽对称)
FW = 7.25
box(ML, yf, FW, HF, ['Multimodal fusion cohort', 'n = 29,370',
                     'development 26,871  \u00b7  validation 2,499'],
    SUB_FC, SUB_EC, [FS_SUB, FS_SUBN, FS_SEC], ['normal', 'bold', 'normal'])
MG_X = 8.45
box(MG_X, yf, FW, HF, ['Causal mediation analysis', '(England; proteomics available)', 'n = 45,893'],
    SUB_FC, SUB_EC, [FS_SUB, FS_SEC, FS_SUBN], ['normal', 'normal', 'bold'])
arr(ML + FW / 2, yd, ML + FW / 2, yf + HF)
arr(MG_X + FW / 2, yd, MG_X + FW / 2, yf + HF)

# 6) 结局
O_W = 13.60
box((W - O_W) / 2, yo, O_W, HO,
    ['Incident severe organ failure during follow-up',
     'heart failure  \u00b7  respiratory failure  \u00b7  liver failure/cirrhosis',
     'kidney failure  \u00b7  haematological failure  \u00b7  stroke',
     'Event counts and incidence rates: Table 1'],
    MAIN_FC, MAIN_EC, [FS_LABEL, FS_SEC, FS_SEC, FS_SEC], ['bold', 'normal', 'normal', 'normal'])
YBUS3 = yf - 0.50
elbow_up(ML + FW / 2, yf, CX, YBUS3)
elbow_up(MG_X + FW / 2, yf, CX, YBUS3)
arr(CX, YBUS3, CX, yo + HO)

# 脚注(3 行, 左对齐)
for i, txt_ in enumerate([
        'The first year after baseline was treated as a lag period; organ events in this period were not counted as incident events.',
        'Exclusion categories are mutually exclusive; organ-event categories are not.',
        'Development and external validation cohorts comprise England and Scotland/Wales, respectively.']):
    ax.text(ML, yo - 0.45 - 0.30 * i, txt_, ha='left', va='top',
            fontsize=FS_FN, color='#555555')

fig.savefig(f'{OUT}/FigS1_flow.pdf')
fig.savefig(f'{OUT}/FigS1_flow.svg')
png = f'{OUT}/FigS1_flow.png'
fig.savefig(png, dpi=600)
plt.close(fig)
Image.open(png).convert('RGB').save(png)
im = Image.open(png)
print(f'saved FigS1_flow.pdf/.png/.svg: {im.size[0]/600*2.54:.2f} x {im.size[1]/600*2.54:.2f} cm')
