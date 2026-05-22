import json
import re
import requests
from app.hermes_client.retry import with_retry, CircuitBreaker, CircuitBreakerOpen


class DeepSeekException(Exception):
    """Raised when DeepSeek API fails after retries."""
    pass


_PROMPT_GENERATOR_SYSTEM = """你是一位《山海经》视觉专家，精通中国上古神话美学与AI图像生成技术。

请为神兽生成两段提示词：

1. **图片提示词**（用于即梦/Jimeng AI图片生成）：
   - 必须包含：神兽形态描述、环境场景、光影效果、细节纹理
   - 风格需符合风格基线要求
   - 限制在150字以内
   - 使用中文描述，关键词用逗号分隔

2. **视频提示词**（用于小云雀/Seedance视频生成）：
   - 必须描述：动作变化趋势、镜头运动方式、氛围演变过程
   - 风格需符合风格基线要求
   - 限制在100字以内
   - 明确起始帧和结束帧的状态差异

经卷地理环境参考：
- 南山经：多山峦、矿产、奇树、怪蛇
- 西山经：多玉石、高峻山岭、猛禽走兽
- 北山经：多冰雪、寒冷、人面兽身之怪
- 东山经：多海洋、河流、鱼类异兽
- 中山经：多祭祀、平原地貌、吉神祥瑞

请以JSON格式返回结果，不要包含任何其他文字：
{"image_prompt": "...", "video_prompt": "...", "negative_prompt": "..."}

负面提示词标准模板：
低质量，模糊，畸形，多肢，变异，文字，水印，签名，NSFW，卡通，3D渲染，塑料感，素描，线稿，黑白，低分辨率，像素化，变形，比例失调，解剖错误"""

_STYLE_REVIEWER_SYSTEM = """你是一位视觉风格分析专家，专注于《山海经》国风神话美学的一致性评估。

请将提示词与风格基线进行对比分析，从以下四个维度评分（每项0-100分）：

1. **光影匹配度**：光照描述（方向、光质、特效光）是否与基线一致
2. **构图一致性**：视角、景深、主体比例描述是否与基线一致
3. **色彩协调度**：色调、饱和度、色彩搭配是否与基线协调
4. **细节风格**：纹理、环境元素、粒子特效风格是否一致

请以严格的 JSON 格式返回评估结果，不要包含任何其他文字：
{
  "lighting_match": <int 0-100>,
  "composition_match": <int 0-100>,
  "color_match": <int 0-100>,
  "detail_match": <int 0-100>,
  "overall_score": <int 0-100>,
  "suggestions": "<修改建议>"
}"""

_DEFAULT_BASELINE = "默认《山海经》国风写实风格：东方神秘主义光影，电影级景深，精细毛发纹理，古卷底色"


