# sun-dai-1917-cipher · 孙戴六月密电开放研究档案

> 孙中山—戴季陶 1917 年六月拉丁字母密电（JACAR B03050090200，帧 0509 / 0511）的开放研究档案。
> **当前状态：未破译。六月电报已验证中文译文为 0 字，密钥 / 码本未找到。**

An open research archive on two unsolved 1917 cipher telegrams between Sun Yat-sen and Dai Jitao
held by the Japan Center for Asian Historical Records (JACAR B03050090200, frames 0509 and 0511).
All reports, code, frozen inputs, positive/negative controls and failure logs from research rounds 11–18 are here.
**Status: unsolved.**

📖 **站点 / Site**：打开 [`docs/index.html`](docs/index.html)，或启用 GitHub Pages 后访问 `https://limin112.github.io/sun-dai-1917-cipher/`。

## 两封电报

| 帧 | 日期 | 方向 | 规模 |
|---|---|---|---|
| 0509 | 1917-06-24 | 孙中山（上海）→ 戴季陶（东京），署名 Sunwen | 8 词 × 10 字母 |
| 0511 | 1917-06-29 | 戴季陶（东京）→ 孙中山（上海），署名 Tai，两张电报纸 | 29 词，282 字母 |

两封都**没有**“文密”或“Cg”前缀；1916 年已破的 G0/Y0 与 1917 年 3 月密钥都译不出。

## 目前进展（截至 Round 18，2026-10-14）

- **结构**：把元音开头的字母对（`ac/as/op/um/ax`）视为虚码删除后，0509 = 20 个四字母电码，0511 = 67 个（40 + 27），长度完全自洽；辅音奇偶 z ≈ 6.3，重复码对 11（`cafe`×3、`mupo`×3 等），统计形态与 1916 年真实已解电报一致。
- **排除**：线性 6 宽表（任意偏移）、5 宽 + y 同码异形、Y0 同构 97,920 把、加数密钥、G0 式坐标表、第 64 号历史表等全部阴性；求解器在 1916 真实 Y0 密文上能无先验找回原钥（正对照）。
- **瓶颈**：若为自由乱序表，唯一解距离约 88 码，而六月总共只有 87 码。**缺的是新材料，不是更多搜索。**

## 🆘 卡点 / Help wanted

详见 [`docs/blockers.html`](docs/blockers.html)。最需要：

1. JACAR 帧 0509 / 0511 **官方高分辨原图**，逐字盲校疑字；
2. **同钥匙的更多密文**（1917 年 7–9 月孙在广州与东京之间的电报等）；
3. **中文侧同文/留底**：戴季陶 1917 年 6 月赴日调查报告、《國父年譜》下册 926 页、《日本論》1954 台北版 71–72 页；
4. **具名私人码本实物**：国民党党史馆 `yiban050/5.3`（仁密）、`yiban333/2.2`（第64号）、`yiban050/1.2`；爱知大学 1923 胡汉民致藤瀬政次郎书简（270 / 138 / 24-6）。

## 仓库结构

```
docs/          静态 HTML 站点（每轮进展页、卡点、密文、来源）——由 scripts/build_site.py 生成
rounds/        Round 11–18 原始报告、脚本、输入、结果、MANIFEST.sha256（原样归档）
data/          最新冻结输入：原始转录 / 独立盲读 / 摩斯与页面观察 / 三月正对照 / R18 结构结果
handoff/       给下一位研究者或 Agent 的交接文档与任务卡
scripts/       站点生成脚本
```

Round 13 的材料未包含在交接包中；Round 1–10 未纳入本次整理。Round 14 的 `MANIFEST.sha256` 列出的 `__pycache__/*.pyc` 已删除（编译缓存），其余文件均通过 SHA-256 校验。

## 复现

```sh
cd rounds/round18 && python3 round18_structure.py 4000     # 标准库，约 10 秒
cd rounds/round17 && python3 round17_analysis.py
pip install markdown && python3 scripts/build_site.py      # 重新生成站点
```

Round 18 的密钥搜索需要 clang++ 和 Dudout 公开的 `lm3` 语言模型，见 [`rounds/round18/WENMI_ROUND18.md`](rounds/round18/WENMI_ROUND18.md) §6。

## 验收标准

只有同时具备：确切码本或书籍版次 / 表格规则、所有异常字符的原图依据、逐字重加密回冻结密文、未参与拟合的独立同钥材料交叉验证、完整中间文件——才称“破译”。语言模型通顺、显著的统计信号都不够。

## 致谢与授权

- 本仓库文字、数据与代码：**CC BY 4.0**（见 [`LICENSE`](LICENSE)）。
- 转录与数据来自 **Daniel Bourdeau**（[cyphersolver](https://github.com/dbourdeau/cyphersolver)，CC BY 4.0）与 **Brice Dudout / Claude**（[wenmi](https://github.com/bdudout/wenmi)，CC BY 4.0），已在各文件中注明。
- **JACAR 扫描影像、爱知大学展品照片不在本仓库中**，版权归原馆；请通过 [`handoff/SOURCES_AND_ACCESS.md`](handoff/SOURCES_AND_ACCESS.md) 中的链接查看。
- 研究过程大量借助 AI Agent（Claude 等）完成，所有结论均附可复现脚本与对照。
