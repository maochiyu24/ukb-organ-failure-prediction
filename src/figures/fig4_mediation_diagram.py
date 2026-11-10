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
fig4_ab_beautified.py — Fig4A/B 美化合成版 (左=保护/右=风险, 同一 GDF15 通路)
================================================================================
内容(数值全部来自 of903 中介结果, organ 层面 GDF15):
  Healthy behaviour      -> GDF15 (a, ↓) -> Any organ failure   [ACME<0 保护]
  Psychological distress -> GDF15 (a, ↑) -> Any organ failure   [ACME>0 风险]
增强:
  * A/B 同画布左右对比; 面板内语义小标题 + 极浅底色圆角面板 + 节点柔和投影
  * 路径 a/b 数值; 虚线 c'(直接) 数值; 总效应 c = ACME+ADE 点值
  * 面板底部小字: 样本/事件/暴露单位/E-value(2-unit)
  * 风格与 Fig4A/B 一致: Arial, 圆角节点, 同色系配色 (不覆盖原 Fig4A/B)
输出: result906/panels/Fig4_AB_beautified.pdf/.png
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Ellipse, FancyArrowPatch
import matplotlib.patheffects as pe

_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 9, 'figure.dpi': 600,
    'savefig.dpi': 600, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.05,
    'axes.linewidth': 0.6,
})
OUT = _PROJECT + '/result/result906/panels'
os.makedirs(OUT, exist_ok=True)

# ---------------- 面板几何 (数据坐标: 每面板 0..4.2 x 0..4.5) ----------------
XW, YH = 4.2, 4.5
CX = 1.85
BW, BH = 2.30, 0.66
ELL_W, ELL_H = 2.55, 1.18
ECY = 2.28
ELL_TOP, ELL_BOT = ECY + ELL_H / 2, ECY - ELL_H / 2
EX_B = 3.35                 # Exposure 框下缘
OU_T = 0.90                 # Outcome 框上缘
PAD = 0.07                  # 圆角框外扩(与可见边一致)


def rbox(ax, x, y, w, h, fc, ec, shadow=True):
    if shadow:  # 柔和投影 (右下方偏移)
        ax.add_patch(FancyBboxPatch((x + 0.045, y - 0.045), w, h,
                                    boxstyle='round,pad=0.07,rounding_size=0.10',
                                    fc='#000000', alpha=0.10, lw=0, zorder=1))
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle='round,pad=0.07,rounding_size=0.10',
                                fc=fc, ec=ec, lw=1.8, zorder=3))


def txt(ax, x, y, s, size=9, color='#1F1F1F', weight='normal', ha='center',
        halo=2.0, rot=0):
    t = ax.text(x, y, s, ha=ha, va='center', fontsize=size, fontweight=weight,
                color=color, rotation=rot, zorder=6)
    t.set_path_effects([pe.withStroke(linewidth=halo, foreground='white')])
    return t


def arrow(ax, p0, p1, color, lw=2.0, ms=15, ls='-', rad=0.0, z=5):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>', mutation_scale=ms,
                                 lw=lw, color=color, linestyle=ls, zorder=z,
                                 connectionstyle=f'arc3,rad={rad}'))


def panel(ax, cfg, title, note_lines):
    """cfg: 配色与数值"""
    ax.set_xlim(0, XW); ax.set_ylim(-0.75, YH); ax.axis('off')
    # 面板底色
    ax.add_patch(FancyBboxPatch((0.06, 0.06), XW - 0.12, YH - 0.12,
                                boxstyle='round,pad=0.02,rounding_size=0.10',
                                fc=cfg['bg'], ec='#D9DEE4', lw=0.9, zorder=0))
    # 语义小标题
    txt(ax, CX, YH - 0.24, title, size=10.5, weight='bold', color=cfg['tc'])
    txt(ax, CX, YH - 0.52, cfg['subtitle'], size=7.6, color='#6A6A6A')

    bx0, by0 = CX - BW / 2, EX_B
    rbox(ax, bx0, by0, BW, BH, cfg['exp_fc'], cfg['exp_ec'])
    txt(ax, CX, EX_B + BH / 2 + 0.13, cfg['exp_title'], size=10.5,
        weight='bold', color='#1F1F1F')
    txt(ax, CX, EX_B + BH / 2 - 0.13, cfg['exp_sub'], size=7.6, color='#555555')
    # 椭圆
    ax.add_patch(Ellipse((CX, ECY), ELL_W, ELL_H, fc=cfg['med_fc'],
                         ec=cfg['med_ec'], lw=1.8, zorder=3))
    txt(ax, CX - 0.06, ECY + 0.31, 'GDF15', size=11, weight='bold')
    _d = ax.text(CX + 0.55, ECY + 0.30, cfg['dir'], ha='center', va='center',
                 fontsize=14, fontweight='bold', color=cfg['ac'], zorder=6)
    _d.set_path_effects([pe.withStroke(linewidth=2.2, foreground='white')])
    txt(ax, CX, ECY - 0.10, f"ACME {cfg['acme']}", size=7.6, weight='bold',
        color='#2B2B2B')
    txt(ax, CX, ECY - 0.28, cfg['ci'], size=7.2, color='#5A5A5A')
    txt(ax, CX, ECY - 0.45, f"PM {cfg['pm']}", size=7.6, weight='bold',
        color='#2B2B2B')
    # Outcome 框
    ox0, oy0 = CX - BW / 2, OU_T - BH
    rbox(ax, ox0, oy0, BW, BH, cfg['out_fc'], cfg['out_ec'])
    txt(ax, CX, OU_T - BH / 2, 'Any organ failure', size=9.6, weight='bold',
        color='#1F1F1F')

    # 路径 a (Exposure -> GDF15)
    arrow(ax, (CX, EX_B - PAD), (CX, ELL_TOP - 0.035), cfg['ac'])
    ya = (EX_B + ELL_TOP) / 2 + 0.02
    txt(ax, CX + 0.20, ya, cfg['a_val'], size=8.2, weight='bold',
        color=cfg['ac'], ha='left')
    # 路径 b (GDF15 -> Outcome)
    arrow(ax, (CX, ELL_BOT + 0.01), (CX, OU_T + PAD), cfg['ac'])
    yb = (ELL_BOT + OU_T) / 2 - 0.02
    txt(ax, CX + 0.20, yb, cfg['b_val'], size=8.2, weight='bold',
        color=cfg['ac'], ha='left')
    # 路径 c' (虚线直接效应, 左绕)
    arrow(ax, (bx0 - 0.02, EX_B - PAD), (bx0 - 0.02, OU_T + PAD - 0.02),
          '#8A8A8A', lw=1.4, ms=12, ls=(0, (4, 3)), rad=0.55)
    ymc = (EX_B + OU_T) / 2
    txt(ax, 0.34, ymc, cfg['c_val'], size=7.2, color='#8A8A8A', rot=90)
    # 底部脚注区 (位于框外, 避免压边)
    for i, ln in enumerate(note_lines):
        txt(ax, CX, -0.10 - i * 0.13, ln, size=6.6, color='#777777')


