---
name: deepseek-prompt-generator
version: 1.0.0
description: 根据神兽信息与Harmony风格基线，调用DeepSeek API生成图片与视频提示词
tools:
  - deepseek_api
  - harmony_baseline_reader
inputs:
  - creature_name: string
  - juan: string (optional)
  - style_tag: string
  - baseline_id: string (optional)
outputs:
  - image_prompt: string
  - video_prompt: string
  - negative_prompt: string (optional)
---

# DeepSeek 提示词生成

## 概述

本 Skill 用于根据《山海经》神兽信息和用户设定的风格基线，调用 DeepSeek API 生成高质量的图片生成提示词和视频动态提示词。生成的提示词专为即梦（Jimeng）AI 图片生成和小云雀（Seedance）视频生成工具优化。

## 执行步骤

### 步骤 1: 读取风格基线（可选）

若调用时提供了 `baseline_id`，使用 `harmony_baseline_reader` 工具读取对应的基线模板内容。

```python
baseline_content = harmony_baseline_reader.read(baseline_id)
if not baseline_content:
    baseline_content = "默认《山海经》国风写实风格：东方神秘主义光影，电影级景深，精细毛发纹理，古卷底色"
```

基线模板包含以下维度的风格参考：
- 光影规范（lighting）：光源方向、光质类型、特效光要求
- 构图规范（composition）：视角、景深、主体比例
- 色彩规范（color）：主色调、饱和度、色彩搭配
- 细节规范（detail）：纹理精度、环境元素、粒子特效

### 步骤 2: 构建系统提示词

```text
你是一位《山海经》视觉专家，精通中国上古神话美学与AI图像生成技术。

请为神兽'{creature_name}'生成两段提示词：

1. **图片提示词**（用于即梦/Jimeng AI图片生成）：
   - 必须包含：神兽形态描述、环境场景、光影效果、细节纹理
   - 风格需符合以下基线要求：
   {baseline_content}
   - 限制在150字以内
   - 使用中文描述，关键词用逗号分隔

2. **视频提示词**（用于小云雀/Seedance视频生成）：
   - 必须描述：动作变化趋势、镜头运动方式、氛围演变过程
   - 风格需符合以下基线要求：
   {baseline_content}
   - 限制在100字以内
   - 明确起始帧和结束帧的状态差异

若提供了经卷信息'{juan}'（如"南山经"、"西山经"等），请确保场景描述符合该经卷的地理环境特征：
- 南山经：多山峦、矿产、奇树、怪蛇
- 西山经：多玉石、高峻山岭、猛禽走兽
- 北山经：多冰雪、寒冷、人面兽身之怪
- 东山经：多海洋、河流、鱼类异兽
- 中山经：多祭祀、平原地貌、吉神祥瑞

请以JSON格式返回结果，不要包含任何其他文字：
{
  "image_prompt": "...",
  "video_prompt": "...",
  "negative_prompt": "..."
}
```

### 步骤 3: 调用 DeepSeek API

```python
response = deepseek_api.chat_completion(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请为神兽'{creature_name}'生成提示词，风格标签：{style_tag}"}
    ],
    temperature=0.7,
    max_tokens=1000
)
```

### 步骤 4: 解析并返回结果

解析 DeepSeek 返回的 JSON 字符串，提取三个字段：
- `image_prompt`: 图片生成提示词
- `video_prompt`: 视频动态提示词
- `negative_prompt`: 负面提示词

若 JSON 解析失败，尝试使用正则表达式提取各字段内容。若仍失败，返回错误信息并建议重试。

### 步骤 5: 返回结构化结果

```json
{
  "creature_name": "蠃鱼",
  "juan": "西山经",
  "style_tag": "dark-fantasy",
  "image_prompt": "东方神话风格，鱼身鸟翼的蠃鱼跃出水面，月光穿透薄雾...",
  "video_prompt": "画面由水下仰拍推至水面，蠃鱼破水而出，翅膀展开洒落水珠...",
  "negative_prompt": "低质量，模糊，畸形，多肢，变异，文字，水印，签名，NSFW，卡通，3D渲染，塑料感",
  "tokens_used": 342,
  "generated_at": "2026-05-21T10:30:00Z"
}
```

## 负面提示词规范

为即梦/小云雀生成的标准负面提示词模板：

```
低质量，模糊，畸形，多肢，变异，文字，水印，签名，NSFW，卡通，3D渲染，塑料感，素描，线稿，黑白，低分辨率，像素化，变形，比例失调，解剖错误，额外的手指，融合的肢体
```

可根据具体神兽特征追加特定负面提示词：
- 有翅膀的神兽：追加 "无翼，断翼，翅膀模糊"
- 多头/多尾神兽：追加 "头数不对，尾数不对，结构错误"
- 人首兽身：追加 "纯人类，纯动物，物种混淆"

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| DeepSeek API 超时（30s） | 重试最多3次，指数退避（1s/2s/4s） |
| DeepSeek API 返回非JSON | 正则提取重试，失败后返回原始文本 |
| baseline_id 不存在 | 使用默认基线模板继续生成 |
| creature_name 为空 | 返回错误，要求提供有效神兽名 |

## 日志要求

每次调用须记录到 hermes_logs：
- `skill_name`: "deepseek-prompt-generator"
- `model`: "deepseek-chat"
- `input_summary`: "{creature_name} + {style_tag}"
- `tokens_used`: 请求 + 响应 token 总量
- `cost_estimate`: 基于 DeepSeek 定价估算（约 ¥0.001/1K tokens）
- `success`: true/false
