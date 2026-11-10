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
make_table1_tex.py — Table 1 输出: LaTeX 源码 + 高分辨率矢量/位图(便于粘入 Word)
=================================================================================
产物(输出到 result/all913/table/):
  Table1.tex            独立可编译的 LaTeX(booktabs + pdflscape; XeLaTeX/pdflatex 均可)
  Table1_render.pdf     同版式的矢量 PDF(matplotlib 绘制, 直接插入 Word/PDF)
  Table1_render.png     600 dpi PNG(粘贴 Word 不变形)
格式规范: 负号 U+2212; 区间: 两侧非负用 en dash, 含负值用 " to "; 千分位逗号保留
"""
import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

TAB = _PROJECT + '/result/all913/table'
_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
plt.rcParams.update({'font.family': 'Arial'})

raw = pd.read_excel(f'{TAB}/Table1.xlsx', header=None)
title = str(raw.iloc[0, 0]).strip()
header = [str(v).strip() for v in raw.iloc[1].tolist()]
WRAP = {'No organ failure': 'No organ\nfailure', 'Respiratory failure': 'Respiratory\nfailure',
        'Liver failure/cirrhosis': 'Liver failure/\ncirrhosis', 'Haematological failure': 'Haematological\nfailure',
        'Any organ failure': 'Any organ\nfailure', 'Heart failure': 'Heart\nfailure',
        'Kidney failure': 'Kidney\nfailure', 'Stroke': 'Stroke'}
header_2l = [WRAP.get(h, h) for h in header]
body = [[str(v) if pd.notna(v) else '' for v in raw.iloc[i].tolist()] for i in range(2, len(raw))]
note = body[-1][0] if body[-1][0].startswith('Data are') else ''
if note:
    body = body[:-1]

DASH, MINUS = '\u2013', '\u2212'


def fix_cell(s):
    """把 '−1.10 (−3.07-2.20)' 这类改写为 '−1.10 (−3.07 to 2.20)' / '9.67 (3.77–20.67)'"""
    s = s.strip()
    m = re.match(r'^([-\u2212]?[\d.,]+) \(([-\u2212]?[\d.,]+)[-\u2013]([-\u2212]?[\d.,]+)\)$', s)
    if m:
        a, lo, hi = m.group(1), m.group(2), m.group(3)
        s = f'{a} ({lo}{DASH}{hi})'
    return s.replace('-', MINUS)


# ---------------- LaTeX ----------------
def tex_escape(t):
    return t.replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')


hdr = [('\\makecell{' + tex_escape(h).replace(chr(10), r'\\') + '}') if chr(10) in h else tex_escape(h) for h in header_2l]
rows = [[tex_escape(fix_cell(c)) for c in r] for r in body]
colspec = 'l' + 'c' * (len(hdr) - 1)
tex = [
    r'% Table 1 — compile with XeLaTeX or pdfLaTeX (packages: booktabs, makecell, pdflscape, geometry, caption)',
    r'\begin{landscape}',
    r'\begin{table}[p]',
    r'  \centering',
    r'  \caption{' + tex_escape(title).rstrip('.') + '.}',
    r'  \label{tab:table1}',
    r'  \footnotesize',
    r'  \setlength{\tabcolsep}{3.2pt}',
    r'  \renewcommand{\arraystretch}{1.15}',
    r'  \begin{tabular}{' + colspec + r'}',
    r'    \toprule',
    '    ' + ' & '.join(r'\textbf{' + h + '}' for h in hdr) + r' \\',
    r'    \midrule',
]
for r in rows:
    tex.append('    ' + ' & '.join(r) + r' \\')
tex += [
    r'    \bottomrule',
    r'  \end{tabular}',
    r'  \\[2pt]',
    r'  \begin{minipage}{\linewidth}\footnotesize',
    r'    ' + tex_escape(note),
    r'  \end{minipage}',
    r'\end{table}',
    r'\end{landscape}',
]
open(f'{TAB}/Table1.tex', 'w').write('\n'.join(tex) + '\n')

# ---------------- 矢量 PDF + 600 dpi PNG ----------------
ncol, nrow = len(header), len(rows)
fig_w = 26.2                                    # cm (A4 横向可打印宽度)
col_w = [4.6] + [2.7] * (ncol - 1)
fig_h = 1.30 + 0.56 * nrow + 1.00
fig = plt.figure(figsize=(fig_w / 2.54, fig_h / 2.54))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, sum(col_w)); ax.set_ylim(0, fig_h); ax.axis('off')

x0 = 0.0
xs = []
for w in col_w:
    xs.append(x0); x0 += w
y_title = fig_h - 0.28
ax.text(0, y_title, title.rstrip('.'), fontsize=9.6, fontweight='bold', ha='left', va='center')
y_head = y_title - 0.50
for j, h in enumerate(header_2l):
    ax.text(xs[j] + (0.06 if j == 0 else col_w[j] / 2), y_head, h, fontsize=8.2,
            fontweight='bold', ha='left' if j == 0 else 'center', va='center', linespacing=1.15)
ax.plot([0, sum(col_w)], [y_head - 0.20] * 2, color='black', lw=0.9)
ax.plot([0, sum(col_w)], [y_head + 0.20] * 2, color='black', lw=0.9)
y = y_head - 0.50
for i, r in enumerate(rows):
    yy = y - 0.56 * i
    for j, c in enumerate(r):
        c2 = fix_cell(c)
        ax.text(xs[j] + (0.06 if j == 0 else col_w[j] / 2), yy, c2, fontsize=8.0,
                ha='left' if j == 0 else 'center', va='center')
y_bot = y - 0.56 * (nrow - 1) - 0.34
ax.plot([0, sum(col_w)], [y_bot + 0.10] * 2, color='black', lw=0.9)
ax.text(0, y_bot - 0.28, note, fontsize=7.2, ha='left', va='center')

fig.savefig(f'{TAB}/Table1_render.pdf')
fig.savefig(f'{TAB}/Table1_render.png', dpi=600)
plt.close(fig)
from PIL import Image
im = Image.open(f'{TAB}/Table1_render.png')
print(f'saved Table1.tex | Table1_render.pdf | Table1_render.png ({im.size[0]/600*2.54:.1f} x {im.size[1]/600*2.54:.1f} cm)')
print('rows:', nrow, 'cols:', ncol)
