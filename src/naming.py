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
naming.py — 论文显示名统一规范 (of903)
======================================
原则: 图片/表格中的器官、蛋白、代谢物、血液指标一律使用可发表正式名,
      无下划线; 全部图共用本模块保证一致性。

- 器官: Heart / Lung / Liver / Kidney / Hematologic / Stroke / Any system
- 蛋白 (Olink): 标准 HGNC 符号; NTproBNP→NT-proBNP (临床名);
  复合交叉反应名 (A_B) 取主符号 A; 含 ';' 描述取 ';' 前
- 代谢物 (Nightingale): '_'→' '; 'to' 连接词; percentage 语义保留为 (%);
  脂蛋白亚类术语规范化
- 血液指标: '_'→' ' 及常用连字符/希腊字母特例
- 中介名: 去模态前缀后按类转换
"""

ORG_CN = {
    'heart': 'Heart', 'lung': 'Lung', 'liver': 'Liver', 'renal': 'Kidney',
    'hemat': 'Hematologic', 'brain': 'Stroke', 'organ': 'Any organ failure',
}
ORGANS = ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']

MOD_LABEL = {
    'proteome': 'Proteomics', 'metabolome': 'Metabolomics',
    'blood': 'Biochemical measures', 'lifestyle': 'Lifestyle',
    'psych': 'Psychosocial', 'prs': 'PRS', 'history': 'Family history',
    'brain': 'Brain imaging', 'merge': 'Multimodal fusion',
}

# ---- 蛋白特例 (Olink → 显示名) ----
PROTEIN_SPECIAL = {
    'NTproBNP': 'NT-proBNP',
    'HLA_A': 'HLA-A', 'HLA_B': 'HLA-B', 'HLA_C': 'HLA-C',
    'HLA_DRA': 'HLA-DRA', 'HLA_E': 'HLA-E', 'HLA_F': 'HLA-F',
    'HLA_G': 'HLA-G', 'HLA_DQA1': 'HLA-DQA1', 'HLA_DQB1': 'HLA-DQB1',
    'HLA_DRB1': 'HLA-DRB1', 'HLA_DPB1': 'HLA-DPB1',
    'PALM2': 'PALM2-AKAP2',
}

# ---- 代谢物/血液特例 (下划线转空格后仍须特修) ----
# ---- 官方 UKB-Nightingale 325 代谢物表 (Biomarker 简写 + Description 全称) ----
_METAB_TABLE = _PROJECT + '/xm/ZS/data/代谢物325_简写_全称_组_亚组.xlsx'
_METAB_MAP = None  # {核心名小写: (biomarker_display, description)}


def _load_metab_table():
    global _METAB_MAP
    if _METAB_MAP is not None:
        return _METAB_MAP
    _METAB_MAP = {}
    try:
        import pandas as pd
        import re
        d = pd.read_excel(_METAB_TABLE)
        for _, r in d.iterrows():
            desc = str(r['Description']).strip()
            key = re.sub(r'[^a-z0-9 ]', '', desc.lower())
            _METAB_MAP[key] = (str(r['Biomarker']).strip(), desc)
    except Exception:
        pass
    return _METAB_MAP


def _core_key(s):
    import re
    x = re.sub(r'_(to|To)_Total_Lipids.*', '', s)
    x = x.replace('_', ' ').lower()
    return re.sub(r'[^a-z0-9 ]', '', x)


def _norm_metab(s):
    """代谢物长名规范化键 (小写、去下划线、去 percentage 与非字母数字, 折叠空白)"""
    import re
    x = s.replace('_', ' ').lower().replace('percentage', '')
    x = re.sub(r'[^a-z0-9 ]', '', x)
    return ' '.join(x.split())


# 图内长名 -> 简写 override (325 表未覆盖的脂蛋白比率类等; 2026-09 用户要求图上用简称)
_METAB_LONG = {
    'total concentration of branched chain amino acids leucine isoleucine valine': 'Total BCAA',
    'f 3 hydroxybutyrate': '3-Hydroxybutyrate',
    'phospholipids to total lipids in very small vldl': 'PL (%) in very small VLDL',
    'cholesteryl esters to total lipids in large hdl': 'CE (%) in large HDL',
    'cholesteryl esters to total lipids in large ldl': 'CE (%) in large LDL',
    'cholesteryl esters to total lipids in small ldl': 'CE (%) in small LDL',
    'cholesteryl esters to total lipids in idl': 'CE (%) in IDL',
    'triglycerides to total lipids in large ldl': 'TG (%) in large LDL',
    'triglycerides to total lipids in idl': 'TG (%) in IDL',
    'cholesterol to total lipids in large ldl': 'Chol (%) in large LDL',
}


# 脂蛋白比率类规则缩写: 'X-to-total lipids in Y (%)' -> 'ABBR (%) in Y''
_LIPID_COMP = {'Triglycerides': 'TG', 'Cholesteryl esters': 'CE', 'Phospholipids': 'PL',
               'Cholesterol': 'Chol', 'Free cholesterol': 'FC', 'Omega 6 fatty acids': 'n-6 FA'}
_LIPID_SUB = {'chylomicrons and extremely large vldl': 'CM & XL VLDL',
              'extremely large vldl': 'XL VLDL', 'very large vldl': 'XL VLDL',
              'very small vldl': 'XS VLDL', 'medium vldl': 'M VLDL',
              'large vldl': 'L VLDL', 'small vldl': 'S VLDL',
              'very large hdl': 'XL HDL', 'large hdl': 'L HDL',
              'medium hdl': 'M HDL', 'small hdl': 'S HDL',
              'large ldl': 'L LDL', 'medium ldl': 'M LDL', 'small ldl': 'S LDL'}


def _shorten_lipid_ratio(t):
    import re
    m = re.match(r'^(.+?)-to-total lipids in (.+?) \(%\)$', t)
    if not m:
        return None
    comp, subj = m.group(1), m.group(2).lower()
    if comp in _LIPID_COMP and subj in _LIPID_SUB:
        return f'{_LIPID_COMP[comp]} (%) in {_LIPID_SUB[subj]}'
    return None


METAB_SPECIAL = {
    'Glycoprotein Acetyls': 'Glycoprotein acetyls (GlycA)',
    'C Reactive Protein': 'C-reactive protein',
    'Gamma Glutamyltransferase': 'γ-glutamyltransferase',
    'Glucose Lactate': 'Glucose/lactate',
    'Docosahexaenoic Acid': 'Docosahexaenoic acid (DHA)',
    'Cystatin C': 'Cystatin C',
    'Igf 1': 'IGF-1',
    'Ldl Direct': 'LDL cholesterol',
    'Hdl Direct': 'HDL cholesterol',
    'Glycated Haemoglobin Hba1C': 'HbA1c',
}

LOWER_WORDS = {'of', 'in', 'and', 'to', 'for', 'the', 'with', 'as', 'total', 'free', 'very', 'large', 'medium', 'small', 'concentration', 'average', 'degree', 'particles', 'diameter', 'lipids', 'lipoprotein', 'acetyls', 'esters', 'cholesterol', 'triglycerides', 'phospholipids', 'apolipoprotein'}
KEEP_UPPER = {'HDL', 'LDL', 'VLDL', 'IDL'}


def _word(w):
    """单词 Title Case, 连词小写, HDL/LDL 等保留大写; 支持 '-' 连接词"""
    if w.lower() in LOWER_WORDS:
        return w.lower()
    if w.upper() in KEEP_UPPER:
        return w.upper()
    if '-' in w:
        return '-'.join(_word(x) for x in w.split('-'))
    return w.title()


def _title(s):
    ws = s.split()
    if not ws:
        return s
    first = ws[0]
    if '-' in first:
        first = '-'.join(_word(x) if x.lower() in LOWER_WORDS or x.upper() in KEEP_UPPER
                         else x for x in first.split('-'))
        # 段首强制大写
        first = first[0].upper() + first[1:]
    else:
        first = _word(first)
        first = first[0].upper() + first[1:] if first else first
    rest = ' '.join(_word(w) for w in ws[1:])
    return first + (' ' + rest if rest else '')


def protein_name(s):
    """蛋白显示名: 去前缀/描述, 复合取主符号, 特例映射"""
    s = str(s)
    if '__' in s:
        s = s.split('__', 1)[1]
    if ';' in s:
        s = s.split(';')[0]
    if '_' in s and s not in PROTEIN_SPECIAL:
        s = s.split('_')[0]          # Olink 交叉反应复合名取主符号
    return PROTEIN_SPECIAL.get(s, s)


def _words(s):
    for k, v in TERM_FIX.items():
        s = s.replace(k, v)
    return s


def metab_name(s, prefer_short=True):
    """代谢物显示名:
    1) 官方表命中: 描述<=14字符用全称, 否则用官方简写 (Biomarker, _->-)
    2) 未命中(比率类等): 规则转换 (去下划线 Title Case + 特例)"""
    s = str(s)
    if s.startswith(('proteome__', 'metabolome__', 'blood__')):
        s = s.split('__', 1)[1]
    pct = 'percentage' in s.lower()
    tb = _load_metab_table()
    hit = tb.get(_core_key(s))
    if hit:
        biom, desc = hit
        if len(desc) <= 14:
            return desc
        if prefer_short and len(biom) <= 16:
            b = biom.replace('_', '-')
            return b if not pct else b + ' (%)'
        return desc
    # 图内长名 -> 简写 override (未命中 325 表的比率类等)
    _k = _norm_metab(s)
    if _k in _METAB_LONG:
        return _METAB_LONG[_k]
    t = (s.replace('_to_', '-to-').replace('_', ' ')
           .replace('percentage', '').replace('Percentage', ''))
    t = ' '.join(t.split())
    t = _title(t)
    t = METAB_SPECIAL.get(t, t)
    if pct and '(%)' not in t:
        t = t + ' (%)'
    _s = _shorten_lipid_ratio(t)
    if _s:
        return _s
    return t


def blood_name(s):
    return metab_name(s)


def mediator_name(s):
    """中介名: 去 'modality__' 前缀后按类型转换"""
    s = str(s)
    if '__' in s:
        mod, feat = s.split('__', 1)
        if mod == 'proteome':
            return protein_name(feat)
        if mod == 'metabolome':
            return metab_name(feat)
        if mod == 'blood':
            return blood_name(feat)
    return protein_name(s)


def display_name(s, kind='protein'):
    if kind == 'protein':
        return protein_name(s)
    if kind == 'metabolite':
        return metab_name(s)
    if kind == 'mediator':
        return mediator_name(s)
    return str(s).replace('_', ' ')

# ---- lifestyle / prs / history 特征显示 ----
LIFESTYLE_SPECIAL = {
    'time since interview start at which blood pressure screen s shown':
        'Time to BP screen',
    'systolic blood pressure automated reading': 'Systolic BP',
    'diastolic blood pressure automated reading': 'Diastolic BP',
    'townsend deprivation index at recruitment': 'TDI',
    'pulse rate automated reading': 'Pulse rate',
    'waist circumference': 'Waist circumference',
    'hip circumference': 'Hip circumference',
    'body mass index (bmi)': 'BMI',
    'body mass index bmi': 'BMI',
    'sleep duration': 'Sleep duration',
    'smoking status': 'Smoking status',
    'alcohol intake frequency': 'Alcohol intake',
}


def lifestyle_name(s):
    t = s.replace('__', ' ').replace('_', ' ').strip().lower()
    t = ' '.join(t.split())
    return LIFESTYLE_SPECIAL.get(t, ' '.join(t.title().split()))


# UKB 官方 PRS 后缀 -> 展示缩写 (未列出的短后缀原样使用)
_PRS_SUFFIX_CLEAN = {'HBA1C_DF': 'HbA1c', 'LDL_SF': 'LDL', 'HT': 'HTN',
                     'HEIGHT': 'Height', 'EBMDT': 'eBMD'}


def prs_name(s):
    import re
    m = re.search(r'Standard_PRS_for_(.+?)(?:__|$)', s)
    if not m:
        return s.replace('_', ' ')
    # 优先: 原始名自带官方缩写后缀, 如 Standard_PRS_for_...__VTE_
    suf = re.search(r'__([A-Za-z0-9_]+)_$', s)
    if suf:
        raw = suf.group(1)
        if raw in _PRS_SUFFIX_CLEAN:
            return f'PRS-{_PRS_SUFFIX_CLEAN[raw]}'
        if re.fullmatch(r'[A-Z0-9]{1,6}', raw):      # VTE/BMI/AF/HDL/T1D/T2D...
            return f'PRS-{raw}'
    disease = m.group(1).replace('_', ' ').lower()
    abbr = {'hypertension': 'HTN', 'cardiovascular disease': 'CVD',
            'type 2 diabetes': 'T2D', 'coronary artery disease': 'CAD',
            'stroke': 'Stroke', 'atrial fibrillation': 'AF'}
    return f'PRS-{abbr.get(disease, disease.title())}'


def other_name(s, modality):
    if modality == 'lifestyle':
        return lifestyle_name(s)
    if modality == 'prs':
        return prs_name(s)
    if modality == 'history':
        return ' '.join(s.replace('_', ' ').split())
    return ' '.join(s.replace('_', ' ').split())


def full_feature_name(feat):
    """按模态前缀选择显示 (feature 可能带 'modality__' 前缀)"""
    if '__' in feat:
        mod, f = feat.split('__', 1)
        if mod == 'proteome':
            return protein_name(f)
        if mod == 'metabolome':
            return metab_name(f)
        if mod == 'blood':
            return blood_name(f)
        return other_name(f, mod)
    return protein_name(feat)
