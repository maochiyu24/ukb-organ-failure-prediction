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
"""Fig5C/D 亚组森林 (v906 v3): JAMA 左文本分栏布局 — 扁长比例/组首行器官/无 y 刻度
Fig5C = Age 亚组 C-index; Fig5D = Sex 亚组 C-index
附图: FigS5_AUC_Age / FigS5_AUC_Sex (AUC 同布局)

v3 相对 v2:
- 比例: 整图更宽更扁 (宽 ~17-18 cm, 高 ~9.5-11 cm), 代替 v2 的 ~13.4 cm 高
- 器官名只在每组首行显示 (bold), 第二行该格留空 (Lung 单行则在首行)
- 彻底隐藏 y 轴刻度数字: axF.set_yticks([])
- 参考线 0.5/0.8 只贯穿数据区 (不越过表头带/图例)
- 保留: 深/浅蓝两亚组、灰 CI、隔行底纹贯穿两区、表头+下划线、点白描边、
  数值 3 位小数不重叠、图例简洁、数据零改动、Arial、600 dpi、无面板字母
"""
import os
import numpy as np, pandas as pd
import matplotlib; import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D

FD = _PROJECT + '/.cache/fonts'
for fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    p = os.path.join(FD, fn)
    if os.path.exists(p):
        fm.fontManager.addfont(p)
COMPACT = os.environ.get('FS5_COMPACT', '0') == '1'
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 11,
    'axes.labelsize': 12, 'legend.fontsize': 10.5,
    'xtick.labelsize': 7.2 if COMPACT else 10.5, 'ytick.labelsize': 7.2 if COMPACT else 10.5,
    'figure.dpi': 600, 'savefig.dpi': 600,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.05,
    'axes.linewidth': 0.6, 'grid.linewidth': 0.35, 'axes.grid': False,
})
OUT = _PROJECT + '/result/result906/panels'
OUTS = _PROJECT + '/result/result906/figures_supp'
res = pd.read_csv(os.path.join(_PROJECT, 'cache', 'subgroup_merge_metrics.csv'))
ORDER = ['Heart', 'Lung', 'Liver', 'Kidney', 'Hematologic', 'Stroke', 'Any organ failure']

# 配色: 两亚组深/浅蓝 (统一)
DEEP = '#1F4E79'
LIGHT = '#8DB4E2'
CI_GRAY = '#9A9A9A'          # 柔和灰 CI
SHADE = '#F2F5F9'            # 隔行浅底纹
SEP = '#B8B8B8'              # 器官分隔线
HDR_LINE = '#333333'         # 表头下划线

# 扁长比例: 宽约 17-18 cm, 高约 9.5-11 cm (figsize 英寸 * tight 裁剪后近似)
FSIZE = (3.60, 2.16) if COMPACT else (6.95, 4.00)     # 紧凑: 半宽小图(供 4x2 拼图)
FS_HDR, FS_ROW = (7.2, 7.0) if COMPACT else (11, 10)
FS_AX, FS_VAL, FS_LEG = (8.0, 6.6, 7.4) if COMPACT else (12, 9.5, 10.5)


def build_rows(sub, sg_order):
    """按 Organ/Subgroup 顺序构建行; 缺失亚组如实省略."""
    sub = sub.sort_values(
        'Organ', key=lambda s: pd.Categorical(s, ORDER).codes
    ).reset_index(drop=True)
    rows = []
    for org in ORDER:
        osub = sub[sub['Organ'] == org]
        if not len(osub):
            continue
        for sg in sg_order:
            r = osub[osub['Subgroup'] == sg]
            if not len(r):
                continue
            r = r.iloc[0]
            rows.append(r)
    return rows


def nice_lims(vals, vmin, vmax, step=0.05, pad_lo=0.03, pad_hi=0.075):
    """由数据 lo/hi 算自适应 xlim: 含 0.5 参考; pad_hi 预留数值标注宽."""
    lo = min(min(vals), vmin, 0.5) - pad_lo
    hi = max(max(vals), vmax, 0.5) + pad_hi
    lo_b = np.floor(lo / step) * step
    hi_b = np.ceil(hi / step) * step
    return lo_b, hi_b


def make_ticks(lo_b, hi_b, step=0.05):
    if (hi_b - lo_b) > 0.5:
        step = 0.1
    start = np.ceil(lo_b / step) * step
    t = np.arange(start, hi_b + 1e-9, step)
    return np.round(t, 2)


