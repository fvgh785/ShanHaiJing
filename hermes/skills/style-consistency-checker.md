---
name: style-consistency-checker
version: 1.0.0
description: 将新生成的提示词与Harmony基线对比，评估风格一致性并给出修改建议
tools:
  - deepseek_api
  - harmony_baseline_reader
inputs:
  - generated_prompt: string
  - baseline_id: string
outputs:
  - overall_score: number (0-100)
  - dimension_scores:
      lighting_match: number
      composition_match: number
      color_match: number
      detail_match: number
  - suggestions: string
---

# 风格一致性校验

## 概述

本 Skill 用于自动评估新生成的提示词与已激活的 Harmony 风格基线之间的一致性。通过 DeepSeek API 从四个维度进行评分，并给出具体的修改建议，确保《山海经》全系列视频保持统一的视觉风格。

## 四维评分体系

| 维度 | 评估内容 | 权重 |
|------|---------|------|
| 光影匹配度 (lighting_match) | 光照方向、光质（硬光/柔光）、特效光（体积光、神光）是否符合基线 | 25% |
| 构图一致性 (composition_match) | 视角（平视/俯视/仰视）、景深（浅/深）、主体在画面中的比例 | 25% |
| 色彩协调度 (color_match) | 色调（暖/冷/中性）、饱和度（高/低）、色彩搭配方案 | 25% |
| 细节风格 (detail_match) | 纹理精度、环境元素类型、粒子特效风格（尘/雾/光点） | 25% |

总体评分 = 四维度加权平均

## 执行步骤

### 步骤 1: 读取基线模板

```python
baseline = harmony_baseline_reader.read(baseline_id)
if not baseline:
    return {"error": f"基线模板 {baseline_id} 不存在", "overall_score": 0}
```

基线模板为标准 Markdown 文件，YAML frontmatter 中包含风格参数，正文为风格描述。

### 步骤 2: 构建评估提示词

```text
你是一位视觉风格分析专家，专注于《山海经》国风神话美学的一致性评估。

请将以下新生成的提示词与风格基线进行对比分析。

## 风格基线
{baseline_content}

## 待评估提示词
{generated_prompt}

请从以下四个维度评分（每项0-100分）：

1. **光影匹配度**：分析提示词中的光照描述（方向、光质、特效光）是否与基线一致
   - 0-30：严重偏离，光源方向相反或光质完全不同
   - 31-60：部分偏离，次要光源或特效光不一致
   - 61-85：基本一致，核心光照特征符合
   - 86-100：高度一致，光照描述精确匹配基线

2. **构图一致性**：分析提示词中的视角、景深、主体比例描述是否与基线一致
   - 0-30：构图方式完全不同（如基线要求仰拍但提示词为俯拍）
   - 31-60：视角一致但景深或比例有偏差
   - 61-85：主体构图一致，次要元素位置有差异
   - 86-100：构图方式完全匹配

3. **色彩协调度**：分析色调、饱和度、色彩搭配是否与基线保持协调
   - 0-30：色调完全冲突（如基线要求冷色调但提示词为暖色调）
   - 31-60：主色调一致但饱和度或搭配色有偏差
   - 61-85：色调协调，局部色彩有细微差异
   - 86-100：色彩方案精确匹配基线

4. **细节风格**：分析纹理、环境元素、粒子特效风格是否一致
   - 0-30：细节风格完全不同（如基线要求写实但提示词倾向卡通）
   - 31-60：核心纹理一致但环境元素或特效有差异
   - 61-85：细节丰富度匹配，个别元素有差异
   - 86-100：细节风格完全一致

## 输出要求

请以严格的 JSON 格式返回评估结果，不要包含任何其他文字或代码块标记：

{
  "lighting_match": <int 0-100>,
  "composition_match": <int 0-100>,
  "color_match": <int 0-100>,
  "detail_match": <int 0-100>,
  "overall_score": <int 0-100>,
  "suggestions": "<具体的修改建议，若分数较高则给出微调建议，若分数较低则给出方向性建议>"
}
```

