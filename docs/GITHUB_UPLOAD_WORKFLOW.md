# GitHub 上传完整工作流（可复现）

> 适用：把一个本地代码目录首次上传到 GitHub，并保证 README/UTF-8/敏感文件/远程地址正确。  
> 本文档来自 `ukb-organ-failure-prediction` 的实际操作流程。

---

## 0. 前置检查

```powershell
$repo = "C:\path\to\your-code"
Set-Location $repo

# 文件数量、总大小、大文件
$files = Get-ChildItem -Recurse -File -Force
"files: $($files.Count)"
"total MB: {0:N2}" -f (($files | Measure-Object Length -Sum).Sum / 1MB)
$files | Where-Object Length -gt 50MB |
  Select-Object FullName, @{n='MB';e={[math]::Round($_.Length/1MB,1)}}
```

必须确认：

- 不含 UK Biobank 个体数据、`.env`、token、私钥、数据库文件；
- 不含 `data/`、`results/`、`cache/`、个人 PDF/Word/Excel（除非明确要公开）；
- 单文件 < 100 MB；整个仓库建议 < 1 GB；
- 已有 `README.md`、`LICENSE`、`.gitignore` 更好。

```powershell
git --version
gh --version        # 如果没有，后续安装
```

---

## 1. 在 GitHub 创建空仓库

登录目标账号，例如 `maochiyu24`：

1. 打开 <https://github.com/new>
2. Repository name：`ukb-organ-failure-prediction`
3. 选择 **Public**（代码可用性声明通常要求公开）
4. **不要**勾选 README/.gitignore/license（本地已有）
5. Create repository

得到远程地址：

```text
https://github.com/maochiyu24/ukb-organ-failure-prediction.git
```

---

## 2. 修复 README 编码（最重要）

### 2.1 不要这样改多语言 README

```powershell
# 危险：Windows PowerShell 可能按 ANSI/GBK 读取 UTF-8 文件，写回后全部乱码
(Get-Content README.md -Raw).Replace("old", "new") | Set-Content README.md
```

### 2.2 推荐用 Python 以 UTF-8 读写

```python
from pathlib import Path

p = Path("README.md")
text = p.read_text(encoding="utf-8")
text = text.replace("https://github.com/OLD-REPO",
                    "https://github.com/maochiyu24/ukb-organ-failure-prediction")
p.write_text(text, encoding="utf-8", newline="\n")
```

或者 PowerShell 明确指定 UTF-8：

```powershell
$text = [System.IO.File]::ReadAllText("README.md", [System.Text.Encoding]::UTF8)
$text = $text.Replace("old", "new")
[System.IO.File]::WriteAllText("README.md", $text, [System.Text.UTF8Encoding]::new($false))
```

### 2.3 README 已经乱码怎么办

- 优先从原始文件/备份恢复；
- 如果无法恢复，按原技术内容重写，不要直接复制乱码；
- 常见乱码通常表现为异常汉字/问号序列，是 UTF-8 被按 GBK 解码造成的；
- 乱码中的 `?` 表示字节已丢失，**不能保证自动逆转**；
- 修完后检查：

```powershell
$py = "C:\path\to\python.exe"
& $py -c "s=open('README.md',encoding='utf-8').read(); print('replacement', s.count(chr(0xfffd))); print('length', len(s))"
```

---

## 3. 替换仓库地址

至少检查：

- `README.md` 的 clone 命令；
- `CITATION.cff` 的 `repository-code`；
- 其他文档中的 `<OLD-REPO>` 占位。

```powershell
Get-ChildItem -Recurse -File -Include *.md,*.cff,*.yml,*.yaml,*.py,*.txt |
  Select-String -Pattern '\[GITHUB-REPO\]|Wang-lab-repo|old-repo'
```

全部替换为：

```text
https://github.com/maochiyu24/ukb-organ-failure-prediction
```

---

## 4. 完善 .gitignore

```gitignore
__pycache__/
*.py[cod]
.ipynb_checkpoints/
*.pkl
*.joblib
.data/
data/
results/
result/
cache/
xm/
*.pdf
*.png
*.docx
*.xlsx
!docs/**/*.png
.venv/
envs_of_site/
.DS_Store
.env
.env.*
*.key
*.pem
*.log
.Rhistory
.Rproj.user/
```