def draw(sub, metric, fname, out, sg_label_map, title_metric, disp_map=None):
    """sub: 已含目标亚组的行; metric in Cindex/AUC."""
    sg_order = list(sg_label_map.keys())
    lo_col = f'{metric[0]}_lo'
    hi_col = f'{metric[0]}_hi'
    rows = build_rows(sub, sg_order)
    n = len(rows)

    # 数据
    m = np.array([r[metric] for r in rows])
    lo = np.array([r[lo_col] for r in rows])
    hi = np.array([r[hi_col] for r in rows])
    nn = np.array([r['n'] for r in rows], dtype=int)
    ne = np.array([r['n_event'] for r in rows], dtype=int)
    orgs = [r['Organ'] for r in rows]
    sgs = [r['Subgroup'] for r in rows]

    # 自适应 x 范围
    xlo, xhi = nice_lims(np.concatenate([lo, hi]), m.min(), m.max())
    ticks = make_ticks(xlo, xhi)

    # y 位置: row 0 = top
    y = np.arange(n)[::-1].astype(float)   # row0 -> n-1
    HDR = 1.05                             # 表头 + 图例带高度 (压缩)
    ytop = n + HDR
    ybot = -0.75

    # ---- 布局: 左文本列 + 右森林, 无缝隙, 共享 ylim ----
    fig = plt.figure(figsize=FSIZE)
    wr = [1.0, 1.0] if COMPACT else [0.74, 1.0]
    gs = fig.add_gridspec(1, 2, width_ratios=wr, wspace=0.0,  # 字体放大后左文本列加宽
                          left=0.0, right=0.99, top=0.985, bottom=0.105)
    axT = fig.add_subplot(gs[0, 0])
    axF = fig.add_subplot(gs[0, 1])
    axT.set_xlim(0, 1)
    axT.set_ylim(ybot, ytop)
    axF.set_xlim(xlo, xhi)
    axF.set_ylim(ybot, ytop)
    for a in (axT, axF):
        a.spines['top'].set_visible(False)
        a.tick_params(left=False, right=False)
    axT.axis('off')
    axF.spines['left'].set_visible(False)
    axF.spines['right'].set_visible(False)
    axF.set_yticks([])          # ★ 彻底隐藏 y 轴刻度数字 (0/2/4/6 …)

    # ---- 隔行底纹 (贯穿两区) ----
    for i in range(n):
        if i % 2 == 0:
            axT.axhspan(y[i] - 0.5, y[i] + 0.5, color=SHADE, zorder=0, lw=0)
            axF.axhspan(y[i] - 0.5, y[i] + 0.5, color=SHADE, zorder=0, lw=0)

    # ---- 左文本列: 表头 + 下划线 ----
    hy = n + 0.60
    if COMPACT:
        hdr = [('Organ', 0.0, 'left'), ('Subgroup', 0.55, 'left'), ('n (ev.)', 0.99, 'right')]
        X_SG, X_N = 0.55, 0.99
    else:
        hdr = [('Organ', 0.0, 'left'), ('Subgroup', 0.44, 'left'), ('n (events)', 0.97, 'right')]
        X_SG, X_N = 0.44, 0.97
    for txt, x, ha in hdr:
        axT.text(x, hy, txt, ha=ha, va='center', fontsize=FS_HDR, fontweight='bold', zorder=5)
    # 表头下划线 (贯穿左右两区)
    axT.axhline(n - 0.5, color=HDR_LINE, lw=0.8, zorder=5)
    axF.axhline(n - 0.5, color=HDR_LINE, lw=0.8, zorder=5)

    # ---- 左文本列: 数据行 (器官名只在组首行) ----
    for i in range(n):
        yi = y[i]
        if i == 0 or orgs[i] != orgs[i - 1]:
            # 组首行: 器官名加粗显示
            axT.text(0.0, yi, orgs[i], ha='left', va='center', fontsize=FS_ROW,
                     fontweight='bold', zorder=5)
        # 亚组名与 n(events) 每行显示
        axT.text(X_SG, yi, (disp_map or {}).get(sgs[i], sgs[i]), ha='left', va='center', fontsize=FS_ROW, zorder=5)
        axT.text(X_N, yi, f'{nn[i]} ({ne[i]})', ha='right', va='center', fontsize=FS_ROW, zorder=5)
        if i > 0 and orgs[i] != orgs[i - 1]:
            # 器官分隔线 (贯穿两区)
            ya = (y[i - 1] + y[i]) / 2
            axT.axhline(ya, color=SEP, lw=0.5, ls=':', zorder=3)
            axF.axhline(ya, color=SEP, lw=0.5, ls=':', zorder=3)

    # ---- 森林: CI 线 + 点 ----
    for i in range(n):
        yi = y[i]
        axF.plot([lo[i], hi[i]], [yi, yi], color=CI_GRAY, lw=1.5,
                 zorder=3, solid_capstyle='round')
        c = DEEP if sgs[i] == sg_order[0] else LIGHT
        axF.scatter(m[i], yi, s=52, color=c, zorder=4, edgecolors='white', linewidth=0.9)

    # ---- 参考线 (只贯穿数据区, 不越表头带/图例) ----
    ymin_frac = (-0.5 - ybot) / (ytop - ybot)
    ymax_frac = (n - 0.5 - ybot) / (ytop - ybot)
    axF.axvline(0.5, color='#7A7A7A', ls='--', lw=0.9, alpha=0.9,
                ymin=ymin_frac, ymax=ymax_frac, zorder=1)
    axF.axvline(0.8, color='#BABABA', ls=':', lw=0.9, alpha=0.95,
                ymin=ymin_frac, ymax=ymax_frac, zorder=1)

    # ---- x 轴 ----
    axF.set_xticks(ticks)
    axF.set_xlim(xlo, xhi)
    axF.set_xlabel(f'{title_metric} (95% CI)', fontweight='bold', fontsize=FS_AX)

    # ---- 右侧数值标注 (3 位小数) ----
    label_x = max(hi) + 0.012
    for i in range(n):
        axF.text(label_x, y[i], f'{m[i]:.3f}', ha='left', va='center',
                 fontsize=FS_VAL, color='#333333', zorder=6, clip_on=False)

    # ---- 图例 (置于森林区顶部表头带内, 不遮挡数据) ----
    handles = [
        Line2D([0], [0], marker='o', ls='', color=DEEP, ms=7, mec='white', mew=0.8,
               label=(disp_map or {}).get(sg_order[0], sg_order[0])),
        Line2D([0], [0], marker='o', ls='', color=LIGHT, ms=7, mec='white', mew=0.8,
               label=(disp_map or {}).get(sg_order[1], sg_order[1])),
    ]
    axF.legend(handles=handles, frameon=False, fontsize=FS_LEG, loc='upper right',
               handletextpad=0.4, labelspacing=0.25, bbox_to_anchor=(1.0, 1.005),
               ncol=2, columnspacing=1.0)

    fig.savefig(f'{out}/{fname}.pdf', dpi=600)
    fig.savefig(f'{out}/{fname}.png', dpi=600)
    plt.close(fig)

    from PIL import Image
    im = Image.open(f'{out}/{fname}.png')
    print(f'{fname}: rows={n}  xlim=({xlo:.2f},{xhi:.2f})  '
          f'size={im.size[0]/600*2.54:.1f}x{im.size[1]/600*2.54:.1f}cm')


