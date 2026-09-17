#!/usr/bin/env python3
"""Verify that DEEPSEEK_API_KEY can access a DeepSeek chat model."""
import os
import sys

import requests


API_URL = "https://api.deepseek.com/chat/completions"
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        print("FAIL: DEEPSEEK_API_KEY is not set")
        return 1

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": "Reply with OK."}],
                "max_tokens": 4,
                "temperature": 0,
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        print(f"FAIL: request error: {exc}")
        return 1

    if response.status_code != 200:
        detail = response.text[:300].replace("\n", " ")
        print(f"FAIL: HTTP {response.status_code}: {detail}")
        return 1

    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        print("FAIL: DeepSeek returned an unexpected response")
        return 1

    print(f"OK: {MODEL} is accessible; model reply: {content.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())