检查暂存区：

```powershell
git init
git add .
git status --short
```

确认没有 `data/`、`result/`、`.env`、token、UKB 原始数据。

---

## 5. 初始化并提交

```powershell
git init
git branch -M main
git config user.name "maochiyu24"
git config user.email "你的GitHub邮箱"

git add .
git status
git commit -m "Initial commit: UKB organ failure prediction code"
```

> `git config` 建议只设置当前仓库，不要随意改全局配置。

---

## 6. GitHub 认证

### 方式 A：GitHub CLI 浏览器授权（推荐）

```powershell
winget install --id GitHub.cli -e --silent --accept-package-agreements --accept-source-agreements
gh auth login --hostname github.com --git-protocol https --web --skip-ssh-key
```

终端会显示一次性代码，例如：

```text
! One-time code: XXXX-XXXX
Open https://github.com/login/device
```

在浏览器打开 <https://github.com/login/device>，登录 `maochiyu24`，输入代码并授权。
完成后检查：

```powershell
gh auth status
```

### 方式 B：手动创建仓库后使用 Git Credential Manager

如果暂时不用 `gh`，先在 GitHub 网页创建空仓库，然后：

```powershell
git remote add origin https://github.com/maochiyu24/ukb-organ-failure-prediction.git
git push -u origin main
```

首次 push 会弹 Git Credential Manager 浏览器登录；不要使用账户密码，使用浏览器登录或 PAT。

---

## 7. 创建远程仓库并推送

```powershell
gh repo create maochiyu24/ukb-organ-failure-prediction `
  --public `
  --description "Code for UK Biobank multi-domain organ failure risk prediction" `
  --source . `
  --remote origin `
  --push `
  --disable-wiki
```

如果仓库已经手动创建，则只需：

```powershell
git remote add origin https://github.com/maochiyu24/ukb-organ-failure-prediction.git
git push -u origin main
```

---

## 8. 验证

```powershell
git remote -v
git status --short
git log --oneline -1
git ls-remote origin
gh repo view maochiyu24/ukb-organ-failure-prediction `
  --json name,url,visibility,defaultBranchRef
```

浏览器检查：

```text
https://github.com/maochiyu24/ukb-organ-failure-prediction
```

确认：

- [ ] 仓库 Public；
- [ ] README 中文/符号正常，无异常乱码字符；
- [ ] 没有数据/密钥；
- [ ] clone 命令和 `CITATION.cff` 地址为新仓库；
- [ ] 远程 `main` 与本地 commit 一致。

---

## 9. 更新论文中的 Code availability

仓库上传后，把稿件中的旧地址替换为：

```text
https://github.com/maochiyu24/ukb-organ-failure-prediction
```

至少检查：

- Methods 中的 GitHub 链接；
- Code availability 小节；
- Cover letter（如果写了代码地址）。

---

## 10. 常见问题

| 问题 | 原因 | 处理 |
|---|---|---|
| README 打开是乱码 | UTF-8 被按 GBK 读取后重写 | 从原始文件恢复；或用 Python `encoding="utf-8"` 重写 |
| `Repository not found` | 仓库未创建/账号不对/私有且未登录 | 先创建空仓库；`gh auth status` 确认账号 |
| `failed to push some refs` | 远程仓库已有 README/提交 | 空仓库创建；或 `git pull --rebase origin main` 后 push |
| `Authentication failed` | GitHub 不再接受账户密码 | 使用 `gh auth login` 或 Git Credential Manager/PAT |
| 文件超过 100 MB | Git 单文件限制 | 从仓库移除；必要时 Git LFS |
| 误提交数据/密钥 | `.gitignore` 不完整 | 先移除并清理历史；不要直接 push |
| PowerShell 改 README 后乱码 | 默认编码不是 UTF-8 | 用 Python 或显式 UTF-8 API |

---

## 11. 本仓库当前信息

- 账号：`maochiyu24`
- 仓库：`ukb-organ-failure-prediction`
- URL：<https://github.com/maochiyu24/ukb-organ-failure-prediction>
- 分支：`main`
- 可见性：Public