### 步骤 3: 调用 DeepSeek API

```python
response = deepseek_api.chat_completion(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一位严格的视觉风格分析专家。只返回JSON，不返回任何其他内容。"},
        {"role": "user", "content": evaluation_prompt}
    ],
    temperature=0.3,  # 低温度确保评分稳定一致
    max_tokens=800
)
```

注意：temperature 设为 0.3（低于提示词生成的 0.7），因为风格评估需要一致性和稳定性，而非创造性。

### 步骤 4: 解析评分结果

解析 DeepSeek 返回的 JSON 评分数据，并计算加权总分用于验证：

```python
data = parse_json(response)
computed_overall = (
    data["lighting_match"] * 0.25 +
    data["composition_match"] * 0.25 +
    data["color_match"] * 0.25 +
    data["detail_match"] * 0.25
)

# 若API返回的overall_score与计算结果偏差超过5分，使用计算值
if abs(data["overall_score"] - computed_overall) > 5:
    data["overall_score"] = round(computed_overall)
```

### 步骤 5: 分数分级与建议增强

根据总分自动追加建议等级标记：

```python
def enhance_suggestions(data):
    score = data["overall_score"]
    prefix = ""
    
    if score >= 90:
        prefix = "[优秀] 提示词与基线高度一致，可直接使用。"
        data["grade"] = "A"
    elif score >= 80:
        prefix = "[良好] 提示词与基线基本一致，建议微调个别维度。"
        data["grade"] = "B"
    elif score >= 70:
        prefix = "[合格] 提示词可通过审核，但需关注偏离维度。"
        data["grade"] = "C"
    elif score >= 50:
        prefix = "⚠️ [待改进] 风格偏差较明显，建议基于以下建议重新生成或手动调整：\n"
        data["grade"] = "D"
    else:
        prefix = "🚫 [不合格] 风格严重偏离基线，必须重新生成。主要问题：\n"
        data["grade"] = "F"
    
    data["suggestions"] = prefix + data["suggestions"]
    return data
```

### 步骤 6: 返回结构化结果

```json
{
  "baseline_id": "dark-fantasy-v1",
  "grade": "B",
  "overall_score": 83,
  "dimension_scores": {
    "lighting_match": 88,
    "composition_match": 79,
    "color_match": 85,
    "detail_match": 80
  },
  "suggestions": "[良好] 提示词与基线基本一致，建议微调个别维度。在构图方面，建议将视角从平视调整为略带仰角（15度左右），以匹配基线的'史诗感仰视'构图要求。细节方面可增加'飘散的金色粒子'特效以增强神话氛围。",
  "checked_at": "2026-05-21T10:31:00Z"
}
```

## 阈值配置

| 配置项 | 默认值 | 说明 |
|--------|-------|------|
| `pass_threshold` | 70 | 低于此分数标记"⚠️ 风格偏差较大" |
| `retry_threshold` | 50 | 低于此分数建议直接重新生成 |
| `api_temperature` | 0.3 | 评估用温度参数 |
| `max_deviation_tolerance` | 5 | API返回总分与计算值允许的最大偏差 |

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| baseline_id 不存在 | 返回错误，不执行评估 |
| DeepSeek API 返回非JSON | 重试一次，失败后返回原始响应作为建议 |
| 单个维度评分缺失 | 该维度记为0，继续计算总分 |
| generated_prompt 为空 | 返回错误，overall_score = 0 |

## 日志要求

每次调用须记录到 hermes_logs：
- `skill_name`: "style-consistency-checker"
- `model`: "deepseek-chat"
- `input_summary`: "评估提示词一致性 (baseline: {baseline_id})"
- `tokens_used`: 请求 + 响应 token 总量
- `cost_estimate`: 基于 DeepSeek 定价估算
- `overall_score`: 评估总分
- `grade`: 评级（A/B/C/D/F）
- `success`: true/false
