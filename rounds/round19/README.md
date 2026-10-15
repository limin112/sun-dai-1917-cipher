# Round 19 复现说明

目标仍是 1917 年六月 0509 / 0511。已验证译文 0 字；本目录提供无损转录审计、统计敏感性与候选表回验，不能把机械通过或小 p 值当作破译。

所有分析和测试仅需 Python 3.10+ 标准库，本轮在 Python 3.14.7 上验证。以下命令从仓库根运行；各 Python 脚本也可用绝对路径从其他目录调用。

## 完整验收（不改证据）

```sh
python3 -B rounds/round19/reproduce.py
```

这会运行全部 Round 19 回归测试，将两个分析结果重算到临时目录，再逐字节比较已保存 JSON，并检查本轮 MANIFEST 的文件覆盖及 SHA-256。默认统计规模为 4,000 次置换 / 每项 16,000 次删除抽样，通常需要约一分钟。随机数与浮点结果的逐字节复现以相同 Python 运行环境为准；跨版本差异应检查，不要自动覆盖。

## 分项命令

```sh
python3 -B -m unittest discover -s rounds/round19/tests -v
python3 -B rounds/round19/provenance_audit.py --check
python3 -B rounds/round19/provenance_audit.py --output /tmp/provenance_audit.json
python3 -B rounds/round19/selection_controls.py --trials 4000 --seed 19019 --output /tmp/selection_controls.json
python3 -B rounds/round19/verify_candidate.py --help
```

两个生成器不传 `--output` 会更新本目录各自的 JSON；只核查时优先使用完整验收或临时输出。修改任何本轮文件后都应重新审查并更新 MANIFEST；不要仅为消除差异而接受新结果。

## 文件与边界

- [主报告](WENMI_ROUND19.md)：结果、对旧结论的修订及下一步。
- [provenance_audit.py](provenance_audit.py) / [JSON](results/provenance_audit.json)：原文、来源 SHA、所有字符位置、12 组读本差异及原图复核队列。CV 诊断投影显式标出未解释字符，不认证历史切分。
- [selection_controls.py](selection_controls.py) / [JSON](results/selection_controls.json) / [统计审计](STATISTICAL_AUDIT.md)：两个删除零模型、原始/压缩词位、6 个固定候选的选择敏感性；没有覆盖全部历史选择。
- [verify_candidate.py](verify_candidate.py) / [接口说明](CANDIDATE_VERIFICATION.md)：单音节单射表的机械回验，需独立提供候选表；没有随包提供任何六月假密钥。
- [来源审计](SOURCE_AUDIT.md) / [访问记录](sources/source_audit.json)：有限检索范围、引文级新线索和访问限制。无新同钥材料。
- `tests/`：人工正负对照与历史观测值再现；人工测试不是历史破解正对照。
- `MANIFEST.sha256`：本轮所有交付文件的散列（不含清单自身及 Python 缓存）。

## 站点

从仓库根运行 `python3 scripts/build_site.py`，需要已有依赖 `markdown`（本轮使用 3.10.2）。`docs/` 可重新生成，源材料链接指向 GitHub 仓库，避免依赖 Pages 发布目录。

本轮没有重新跑 R18 语言模型密钥搜索，没有改变 `data/` 或 R11–18，也没有将旧轮次统计输出覆盖成新结果。
