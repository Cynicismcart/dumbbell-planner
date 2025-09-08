# Dumbbell Planner — 哑铃/连接杆组合计算器（含上片图）

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6-brightgreen.svg)](https://doc.qt.io/qtforpython/)

一款**本地运行**的哑铃/连接杆“上片”组合计算器：输入你拥有的杠片 **重量/厚度/数量** 与 **每侧可用长度**，一键枚举所有**符合长度限制**的可行组合，自动按**重量从大到小**排序，并绘制**上片图**（每片独立，标注 KG）。

> 适合配对哑铃、连接杆、单只哑铃三类场景，支持搜索目标重量与**就近 ±1 kg**提示。

## 预览

<p align="center">
  <img src="docs/images/hero-overview.png" alt="应用总览（Hero）">
</p>
<p align="center"><em>应用总览（清单 → 结果 → 上片图）</em></p>

---

## ✨ 功能特性

- **三种模式**
  - **哑铃（配成一对）**：库存按 4 片计（两只哑铃两侧对称），显示“每只不含杆”与“<strong>一对含杆总重（公式）</strong>”。
    <p align="center">
      <img src="docs/images/tab-pair-formula.png" alt="哑铃一对：一对含杆总重（公式）">
    </p>
    <p align="center"><em>哑铃一对：展示 “每只不含杆 ×2 + 单根杆重 ×2 = 一对含杆总重” 的公式列</em></p>

  - **单只哑铃**：库存按 2 片计（单只左右对称），显示“<strong>单只不含杆</strong>”与“<strong>含杆总重</strong>”。
    <p align="center">
      <img src="docs/images/tab-single-without-and-with-bar.png" alt="单只哑铃：不含杆 + 含杆">
    </p>
    <p align="center"><em>单只哑铃：首列为不含杆重量；末列为含杆总重</em></p>

  - **连接杆（单根）**：库存按 2 片计（左右对称），显示“不含杆”与“<strong>含杆总重(kg)</strong>”。
    <p align="center">
      <img src="docs/images/tab-connector-with-bar.png" alt="连接杆（单根）：含杆总重">
    </p>
    <p align="center"><em>连接杆模式：展示不含杆与含杆总重(kg)</em></p>

- **上片图可视化**：每片独立矩形，片上标注“x kg”，带“中心/长度上限”参考线与“杆体”示意。  
- **搜索重量**：当前页按“<strong>含杆总重</strong>”列搜索；若未命中，自动显示**最近的 ±1 kg**候选并定位。  
- **数据导出**：各页一键导出 CSV。  
- **中文字体自动设置**，避免 Matplotlib 中文乱码。

---

## 📦 安装

```bash
git clone https://github.com/Cynicismcart/dumbbell-planner.git
cd dumbbell-planner
python -m venv .venv && . .venv/Scripts/activate  # Windows PowerShell
pip install -r requirements.txt
python main.py
```

> macOS/Linux 激活请用 `source .venv/bin/activate`。

---

## 🚀 快速上手

1. 左侧表格输入或导入 `sample_inventory.json`（重量/厚度/数量/标签）。  
2. 设置每侧可用长度：
   - 哑铃一对：默认 **21 cm**
   - 连接杆：默认 **21 cm**
3. 设置杆重（可自定义）：
   - 单根哑铃杆：默认 **0.365 kg**
   - 连接杆（整根）：默认 **1.0 kg**
4. 点击 **“开始计算所有组合”**。  
5. 右侧选择分页、搜索目标重量、点击“查看上片图”。

---

## 🧮 计算逻辑（简述）

- **对称上片**：只考虑**左右对称**的装片方式。  
- **库存约束**：  
  - 配对哑铃：每种片最多使用 `count // 4` 作为**每侧上限**。  
  - 连接杆/单只哑铃：每种片最多使用 `count // 2` 作为**每侧上限**。  
- **长度约束**：每侧厚度累加 ≤ **每侧可用长度**。  
- **重量**：结果中的 `总重` 指**片重合计**（连接杆与哑铃杆重在展示时另行加总）。  
- **排序**：按 `总重` 降序，厚度升序。

---

## 🔎 搜索说明

- 在**当前分页**搜索目标重量（kg）。  
- 精确命中则直接定位；否则展示**最近的 ±1 kg**若干候选并定位到最接近项。  
- 搜索列：  
  - 配对哑铃：**“一对含杆总重（公式）”**（内部以结果值比较）  
  - 连接杆：**“含杆总重(kg)”**  
  - 单只哑铃：**“含杆总重(kg)”**

---

## 🖼️ 上片图

<p align="center">
  <img src="docs/images/diagram-closeup.png" alt="上片图特写（逐片 KG 标注）">
</p>
<p align="center"><em>上片图特写：每片均标注 KG，含中心线与长度上限线</em></p>

- 以**中心为 0**，向两侧累加厚度；  
- 细线标出**每侧上限**位置；  
- 每片以矩形绘制，**片内标注 KG**；  
- 仅用于可视化的**细缝**不会改变实际厚度计算。

> 小技巧：可用系统截图工具保存当前上片图。也可在 `PlateDiagramCanvas.draw_layout()` 中扩展自定义导出 PNG。

---

## 📁 数据格式（JSON）

```json
[
  { "weight": 3.0, "thickness": 4.0, "count": 10, "label": "3 kg" },
  { "weight": 2.5, "thickness": 4.0, "count": 2,  "label": "2.5 kg" },
  { "weight": 2.0, "thickness": 4.0, "count": 4,  "label": "2 kg" },
  { "weight": 1.5, "thickness": 3.5, "count": 2,  "label": "1.5 kg" },
  { "weight": 1.25, "thickness": 3.0, "count": 10, "label": "1.25 kg" }
]
```

---

## 🧰 开发

- 代码结构：  
  - `planner.py`：核心枚举与组合逻辑（与 GUI 解耦，可单独测试）。  
  - `main.py`：PySide6 GUI、可视化、导入导出、搜索等。  
- 代码风格：建议 `black` + `flake8`（CI 已配置）。

### 运行测试

```bash
pip install -r requirements.txt
pip install pytest
pytest -q
```

---

## 🗺️ 路线图（Roadmap）

- [ ] 导出上片图 PNG / SVG  
- [ ] 支持“卡扣厚度/重量”参与计算与可视化  
- [ ] 自定义摆放排序（重→轻/厚→薄/固定序）  
- [ ] 方案去重的更强“等价类”合并策略  
- [ ] 多语言（en/zh）界面切换

---

## 🤝 参与贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。欢迎 Issue 与 PR！

---

## 📜 许可证

本项目使用 [MIT License](LICENSE)。版权所有 © 2025 Cynicismcart

---

### 放图说明
将以下真实截图按同名覆盖到仓库的 `docs/images/` 下即可在 README 中显示：  
- `hero-overview.png`（应用总览）  
- `tab-pair-formula.png`（哑铃一对：公式列）  
- `tab-single-without-and-with-bar.png`（单只：不含杆 + 含杆）  
- `tab-connector-with-bar.png`（连接杆：含杆总重）  
- `diagram-closeup.png`（上片图特写）

> 建议窗口宽度 1200–1440px、只截应用窗口、统一浅色主题与缩放比例。
