#!/usr/bin/env python3
"""Verify that DEEPSEEK_API_KEY can access a DeepSeek chat model."""
import os
import sys
import json

import requests


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_config.json")


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except (OSError, ValueError) as exc:
        print(f"FAIL: cannot load llm_config.json: {exc}")
        return None


def main():
    config = load_config()
    if not config:
        return 1
    api_url = f"{config['base_url'].rstrip('/')}/{config['chat_endpoint'].lstrip('/')}"
    model = config["model"]
    api_key = os.environ.get(config.get("api_key_env", "DEEPSEEK_API_KEY"), "").strip()
    if not api_key:
        print("FAIL: DEEPSEEK_API_KEY is not set")
        return 1

    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with OK."}],
                "max_tokens": 4,
                "temperature": 0,
            },
            timeout=config.get("request_timeout_seconds", 30),
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

    print(f"OK: {model} is accessible; model reply: {content.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())