class DeepSeekClient:
    def __init__(self, api_key, base_url="https://api.deepseek.com", model="deepseek-chat",
                 timeout=30, max_retries=3, circuit_threshold=5, circuit_cooldown=60):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.circuit_breaker = CircuitBreaker(
            threshold=circuit_threshold,
            cooldown=circuit_cooldown
        )
        self.max_retries = max_retries

    def _chat_completion(self, messages, temperature=0.7, max_tokens=1000):
        if self.circuit_breaker.is_open():
            remaining = self.circuit_breaker.remaining_cooldown()
            raise CircuitBreakerOpen(
                f"Circuit breaker open. Try again in {int(remaining)} seconds."
            )

        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        def _request():
            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            if not resp.ok:
                raise DeepSeekException(
                    f"DeepSeek returned {resp.status_code}: {resp.text[:500]}"
                )
            return resp.json()

        try:
            result = with_retry(_request, max_retries=self.max_retries)
            self.circuit_breaker.record_success()
            return result
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise DeepSeekException(
                f"AI service temporarily unavailable, please try again "
                f"or enter prompts manually. Details: {str(e)}"
            ) from e

    @staticmethod
    def _parse_json_response(content):
        """Parse JSON from DeepSeek response, with regex fallback."""
        content = content.strip()
        # Remove markdown code fences if present
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        # Regex fallback: extract key-value pairs
        result = {}
        patterns = {
            "image_prompt": r'"image_prompt"\s*:\s*"([^"]*)"',
            "video_prompt": r'"video_prompt"\s*:\s*"([^"]*)"',
            "negative_prompt": r'"negative_prompt"\s*:\s*"([^"]*)"',
            "lighting_match": r'"lighting_match"\s*:\s*(\d+)',
            "composition_match": r'"composition_match"\s*:\s*(\d+)',
            "color_match": r'"color_match"\s*:\s*(\d+)',
            "detail_match": r'"detail_match"\s*:\s*(\d+)',
            "overall_score": r'"overall_score"\s*:\s*(\d+)',
            "suggestions": r'"suggestions"\s*:\s*"([^"]*)"',
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1)
                if key.endswith("_match") or key == "overall_score":
                    result[key] = int(value)
                else:
                    result[key] = value
        if not result:
            raise DeepSeekException(f"Failed to parse DeepSeek response: {content[:300]}")
        return result

    def generate_prompt(self, creature_name, juan=None, style_tag=None, baseline_content=None):
        baseline = baseline_content or _DEFAULT_BASELINE

        system_msg = _PROMPT_GENERATOR_SYSTEM + f"""

当前风格基线：
{baseline}"""

        user_msg = f"请为神兽'{creature_name}'生成提示词"
        if style_tag:
            user_msg += f"，风格标签：{style_tag}"
        if juan:
            user_msg += f"\n该神兽出自《山海经·{juan}》，请确保场景描述符合该经卷的地理环境特征。"

        response = self._chat_completion(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        content = response["choices"][0]["message"]["content"]
        parsed = self._parse_json_response(content)

        usage = response.get("usage", {})
        return {
            "image_prompt": parsed.get("image_prompt", ""),
            "video_prompt": parsed.get("video_prompt", ""),
            "negative_prompt": parsed.get("negative_prompt", ""),
            "tokens_input": usage.get("prompt_tokens"),
            "tokens_output": usage.get("completion_tokens"),
            "api_cost": _estimate_cost(usage),
        }

    def review_style(self, generated_prompt, baseline_content=None):
        baseline = baseline_content or _DEFAULT_BASELINE

        user_msg = f"""## 风格基线
{baseline}

## 待评估提示词
{generated_prompt}"""

        response = self._chat_completion(
            messages=[
                {"role": "system", "content": "你是一位严格的视觉风格分析专家。只返回JSON，不返回任何其他内容。"},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=800,
        )

        content = response["choices"][0]["message"]["content"]
        parsed = self._parse_json_response(content)

        # Compute weighted overall score and grade
        dims = ["lighting_match", "composition_match", "color_match", "detail_match"]
        if all(k in parsed for k in dims):
            computed = sum(parsed[k] for k in dims) / 4
            if abs(parsed.get("overall_score", 0) - computed) > 5:
                parsed["overall_score"] = round(computed)

        score = parsed.get("overall_score", 0)
        grade = _score_to_grade(score)
        parsed["suggestions"] = _enhance_suggestions(grade, parsed.get("suggestions", ""))

        usage = response.get("usage", {})
        return {
            "overall_score": score,
            "grade": grade,
            "dimension_scores": {k: parsed.get(k, 0) for k in dims},
            "suggestions": parsed.get("suggestions", ""),
            "tokens_input": usage.get("prompt_tokens"),
            "tokens_output": usage.get("completion_tokens"),
            "api_cost": _estimate_cost(usage),
        }


def _estimate_cost(usage):
    """Estimate cost based on DeepSeek pricing (~¥0.001/1K tokens)."""
    if not usage:
        return None
    total_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
    return round(total_tokens * 0.001 / 1000, 6)


def _score_to_grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 50:
        return "D"
    return "F"


def _enhance_suggestions(grade, suggestions):
    prefix_map = {
        "A": "[优秀] 提示词与基线高度一致，可直接使用。",
        "B": "[良好] 提示词与基线基本一致，建议微调个别维度。",
        "C": "[合格] 提示词可通过审核，但需关注偏离维度。",
        "D": "⚠️ [待改进] 风格偏差较明显，建议基于以下建议重新生成或手动调整：",
        "F": "🚫 [不合格] 风格严重偏离基线，必须重新生成。主要问题：",
    }
    prefix = prefix_map.get(grade, "")
    return f"{prefix}{suggestions}" if suggestions else prefix
