import os
import json
from datetime import datetime, timezone

def send_wecom_notification(job_status, run_url):
    """
    发送企业微信通知
    """
    # ✅ 所有函数内代码必须缩进 4 个空格！！！
    webhook_url = os.environ.get("WECOM_WEBHOOK")
    if not webhook_url:
        print("⚠️ 未配置 WECOM_WEBHOOK，跳过企业微信通知")
        return

    # 1. 读取状态文件
    state_path = "state/domains-state.json"
    domain_lines = []
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                for domain, info in state.items():
                    exp_str = info.get("expires_at", "N/A")
                    renewed_at = info.get("last_renewed_at", "")
                    
                    # 尝试计算剩余天数（适配你的实际日期格式：YYYY-MM-DD HH:MM）
                    days_left = "N/A"
                    try:
                        # ✅ 修正：用 strptime 解析你的日期格式，不要用 fromisoformat
                        exp_dt = datetime.strptime(exp_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        days_left = (exp_dt - now).days
                    except Exception:
                        pass

                    # 构建每一行的信息
                    line = f"- `{domain}` | 到期：`{exp_str}`"
                    if isinstance(days_left, int):
                        line += f" | 剩余 **{days_left}** 天"
                    if renewed_at:
                        line += f"\n  > 续期时间：`{renewed_at}`"
                    
                    domain_lines.append(line)
        except Exception as e:
            domain_lines.append(f"❌ 读取状态文件失败: {e}")
    else:
        domain_lines.append("⚠️ 状态文件不存在（首次运行可能还未生成）")

    # 2. 状态映射
    emoji_map = {
        "SUCCESS": "✅",
        "FAILURE": "❌",
        "CANCELLED": "⛔",
        "SKIPPED": "⏭️"
    }
    emoji = emoji_map.get(job_status, "❓")

    status_text_map = {
        "SUCCESS": "成功",
        "FAILURE": "失败",
        "CANCELLED": "已取消",
        "SKIPPED": "已跳过"
    }
    status_text = status_text_map.get(job_status, "未知状态")

    # 3. ✅ 补全完整的 Markdown 内容（之前你只写了一半）
    content = f"""## {emoji} DNSHE 自动续期任务 {status_text}
**运行时间**：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC
**运行状态**：`{job_status.upper()}`

### 📋 域名状态明细
{chr(10).join(domain_lines) if domain_lines else '❌ 无域名数据'}

---
🔗 [点击查看完整运行日志]({run_url})
    """

    # 4. 发送请求
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content.strip()
        }
    }

    try:
        import requests
        resp = requests.post(webhook_url, json=payload, timeout=15)
        if resp.status_code == 200:
            print("✅ 企业微信通知发送成功")
        else:
            print(f"❌ 企业微信通知发送失败，状态码: {resp.status_code}, 响应: {resp.text}")
    except Exception as e:
        print(f"❌ 发送通知时发生异常: {e}")

# ✅ 修正：必须是 __name__ 和 __main__，前后双下划线
if __name__ == "__main__":
    JOB_STATUS = os.environ.get("STATUS", "UNKNOWN")
    RUN_URL = os.environ.get("RUN_URL", "#")
    send_wecom_notification(JOB_STATUS, RUN_URL)