CFG_A = {
    'bg': '#F2F7F4', 'tc': '#1F6B4A',
    'subtitle': 'Protective pathway  \u00b7  Healthy behaviour \u2192 GDF15 \u2193 \u2192 any organ failure',
    'exp_fc': '#D6E4F5', 'exp_ec': '#2E6FA8',
    'med_fc': '#DFF0DB', 'med_ec': '#4E8A43',
    'out_fc': '#D5EAEE', 'out_ec': '#1F7A8C',
    'ac': '#2E6FA8',
    'exp_title': 'Healthy behaviour', 'exp_sub': '5-component score (0\u20135)',
    'dir': '\u2193',
    'acme': '\u22120.0064', 'ci': '(95%CI \u22120.0071, \u22120.0058)', 'pm': '33.8%',
    'a_val': 'a = \u22120.006 (per point)',
    'b_val': 'b = 0.557 (per SD)',
    'c_val': 'c\u2032 = \u22120.0130 (direct)',
    'c_total': 'total effect c = \u22120.0194',
}
CFG_B = {
    'bg': '#FBF3EF', 'tc': '#9C3B2E',
    'subtitle': 'Risk pathway  \u00b7  Psychological distress \u2192 GDF15 \u2191 \u2192 any organ failure',
    'exp_fc': '#F6DCD8', 'exp_ec': '#B0453B',
    'med_fc': '#FCE2CB', 'med_ec': '#D07E2C',
    'out_fc': '#F0DAE8', 'out_ec': '#B2477C',
    'ac': '#B0453B',
    'exp_title': 'Psychological distress', 'exp_sub': '4-component score (0\u20134)',
    'dir': '\u2191',
    'acme': '+0.0024', 'ci': '(95%CI +0.0020, +0.0028)', 'pm': '33.0%',
    'a_val': 'a = +0.003 (per point)',
    'b_val': 'b = 0.565 (per SD)',
    'c_val': 'c\u2032 = +0.0047 (direct)',
    'c_total': 'total effect c = +0.0071',
}

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.9))
for ax, cfg, title, notes in [
        (axes[0], CFG_A, 'A', ['n = 45,718 \u00b7 events 5,524 \u00b7 England',
                               'E-value (2-unit) = 1.48',
                               'total effect c = \u22120.0194 (= ACME + c\u2032)']),
        (axes[1], CFG_B, 'B', ['n = 45,718 \u00b7 events 5,524 \u00b7 England',
                               'E-value (2-unit) = 1.24',
                               'total effect c = +0.0071 (= ACME + c\u2032)'])]:
    panel(ax, cfg, title, notes)
fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005,
                    wspace=0.02)
fig.savefig(f'{OUT}/Fig4_AB_beautified.pdf', dpi=600)
fig.savefig(f'{OUT}/Fig4_AB_beautified.png', dpi=600)
fig.savefig(f'{OUT}/Fig4_AB_beautified.svg')  # AI 导入用(文字转路径)
plt.close(fig)
from PIL import Image
im = Image.open(f'{OUT}/Fig4_AB_beautified.png')
print(f'saved Fig4_AB_beautified: {im.size[0]/600*2.54:.2f} x {im.size[1]/600*2.54:.2f} cm')
