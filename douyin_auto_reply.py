#!/usr/bin/env python3
"""抖音网页私信自动回复脚本（Ubuntu 友好）。

用法：
1) 首次运行手动扫码登录抖音网页版；
2) 脚本会定时轮询会话列表；
3) 当发现未读会话时，按关键词规则自动回复。
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


DEFAULT_CONFIG: dict[str, Any] = {
    "poll_interval_seconds": 8,
    "session_storage_path": ".douyin_storage_state.json",
    "headless": False,
    "default_reply": "你好，我已收到你的消息，稍后回复你。",
    "keyword_rules": [
        {"pattern": "价格|多少钱|报价", "reply": "你好，具体价格请私信说明需求，我会尽快回复。"},
        {"pattern": "合作|商务", "reply": "你好，商务合作请留下联系方式，我会尽快联系你。"},
    ],
    "selectors": {
        "chat_item": '[class*="message-chat-list"] [class*="message-chat-item"]',
        "chat_item_unread": '[class*="message-chat-item"][class*="unread"]',
        "last_message": '[class*="message-chat-item"] [class*="content"]',
        "input_box": 'div[contenteditable="true"]',
        "send_button": 'button:has-text("发送")',
    },
}


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
        logging.warning("配置文件不存在，已生成默认配置：%s", path)
        return DEFAULT_CONFIG
    with path.open("r", encoding="utf-8") as f:
        user_config = json.load(f)
    return deep_merge(DEFAULT_CONFIG, user_config)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def pick_reply(message: str, config: dict[str, Any]) -> str:
    for rule in config.get("keyword_rules", []):
        pattern = rule.get("pattern", "")
        if pattern and re.search(pattern, message, flags=re.IGNORECASE):
            return rule.get("reply", config["default_reply"])
    return config["default_reply"]


def ensure_login(page, storage_path: Path) -> None:
    page.goto("https://www.douyin.com/message", wait_until="domcontentloaded")
    if "login" in page.url.lower() or "passport" in page.url.lower():
        logging.info("请在打开的浏览器中完成扫码登录，脚本会等待...")
        while True:
            page.wait_for_timeout(2000)
            if "douyin.com/message" in page.url:
                break
    page.context.storage_state(path=str(storage_path))
    logging.info("登录状态已保存到 %s", storage_path)


def get_last_message(chat_item, selector: str) -> str:
    try:
        node = chat_item.locator(selector).first
        text = node.inner_text(timeout=1500).strip()
        return text
    except PlaywrightTimeoutError:
        return ""


def process_unread_chats(page, config: dict[str, Any]) -> int:
    selectors = config["selectors"]
    unread_items = page.locator(selectors["chat_item_unread"])
    count = unread_items.count()
    if count == 0:
        return 0

    replied = 0
    for i in range(count):
        item = unread_items.nth(i)
        item.click(timeout=3000)
        page.wait_for_timeout(700)

        last_text = get_last_message(item, selectors["last_message"])
        reply = pick_reply(last_text, config)

        input_box = page.locator(selectors["input_box"]).first
        input_box.click(timeout=3000)
        input_box.fill(reply)

        send_btn = page.locator(selectors["send_button"]).first
        send_btn.click(timeout=3000)

        replied += 1
        logging.info("已自动回复：%s -> %s", last_text, reply)
        page.wait_for_timeout(400)

    return replied


def run_bot(config: dict[str, Any]) -> None:
    storage_path = Path(config["session_storage_path"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.get("headless", False))

        if storage_path.exists():
            context = browser.new_context(storage_state=str(storage_path))
        else:
            context = browser.new_context()

        page = context.new_page()
        ensure_login(page, storage_path)

        logging.info("自动回复已启动，轮询间隔：%s 秒", config["poll_interval_seconds"])
        while True:
            try:
                page.goto("https://www.douyin.com/message", wait_until="domcontentloaded")
                replied = process_unread_chats(page, config)
                if replied:
                    context.storage_state(path=str(storage_path))
                time.sleep(config["poll_interval_seconds"])
            except KeyboardInterrupt:
                logging.info("收到退出信号，停止运行。")
                break
            except Exception as e:  # noqa: BLE001
                logging.exception("循环处理失败：%s", e)
                time.sleep(max(config["poll_interval_seconds"], 5))

        context.close()
        browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抖音自动回复脚本")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="配置文件路径（默认 config.json）",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = load_config(args.config)
    run_bot(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
