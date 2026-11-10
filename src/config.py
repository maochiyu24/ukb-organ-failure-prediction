# -*- coding: utf-8 -*-
"""
OF823 重构项目 - 全局配置
================================
参考 ZS（UKB 多组学抑郁）的区域划分与特征选择流程，
重构 OF（UK Biobank 五器官衰竭多组学分析）：
  - 区域划分外部验证：England(Region=1) 训练，Scotland(Region=2)+Wales(Region=3) 外部验证
  - 特征选择：Spearman 聚类去冗余 -> 单特征 AUC -> SHAP+TotalGain 综合重要性
              -> top90% 累计增益 -> DeLong 顺序前向选择
  - 建模：LightGBM（Region==1 训练 + 5 折 CV + Region 2/3 外部验证）

运行环境：
  python (conda env with packages in requirements.txt)
  export PYTHONPATH=$PROJECT/envs_of_site:$PYTHONPATH  # optional, if scikit-survival is installed to a local path
"""

import os

# ==================== 路径(环境变量驱动) ====================
# 项目根: 其下应有 xm/(UKB 衍生数据) 与 result/(分析输出); 默认取本仓库的上级目录
BASE_DIR = os.environ.get('UKB_PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
XM_DIR = os.environ.get('UKB_XM_DIR', os.path.join(BASE_DIR, 'xm'))
CODE_DIR = SRC_DIR
# 分析输出目录(可独立指定; 默认 BASE_DIR/result/of903, 与原项目布局一致)
RESULT_DIR = os.environ.get('OF_RESULT_DIR', os.path.join(BASE_DIR, 'result', 'of903'))
# incident-only 模式(本论文使用): 诊断矩阵值 1=阳性, 2=prevalent/首年事件→排除, 0=阴性
INCIDENT_ONLY = os.environ.get('OF_INCIDENT_ONLY', '1') == '1'

# 器官标签的 ICD 定义 (of902: 六系统"严重器官事件", 中长期预警叙事)
#   heart=I50(心衰; 剔 I13 心肾复合/I97 操作后) | lung=J96(呼衰)
#   liver=K72(肝衰竭)+K74(肝硬化; 剔 K70 酒精性作敏感性/K71/K91 操作后)
#   renal=N17+N19(急性/未特指肾衰; 剔 N99 操作后) | hemat=D65+D68(凝血)
#   brain=I60-I64(卒中, UKB 官方算法: 缺血 I63、出血 I60-I62; 剔 G45/S06/I69)
ORGAN_ICD = {
    'heart': ['I50'],
    'lung':  ['J96'],
    'liver': ['K72', 'K74'],
    'renal': ['N17', 'N19'],
    'hemat': ['D65', 'D68', 'D69'],   # D69 紫癜/血小板减少 (SOFA 凝血, 2026-09 用户确认)
    'brain': ['I60', 'I61', 'I62', 'I63', 'I64'],
}

# 原始数据
OF_DATA_DIR = os.path.join(XM_DIR, 'OF')
ZS_DATA_DIR = os.path.join(XM_DIR, 'ZS', '8.7', 'data')
COUNTRY_FILE = os.path.join(ZS_DATA_DIR, 'participant_country_classification.csv')
DIAG_MATRIX = os.path.join(ZS_DATA_DIR, 'all_icd_f_group_1000_25y_instance0.csv')

# 各模态数据文件（OF 项目）
MODALITY_FILES = {
    'proteome': os.path.join(OF_DATA_DIR, 'data', 'organ_failure.csv'),          # 53k 蛋白组（含 Region）
    'metabolome': os.path.join(OF_DATA_DIR, '3.3', 'data', 'organ_failure.csv'), # 274k 代谢组（无 Region）
    'prs':       os.path.join(OF_DATA_DIR, '3.3', 'data', 'organ_failure_prs.csv'),      # 502k PRS
    'brain':     os.path.join(OF_DATA_DIR, '3.9', 'data', 'organ_failure_brain.csv'),    # 65k 脑影像
    'history':   os.path.join(OF_DATA_DIR, '3.9', 'data', 'organ_failure_his.csv'),      # 502k 家族史
    'lifestyle': os.path.join(OF_DATA_DIR, '3.9', 'data', 'organ_failure_life.csv'),     # 502k 生活方式
    'psych':     os.path.join(OF_DATA_DIR, '3.9', 'data', 'organ_failure_psy.csv'),      # 502k 心理
    # 血生化（来自 ZS 数据体系，无器官衰竭标签，prep 时从 organ_failure.csv 合并）
    'blood':     os.path.join(ZS_DATA_DIR, '..', 'data_pro', 'Blood_biochemistry_instance0_ml_pro.csv'),
}

# 标签列（六系统 + 任意 + 多系统负担）
LABEL_COLUMNS = ['liver_failure', 'lung_failure', 'heart_failure',
                 'renal_failure', 'hemat_failure', 'brain_failure',
                 'organ_failure']

# 器官简称（用于文件命名）
ORGAN_SHORT = {
    'liver_failure': 'liver', 'lung_failure': 'lung', 'heart_failure': 'heart',
    'renal_failure': 'renal', 'hemat_failure': 'hemat', 'brain_failure': 'brain',
    'organ_failure': 'organ',
}

# ==================== 区域划分（与 ZS 一致） ====================
REGION_TRAIN = [1]        # England
REGION_TEST  = [2, 3]     # Scotland + Wales
COUNTRY_MAP = {'England': 1, 'Scotland': 2, 'Wales': 3}

# ==================== LightGBM 参数（与 ZS ranking 一致） ====================
LGB_PARAMS = {
    'boosting_type': 'gbdt',
    'learning_rate': 0.01,
    'n_estimators': 300,
    'num_leaves': 31,
    'class_weight': 'balanced',
    'subsample': 0.7,
    'verbosity': -1,
}

# ranking 单特征 AUC 的 CV
RANK_CV = {'n_splits': 10, 'shuffle': True, 'random_state': 42}

# 层次聚类去冗余阈值（距离阈值，对应 |rho| > 0.5 合并）
CLUSTER_DISTANCE_THRESHOLD = 0.5

# 综合重要性累计增益阈值
TOP_GAIN_PROP = 0.9

# DeLong 前向选择显著性阈值
DELONG_P = 0.05
# 前向选择：候选上限 100；至少评估 50 个特征（50 轮内不提前终止），
# 之后连续 FORWARD_SELECTION_STOP 个不显著才提前终止
FORWARD_SELECTION_MAX = 100
FORWARD_SELECTION_MIN = 50
FORWARD_SELECTION_STOP = 5

# ==================== 模型训练（与 ZS model 一致） ====================
# ==================== 模态级调参（每模态一套统一参数） ====================
MODEL_PARAM_GRID = {
    'n_estimators': [100, 200, 300],
    'learning_rate': [0.01, 0.1, 0.2],
    'num_leaves': [31, 50, 100],
    'min_child_samples': [20, 50],
    'class_weight': ['balanced', None],
}
MODEL_CV = {'n_splits': 3, 'shuffle': True, 'random_state': 42}
N_JOBS = 28   # of902: 全程 <=28 核 (用户限制 30)
# 并行预算：最多 20 核 -> 同时 2 个器官 × 每任务 10 线程
N_JOBS_RANKING = 10
N_ORGAN_PARALLEL = 2
OPENBLAS_THREADS = 10

# 聚类去冗余仅用于高维组学模态；低维模态保留全部特征（避免信息损失）
REDUNDANCY_MODALITIES = {'proteome', 'metabolome', 'brain'}

# ==================== 子目录 ====================
SUBDIRS = {
    'prep':    '01_prep',
    'ranking': '02_ranking',
    'model':   '03_model',
    'fusion':  '04_fusion',
}


def ensure_dirs():
    for sub in SUBDIRS.values():
        os.makedirs(os.path.join(RESULT_DIR, sub), exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
