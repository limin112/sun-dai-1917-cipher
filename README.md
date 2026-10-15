# sun-dai-1917-cipher · 孙戴六月密电开放研究档案

> 孙中山—戴季陶 1917 年六月拉丁字母密电（JACAR B03050090200，帧 0509 / 0511）的开放研究档案。
> **当前状态：未破译。六月电报已验证中文译文为 0 字，密钥 / 码本未找到。**

An open research archive on two unsolved 1917 cipher telegrams between Sun Yat-sen and Dai Jitao
held by the Japan Center for Asian Historical Records (JACAR B03050090200, frames 0509 and 0511).
All reports, code, frozen inputs, positive/negative controls and failure logs from research rounds 11–19 are here.
**Status: unsolved.**

📖 **站点 / Site**：<https://limin112.github.io/sun-dai-1917-cipher/>

✉️ **维护者 / Maintainer**：X [@MinliBuilds](https://x.com/MinliBuilds) · <uslimin@gmail.com>

## 两封电报

| 帧 | 日期 | 方向 | 规模 |
|---|---|---|---|
| 0509 | 1917-06-24 | 孙中山（上海）→ 戴季陶（东京），署名 Sunwen | 8 词 × 10 字母 |
| 0511 | 1917-06-29 | 戴季陶（东京）→ 孙中山（上海），署名 Tai，两张电报纸 | 29 词，282 字母 |

两封都**没有**“文密”或“Cg”前缀；1916 年已破的 G0/Y0 与 1917 年 3 月密钥都译不出。

## 目前进展（截至 Round 19，2026-10-15）

- **转录可追溯**：新增逐字符无损解析与差异清单。Round 18 的 D 读本相对冻结独立盲读有 4 处改动，不能当作未改动的独立验证；所有原始输入和旧轮次保持不变。
- **统计更明确**：并列检验原始字母对与方向归一化序列的随机删除对照，保留种子、输入 SHA-256 和选择范围。删除元音开头字母对后得到 20 + 67 码，是 R18 校改读本下的候选解释，尚未证明这些字符就是虚码。
- **结论纠偏**：已有搜索未找到可验收密钥，但有限退火搜索不能排除整个表族；“约 88 码”是依赖假设的估算，不能证明 87 码不可解。
- **复现改进**：新增回归测试、结构结果与来源审计，详见 [Round 19 报告](rounds/round19/WENMI_ROUND19.md)。下一步仍优先寻找独立同钥材料、可靠中文留底和具名密表。

## 🆘 卡点 / Help wanted

详见 [卡点与求助](https://limin112.github.io/sun-dai-1917-cipher/docs/blockers.html)。有线索请提 [Issue](https://github.com/limin112/sun-dai-1917-cipher/issues) 或联系 X [@MinliBuilds](https://x.com/MinliBuilds) / <uslimin@gmail.com>。最需要：

1. **同钥匙的更多密文**（1917 年 7–9 月孙在广州与东京之间的电报等）；
2. **中文侧同文/留底**：戴季陶 1917 年 6 月赴日调查报告、《國父年譜》下册 926 页、《日本論》1954 台北版 71–72 页；
3. **具名私人码本实物**：国民党党史馆 `yiban050/5.3`（仁密）、`yiban333/2.2`（第64号）、`yiban050/1.2`；爱知大学 1923 胡汉民致藤瀬政次郎书简（270 / 138 / 24-6）。

## 仓库结构

```
docs/          静态 HTML 站点（每轮进展页、卡点、密文与扫描图、来源、致谢）——由 scripts/build_site.py 生成
rounds/        Round 11–19 报告、脚本、输入、结果、MANIFEST.sha256（原样归档）
data/          最新冻结输入：原始转录 / 独立盲读 / 摩斯与页面观察 / 三月正对照 / R18 结构结果
handoff/       给下一位研究者或 Agent 的交接文档与任务卡
scripts/       站点生成脚本
```

Round 13 的材料未包含在交接包中；Round 1–10 未纳入本次整理。Round 14 的 `MANIFEST.sha256` 列出的 `__pycache__/*.pyc` 已删除（编译缓存），其余文件均通过 SHA-256 校验。

## 复现

Round 19 的审计与测试仅使用 Python 标准库。完整命令及各项输入假设见 [复现说明](rounds/round19/README.md)。

```sh
python3 -B rounds/round19/reproduce.py   # 测试、临时重算比对、SHA-256 清单
python3 scripts/build_site.py           # 重新生成站点；需要 markdown
```

历史轮次的复现指令见各轮报告。它们默认会重写结果文件，请先复制对应轮次目录到临时位置再运行，避免覆盖归档。

Round 18 的密钥搜索需要 clang++ 和 Dudout 公开的 `lm3` 语言模型，见 [`rounds/round18/WENMI_ROUND18.md`](rounds/round18/WENMI_ROUND18.md) §6。

## 验收标准

只有同时具备：确切码本或书籍版次 / 表格规则、所有异常字符的原图依据、逐字重加密回冻结密文、未参与拟合的独立同钥材料交叉验证、完整中间文件——才称“破译”。语言模型通顺、显著的统计信号都不够。

## 前人工作、致谢与授权

本项目建立在以下公开研究之上（详见站点 [前人工作与致谢](docs/credits.html)）：

- **Daniel Bourdeau** · [cyphersolver](https://github.com/dbourdeau/cyphersolver)（文字 CC BY 4.0，代码 MIT）——六月密电原始转录、1916 年已解转录、1917 年 3 月已破译电报与密钥（正对照）。
- **Brice Dudout / Claude** · [wenmi](https://github.com/bdudout/wenmi)（CC BY 4.0）——0509/0511 扫描复制图、独立盲读、“无文密前缀”的纠偏、`lm3` 语言模型与 1916 G0/Y0 数据。
- **Cryptiana**（经 [NoAutopilot/cipher-lab](https://github.com/NoAutopilot/cipher-lab) 镜像）——爱知大学展品的早期讨论。

授权：

- 本仓库的文字、数据与代码采用 **CC BY 4.0**（见 [`LICENSE`](LICENSE)），与上述项目一致。引用请注明 “sun-dai-1917-cipher contributors” 并链接本仓库。
- **例外**：[`docs/assets/img/jacar/`](docs/assets/img/jacar/) 的两张电报扫描图为日本外务省外交史料馆藏、亚洲历史资料中心（JACAR，Ref. B03050090200）提供，副本取自 wenmi 项目，注明出处转载，**不在 CC BY 范围内**，请遵循 JACAR 利用规定。爱知大学展品照片未收录。
- 研究过程大量借助 AI Agent（Claude 等）完成，所有结论均附可复现脚本与对照。
