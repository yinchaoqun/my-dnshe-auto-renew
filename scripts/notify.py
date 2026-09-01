import os
import json
from datetime import datetime, timezone

def send_wecom_notification(job_status, run_url):
    """发送企业微信通知（标准 Markdown 格式，无日志链接）"""
    webhook_url = os.environ.get("WECOM_WEBHOOK")
    if not webhook_url:
        print("⚠️ 未配置 WECOM_WEBHOOK，跳过通知")
        return

    state_path = "state/domains-state.json"
    domain_sections = []

    # 1. 读取状态文件
    raw_state = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                raw_state = json.load(f)
        except Exception as e:
            domain_sections.append(f"❌ 状态文件解析失败：{str(e)}")
    else:
        domain_sections.append("⚠️ 状态文件不存在")

    # 2. 提取数据并构建 Markdown 内容块
    domains_data = raw_state.get("domains", {})
    if domains_data:
        for domain, info in domains_data.items():
            expires_at = info.get("expires_at", "N/A")
            renew_before = info.get("renew_before_days", "N/A")
            source = info.get("source", "N/A")
            
            # 计算剩余天数以确定状态图标
            days_left = "N/A"
            status_icon = "🟢"
            if expires_at != "N/A":
                try:
                    exp_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    days_left = (exp_dt - now).days
                    
                    if days_left < 30:
                        status_icon = "🔴"
                    elif days_left < 90:
                        status_icon = "🟡"
                except:
                    days_left = "解析失败"

            # 构建单个域名的 Markdown 块（使用两个空格 + 换行符实现换行）
            section = f"""---
### {status_icon} 域名状态
- **域名**：`{domain}`
- **到期时间**：`{expires_at}`
- **剩余天数**：`{days_left}` 天
- **提前续期阈值**：`{renew_before}` 天
- **数据来源**：`{source}`"""
            domain_sections.append(section)

    # 3. 状态映射（修复大小写问题）
    status_upper = job_status.upper()
    emoji_map = {
        "SUCCESS": "✅",
        "FAILURE": "❌",
        "CANCELLED": "⛔",
        "SKIPPED": "⏭️"
    }
    text_map = {
        "SUCCESS": "执行成功",
        "FAILURE": "执行失败",
        "CANCELLED": "已取消",
        "SKIPPED": "已跳过"
    }
    
    emoji = emoji_map.get(status_upper, "❓")
    status_text = text_map.get(status_upper, "未知状态")

    # 4. 组装最终 Markdown 内容（标准语法，无 HTML）
    content = f"""## {emoji} DNSHE 自动续期任务 · {status_text}
*运行时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC*

### 📋 域名状态明细
{''.join(domain_sections)}
---"""

    # 5. 发送请求
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
            print(f"❌ 通知发送失败，状态码: {resp.status_code}，响应: {resp.text}")
    except Exception as e:
        print(f"❌ 发送通知异常: {str(e)}")

if __name__ == "__main__":
    JOB_STATUS = os.environ.get("STATUS", "UNKNOWN")
    RUN_URL = os.environ.get("RUN_URL", "#")
    send_wecom_notification(JOB_STATUS, RUN_URL)
