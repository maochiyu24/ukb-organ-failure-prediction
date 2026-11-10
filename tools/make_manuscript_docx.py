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
make_docx.py — 将 all913/manuscript 的 Markdown 汇编为单个 Word 文档
====================================================================
组成: 标题页 → 摘要 → Introduction → Methods → Results → Discussion
      → Table 1(真实 Word 表格) → Figures 1–5(嵌入 PNG + 图注) → 图表清单 → 作者备注(附录, 非投稿用)
样式: Times New Roman 12 pt, 1.5 倍行距, 两端对齐; 各级标题加粗; 主要章节分页
输出: result/all913/manuscript/Manuscript_all913.docx
"""
import os
import re
import glob
import numpy as np
import pandas as pd
import pypdfium2 as pdfium
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION

BASE = _PROJECT + '/result/all913'
MD = f'{BASE}/manuscript'
FIG = f'{BASE}/fig'
TAB = f'{BASE}/table'
TMP = '/tmp/all913_docx'
os.makedirs(TMP, exist_ok=True)

doc = Document()
st = doc.styles['Normal']
st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.paragraph_format.line_spacing = 1.5
st.paragraph_format.space_after = Pt(6)
for s in doc.sections:
    s.top_margin = s.bottom_margin = Cm(2.5)
    s.left_margin = s.right_margin = Cm(2.5)


def add_inline(par, text):
    """解析 **粗体** / *斜体* / `代码`"""
    text = text.replace('\\', '')
    for tok in re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)', text):
        if not tok:
            continue
        if tok.startswith('**') and tok.endswith('**'):
            r = par.add_run(tok[2:-2]); r.bold = True
        elif tok.startswith('*') and tok.endswith('*'):
            r = par.add_run(tok[1:-1]); r.italic = True
        elif tok.startswith('`') and tok.endswith('`'):
            r = par.add_run(tok[1:-1]); r.font.name = 'Courier New'; r.font.size = Pt(10)
        else:
            par.add_run(tok)
    return par


def add_heading(text, level):
    sizes = {1: 16, 2: 14, 3: 12.5, 4: 12}
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14 if level <= 2 else 10)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(re.sub(r'[*`]', '', text)); r.bold = True; r.font.size = Pt(sizes.get(level, 12))
    return p


def add_md_table(rows):
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = 'Table Grid'
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].text = ''
            par = cells[j].paragraphs[0]
            par.paragraph_format.line_spacing = 1.0
            add_inline(par, val.strip())
            for r in par.runs:
                r.font.size = Pt(9)
                if i == 0:
                    r.bold = True
    return t


def add_markdown_file(path, skip_h1=False):
    lines = open(path).read().split('\n')
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1; continue
        if ln.startswith('|') and i + 1 < len(lines) and set(lines[i + 1].replace('|', '').strip()) <= set('-: '):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c for c in lines[i].strip().strip('|').split('|')]
                if not set(''.join(cells).replace(' ', '')) <= set('-:'):
                    rows.append(cells)
                i += 1
            if rows:
                add_md_table(rows)
            continue
        m = re.match(r'^(#{1,4})\s+(.*)$', ln)
        if m:
            lvl = len(m.group(1))
            if not (skip_h1 and lvl == 1):
                add_heading(m.group(2), lvl)
            i += 1; continue
        m = re.match(r'^([-*])\s+(.*)$', ln)
        if m:
            p = doc.add_paragraph(style='List Bullet'); add_inline(p, m.group(2)); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.*)$', ln)
        if m:
            p = doc.add_paragraph(style='List Number'); add_inline(p, m.group(2)); i += 1; continue
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_inline(p, ln.strip()); i += 1


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ---------------- 1. 标题页 ----------------
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('Pre-clinical multi-domain profiling for the long-horizon prediction\nof severe organ failure: a UK Biobank cohort study with external validation')
r.bold = True; r.font.size = Pt(16)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('Short title: Multi-domain prediction of severe organ failure')
r.italic = True; r.font.size = Pt(12)
for txt in ['Authors and affiliations: [to be completed]',
            'Correspondence: [to be completed]',
            'UK Biobank Application ID: [to be completed]',
            'Word count (main text): ~5,900; Tables: 1; Figures: 5; Supplementary tables: S1-S7; Supplementary figures: S1-S4']:
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_inline(p, txt)
page_break()

# ---------------- 2. 摘要 + 正文 ----------------
add_markdown_file(f'{MD}/00_Title_Abstract.md', skip_h1=True)
page_break()
for f in ['01_Introduction.md', '02_Methods.md', '03_Results.md', '04_Discussion.md']:
    add_markdown_file(f'{MD}/{f}')
    page_break()

# ---------------- 3. Table 1 (真实表格) ----------------
add_heading('Table 1', 1)
raw = pd.read_excel(f'{TAB}/Table1.xlsx', header=None)
title = str(raw.iloc[0, 0])
p = doc.add_paragraph(); add_inline(p, f'**{title}**')
body = raw.iloc[1:].copy()
rows = [[str(v) if pd.notna(v) else '' for v in body.iloc[i].tolist()] for i in range(len(body))]
t = add_md_table(rows)
page_break()

# ---------------- 4. Figures 1-5 (嵌入) ----------------
add_heading('Figures', 1)
CAPTIONS = {}
cap_txt = open(f'{MD}/05_Figures_Tables_and_Captions.md').read()
for m in re.finditer(r'\*\*(Fig\.\s*S?\d+)\.\s*(.*?)\*\*(.*?)(?=\n\n)', cap_txt, re.S):
    label = re.sub(r'\s+', ' ', m.group(1)).strip()
    title = re.sub(r'\s+', ' ', m.group(2)).strip().rstrip('.')
    body = re.sub(r'\s+', ' ', m.group(3)).strip()
    CAPTIONS[label] = f'{title}. {body}'.strip()
FIGFILES = [('Fig. 1', 'fig1.pdf'), ('Fig. 2', 'fig2.pdf'), ('Fig. 3', 'fig3.pdf'),
            ('Fig. 4', 'fig4.pdf'), ('Fig. 5', 'fig5.pdf')]
for label, fn in FIGFILES:
    png = f'{TMP}/{fn.replace(".pdf", ".png")}'
    pdfium.PdfDocument(f'{FIG}/{fn}')[0].render(scale=2.0).to_pil().convert('RGB').save(png)
    doc.add_picture(png, width=Cm(16.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    cap = CAPTIONS.get(label, '')
    if '.' in cap:
        head, rest = cap.split('.', 1)
        r = p.add_run(f'{label}. {head}.'); r.bold = True
        p.add_run(rest)
    else:
        r = p.add_run(f'{label}. '); r.bold = True
        p.add_run(cap)
page_break()

# ---------------- 5. 图表清单与图注 ----------------
add_markdown_file(f'{MD}/05_Figures_Tables_and_Captions.md', skip_h1=True)
page_break()

# ---------------- 6. 作者备注(附录) ----------------
add_heading('Appendix. Author notes — not for submission', 1)
add_markdown_file(f'{MD}/06_Consistency_Notes.md', skip_h1=True)

out = f'{MD}/Manuscript_all913.docx'
doc.save(out)
print('saved', out, f'{os.path.getsize(out)/1e6:.2f} MB')
print('paragraphs:', len(doc.paragraphs), '| tables:', len(doc.tables),
      '| images:', len(doc.inline_shapes))
