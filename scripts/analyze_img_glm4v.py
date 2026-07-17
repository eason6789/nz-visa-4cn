#!/usr/bin/env python3
"""
analyze_img_glm4v.py — 智谱GLM-4V图像识别API调用
用于识别证件照片中的中文文字（身份证、户口本、营业执照、银行流水等）。

关键: 必须使用 glm-4v 模型（glm-5.1 不支持图片输入！）

Usage:
    from analyze_img_glm4v import analyze_img
    text = analyze_img("id_card_front.jpg", "请提取图中所有文字")

环境变量:
    ZHIPU_API_KEY — 智谱API Key（新用户有大量免费额度）
"""

import os
import io
import json
import base64
import urllib.request
from PIL import Image

# glm-5.1 不支持图片！只能用 glm-4v 系列
MODEL = "glm-4v"


def analyze_img(path_or_pil, prompt, api_key=None):
    """
    调用智谱GLM-4V识别图片中的文字。

    Args:
        path_or_pil: 图片文件路径（str）或 PIL Image 对象
        prompt: 识别提示词，如 "请提取图中所有文字，包括姓名、性别..."
        api_key: 智谱API Key，不传则读环境变量 ZHIPU_API_KEY

    Returns:
        str: 模型返回的识别文本

    Raises:
        RuntimeError: API返回错误时抛出
    """
    if api_key is None:
        api_key = os.environ.get("ZHIPU_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "请提供智谱API Key（设置环境变量 ZHIPU_API_KEY 或传入 api_key 参数）"
        )

    # 加载并压缩图片到1200px以内（避免太大被API拒绝）
    if isinstance(path_or_pil, str):
        img = Image.open(path_or_pil)
    else:
        img = path_or_pil

    img = img.convert("RGB")
    img.thumbnail((1200, 900), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }

    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"GLM-4V API error (HTTP {e.code}): {body}")
    except Exception as e:
        raise RuntimeError(f"GLM-4V API call failed: {e}")
