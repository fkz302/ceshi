# 抖音私信自动回复脚本（Ubuntu）

这是一个基于 Playwright 的示例脚本，用于在抖音网页版私信页面自动回复未读消息。

> ⚠️ 请仅用于你自己的账号，并遵守抖音平台规则；自动化行为存在账号风控风险，请谨慎使用。

## 1. 环境准备

```bash
sudo apt update
sudo apt install -y python3 python3-pip
python3 -m pip install --upgrade pip
python3 -m pip install playwright
python3 -m playwright install chromium
```

## 2. 启动脚本

```bash
python3 douyin_auto_reply.py --config config.json
```

首次运行会自动生成 `config.json`，并打开浏览器让你扫码登录。登录后会保存会话状态到 `.douyin_storage_state.json`。

## 3. 配置说明

默认配置示例：

```json
{
  "poll_interval_seconds": 8,
  "session_storage_path": ".douyin_storage_state.json",
  "headless": false,
  "default_reply": "你好，我已收到你的消息，稍后回复你。",
  "keyword_rules": [
    {
      "pattern": "价格|多少钱|报价",
      "reply": "你好，具体价格请私信说明需求，我会尽快回复。"
    },
    {
      "pattern": "合作|商务",
      "reply": "你好，商务合作请留下联系方式，我会尽快联系你。"
    }
  ],
  "selectors": {
    "chat_item": "[class*=\"message-chat-list\"] [class*=\"message-chat-item\"]",
    "chat_item_unread": "[class*=\"message-chat-item\"][class*=\"unread\"]",
    "last_message": "[class*=\"message-chat-item\"] [class*=\"content\"]",
    "input_box": "div[contenteditable=\"true\"]",
    "send_button": "button:has-text(\"发送\")"
  }
}
```

## 4. 常见问题

1. **元素定位失败**：抖音页面结构可能变化，修改 `selectors` 里的选择器即可。
2. **登录失效**：删除 `.douyin_storage_state.json` 后重新扫码登录。
3. **不想显示浏览器**：将 `headless` 设为 `true`，但首次登录建议 `false`。

## 5. 安全建议

- 回复频率不要过快，适当增大 `poll_interval_seconds`。
- 建议先在小号上验证再用于主账号。
- 不要回复违法违规内容，保留人工审核流程。
