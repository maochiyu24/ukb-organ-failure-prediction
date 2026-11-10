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
compose_figS5.py — 附图 FigS5 整体出图 (4 行 x 2 列, 面板 a–h, 全矢量)
================================================================
  a Heart PPI        | b Kidney PPI
  c Lung PPI         | d Hematologic PPI
  e Liver PPI        | f Stroke PPI
  g AUC forest (Age) | h AUC forest (Sex)
实现: 源文件全部为矢量 PDF(PPI=FigS5_PPI_*.pdf, 森林=FigS5_AUC_*_compact.pdf),
      pypdf 等比缩放/平移合并到一页, 字母 a–h 用 matplotlib 生成透明矢量层叠加。
可调参数: TOTAL_W_CM(总宽) / GAP_X_CM, GAP_Y_CM / LETTER_FS / PPI_ROW_H_CM(None=按列宽自适应)
输出: result906/figures_supp/FigS5.pdf (+ 预览 PNG)
"""
import os
import numpy as np
from pypdf import PdfReader, PdfWriter, Transformation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# ---------------- 可调参数 ----------------
TOTAL_W_CM = 18.0
GAP_X_CM, GAP_Y_CM = 0.35, 0.30
MARGIN_CM = 0.05
LETTER_FS = 12.5
LETTER_DX_PT, LETTER_DY_PT = 3.0, 3.0
LETTER_BAND_CM = 0.36          # 每行顶部预留的字母带高度
TARGET_H_CM = 29.4             # 成图总高上限(A4); None = 不缩放
CELL_ASPECT = 1.25             # PPI 单元格宽/高(1.22≈六图宽高比中位数)
# -----------------------------------------

FS = _PROJECT + '/result/result906/figures_supp'
OUT = f'{FS}/FigS5.pdf'
GRID = [
    [('A', f'{FS}/FigS5_PPI_Heart.pdf'), ('B', f'{FS}/FigS5_PPI_Kidney.pdf')],
    [('C', f'{FS}/FigS5_PPI_Lung.pdf'), ('D', f'{FS}/FigS5_PPI_Hematologic.pdf')],
    [('E', f'{FS}/FigS5_PPI_Liver.pdf'), ('F', f'{FS}/FigS5_PPI_Stroke.pdf')],
    [('G', f'{FS}/FigS5_AUC_Age_compact.pdf'), ('H', f'{FS}/FigS5_AUC_Sex_compact.pdf')],
]
cm2pt = lambda x: x / 2.54 * 72.0
_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)

W = cm2pt(TOTAL_W_CM)
GX, GY, MG = cm2pt(GAP_X_CM), cm2pt(GAP_Y_CM), cm2pt(MARGIN_CM)
COLW = (W - 2 * MG - GX) / 2
BAND = cm2pt(LETTER_BAND_CM)


def page_size(p):
    pg = PdfReader(p).pages[0]
    return float(pg.mediabox.width), float(pg.mediabox.height)


# ---- 计算每格缩放与行高(PPI 行: 统一行高; 森林行: 以列宽为准) ----
# PPI 三行统一行高(取最宽宽高比, 保证不超列宽); 森林行各自按列宽
H_PPI = COLW / CELL_ASPECT          # PPI 三行统一单元格高度
cells, content_h = [], []
for ri, row in enumerate(GRID):
    items = []
    for letter, path in row:
        w, h = page_size(path)
        if ri < 3:
            s = min(COLW / w, H_PPI / h)     # fit-inside, 保持比例
        else:
            s = COLW / w
        items.append((letter, path, s, w * s, h * s))
    cells.append(items)
    content_h.append(H_PPI if ri < 3 else max(it[4] for it in items))
row_h = [c + BAND for c in content_h]
H = 2 * MG + sum(row_h) + GY * (len(GRID) - 1)

# ---- 主页面: 矢量合并 ----
writer = PdfWriter()
page = writer.add_blank_page(width=W, height=H)
letter_pos = []
y_top = H - MG
for ri, row in enumerate(cells):
    rh = row_h[ri]
    y_row = y_top - rh
    ch = content_h[ri]
    for ci, (letter, path, s, sw, sh) in enumerate(row):
        x_cell = MG + ci * (COLW + GX)
        x = x_cell + (COLW - sw) / 2                      # 水平居中
        y = y_row + (ch - sh) / 2                         # 内容在带下方居中
        page.merge_transformed_page(PdfReader(path).pages[0],
                                    Transformation().scale(s).translate(x, y))
        letter_pos.append((letter, x_cell + LETTER_DX_PT,
                           y_row + rh - LETTER_DY_PT))
    y_top = y_row - GY

# ---- 字母层(matplotlib 透明矢量), 与主页同尺寸 ----
fig = plt.figure(figsize=(W / 72, H / 72))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
for letter, lx, ly in letter_pos:
    ax.text(lx, ly, letter, fontsize=LETTER_FS, fontweight='bold',
            family='Arial', ha='left', va='top', color='black')
ov = '/tmp/_figs5_letters.pdf'
fig.savefig(ov, transparent=True)
plt.close(fig)
page.merge_transformed_page(PdfReader(ov).pages[0], Transformation())

if TARGET_H_CM:
    target = cm2pt(TARGET_H_CM)
    if H > target:
        k = target / H
        w2 = PdfWriter()
        p2 = w2.add_blank_page(width=W * k, height=target)
        p2.merge_transformed_page(page, Transformation().scale(k))
        writer, page = w2, p2
        H, W = target, W * k

with open(OUT, 'wb') as f:
    writer.write(f)
print(f'saved {OUT}: {W:.1f}x{H:.1f} pt = {W/72*2.54:.2f}x{H/72*2.54:.2f} cm; '
      f'rows={[round(r/72*2.54,2) for r in row_h]} cm; colw={COLW/72*2.54:.2f} cm')