# ================= Age (Fig5C + AUC) =================
age = res[res.Subgroup.isin(['Age<60', 'Age>=60'])].copy()
AGE_MAP = {'Age<60': DEEP, 'Age>=60': LIGHT}
AGE_DISP_C = {'Age<60': '<60', 'Age>=60': '\u226560'}   # 紧凑版短标签(仅显示)
if COMPACT:
    draw(age, 'AUC', 'FigS5_AUC_Age_compact', OUTS, AGE_MAP, 'AUC', disp_map=AGE_DISP_C)
else:
    draw(age, 'Cindex', 'Fig5C', OUT, AGE_MAP, 'C-index')
    draw(age, 'AUC', 'FigS5_AUC_Age', OUTS, AGE_MAP, 'AUC')

# ================= Sex (Fig5D + AUC) =================
sex = res[res.Subgroup.isin(['Female', 'Male'])].copy()
SEX_MAP = {'Female': DEEP, 'Male': LIGHT}
if COMPACT:
    draw(sex, 'AUC', 'FigS5_AUC_Sex_compact', OUTS, SEX_MAP, 'AUC')
else:
    draw(sex, 'Cindex', 'Fig5D', OUT, SEX_MAP, 'C-index')
    draw(sex, 'AUC', 'FigS5_AUC_Sex', OUTS, SEX_MAP, 'AUC')

print('DONE')
