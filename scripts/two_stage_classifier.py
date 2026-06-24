"""
Two-stage classification module for SNS post analysis.

Stage 1: Detect post type (policy, meta, sarcasm, news_share, unclear)
Stage 2: Return classification hints based on detected type

Usage:
    from two_stage_classifier import detect_post_types, detect_post_types_batch
"""

import json
import urllib.request

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

VALID_TYPES = {"policy", "meta", "sarcasm", "news_share", "unclear"}

HINTS = {
    "meta": "この投稿は人物・政党の行動批判です。政策カテゴリではなく行動・信頼性の観点で分類してください。",
    "sarcasm": "この投稿は皮肉・揶揄です。攻撃対象を推定し、その対象への批判として分類してください。",
    "news_share": "この投稿はニュース共有です。共有されたニュースの主題に基づいてカテゴリを判断してください。",
}


def _call_ollama(model: str, prompt: str, timeout: int) -> str:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 20},
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "").strip()


def _parse_type(raw: str) -> str:
    """Extract a valid post type from the model response."""
    token = raw.strip().lower().split()[0] if raw.strip() else ""
    # Strip punctuation
    token = token.strip(".,;:!?\"'()[]{}。、")
    if token in VALID_TYPES:
        return token
    # Fallback: check if any valid type appears in the response
    for t in VALID_TYPES:
        if t in raw.lower():
            return t
    return "unclear"


def _classify_one(text: str, model: str, timeout: int) -> dict:
    prompt = (
        "この投稿のタイプを1つ選んでください: policy, meta, sarcasm, news_share, unclear\n"
        f"投稿: {text}\n"
        "回答（1単語のみ）:"
    )
    raw = _call_ollama(model, prompt, timeout)
    post_type = _parse_type(raw)
    return {"type": post_type, "hint": HINTS.get(post_type, "")}


def detect_post_types(
    texts: list[str],
    model: str = "qwen2.5:7b",
    timeout: int = 60,
) -> list[dict]:
    """
    Classify each text individually and return type + hint.

    Returns list of {"type": "policy"|"meta"|"sarcasm"|"news_share"|"unclear",
                      "hint": "..."} for each text.
    """
    results = []
    for text in texts:
        try:
            result = _classify_one(text, model, timeout)
        except Exception as e:
            print(f"[two_stage_classifier] Error classifying post: {e}")
            result = {"type": "unclear", "hint": ""}
        results.append(result)
    return results


def detect_post_types_batch(
    texts: list[str],
    model: str = "qwen2.5:7b",
    batch_size: int = 5,
    timeout: int = 120,
) -> list[dict]:
    """
    Classify texts in batches for efficiency.

    Each batch sends multiple posts in a single prompt asking the model
    to return one type per line. Falls back to individual classification
    on parse failure.
    """
    all_results: list[dict] = [None] * len(texts)  # type: ignore[list-item]

    for start in range(0, len(texts), batch_size):
        chunk = texts[start : start + batch_size]
        indices = list(range(start, start + len(chunk)))

        if len(chunk) == 1:
            # Single post — use individual classification
            result = _classify_one(chunk[0], model, timeout)
            all_results[indices[0]] = result
            continue

        # Build batch prompt
        lines = []
        for i, text in enumerate(chunk, 1):
            lines.append(f"{i}. {text}")
        posts_block = "\n".join(lines)

        prompt = (
            "以下の各投稿のタイプを1つずつ選んでください: policy, meta, sarcasm, news_share, unclear\n"
            f"{posts_block}\n"
            f"回答（各行に番号とタイプのみ、{len(chunk)}行で）:"
        )

        try:
            raw = _call_ollama(model, prompt, timeout)
            parsed = _parse_batch_response(raw, len(chunk))

            if parsed is not None:
                for idx, post_type in zip(indices, parsed):
                    all_results[idx] = {
                        "type": post_type,
                        "hint": HINTS.get(post_type, ""),
                    }
                continue
        except Exception as e:
            print(f"[two_stage_classifier] Batch failed, falling back: {e}")

        # Fallback: classify individually
        for idx, text in zip(indices, chunk):
            try:
                result = _classify_one(text, model, timeout)
            except Exception as e:
                print(f"[two_stage_classifier] Error classifying post: {e}")
                result = {"type": "unclear", "hint": ""}
            all_results[idx] = result

    return all_results


def _parse_batch_response(raw: str, expected: int) -> list[str] | None:
    """Parse batch response into list of types. Returns None on failure."""
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    if len(lines) < expected:
        return None

    types = []
    for line in lines[:expected]:
        # Try to extract type from lines like "1. meta" or "1: policy"
        parts = line.replace(".", " ").replace(":", " ").split()
        found = None
        for part in parts:
            cleaned = part.strip().lower().strip(".,;:!?\"'()[]{}。、")
            if cleaned in VALID_TYPES:
                found = cleaned
                break
        if found is None:
            return None
        types.append(found)

    return types


if __name__ == "__main__":
    examples = [
        "憲法改正には賛成。9条の改正が必要だと思う。",
        "自民党は言ってることとやってることが違いすぎる。ダブスタもいいとこ。",
        "さすが我が国の政治家、国民のことなんて考えてないよねw",
        "【速報】岸田首相が憲法改正について言及 NHKニュース https://t.co/xxx",
        "なんかよくわからんけど政治の話多いな",
    ]

    print("=== Individual classification ===")
    results = detect_post_types(examples)
    for text, result in zip(examples, results):
        print(f"  [{result['type']:12s}] {text[:50]}")
        if result["hint"]:
            print(f"               hint: {result['hint'][:60]}...")

    print("\n=== Batch classification ===")
    results_batch = detect_post_types_batch(examples)
    for text, result in zip(examples, results_batch):
        print(f"  [{result['type']:12s}] {text[:50]}")
