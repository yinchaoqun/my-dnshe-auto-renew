import os
import json
from datetime import datetime, timezone

def send_wecom_notification(job_status, run_url):
    """发送企业微信通知，完全适配你的接口返回结构"""
    webhook_url = os.environ.get("WECOM_WEBHOOK")
    if not webhook_url:
        print("⚠️ 未配置 WECOM_WEBHOOK，跳过通知")
        return

    state_path = "state/domains-state.json"
    raw_state = {}
    domain_lines = []

    # 1. 读取状态文件（和你保存的结构完全一致，包含外层 domains）
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                raw_state = json.load(f)
        except Exception as e:
            domain_lines.append(f"❌ 状态文件解析失败：{str(e)}")
    else:
        domain_lines.append("⚠️ 状态文件不存在，首次运行可能尚未生成")

    # 2. 提取域名数据（关键：适配外层 domains 嵌套结构）
    domains_data = raw_state.get("domains", {})
    
    if domains_data:
        for domain, info in domains_data.items():
            expires_at = info.get("expires_at", "N/A")
            renew_before = info.get("renew_before_days", "N/A")
            source = info.get("source", "N/A")
            
            # 计算真实剩余天数
            days_left = "N/A"
            if expires_at != "N/A":
                try:
                    exp_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    days_left = (exp_dt - now).days
                except:
                    pass
            
            # 状态标识（企业微信支持的颜色标签）
            if isinstance(days_left, int):
                if days_left < 30:
                    status_color = "warning"  # 橙色
                    status_text = "🔴 即将过期"
                elif days_left < 90:
                    status_color = "comment"   # 灰色
                    status_text = "🟡 临近续期窗口"
                else:
                    status_color = "info"      # 绿色
                    status_text = "🟢 状态正常"
            else:
                status_color = "comment"
                status_text = "⚠️ 状态未知"

            # 拼接单行通知内容（用<br>换行，企业微信 Markdown 支持）
            line = f"<font color=\"{status_color}\">【{status_text}】</font><br>"
            line += f"▸ 域名：<code>{domain}</code><br>"
            line += f"▸ 到期时间：<code>{expires_at}</code><br>"
            line += f"▸ 剩余天数：<code>{days_left}</code> 天<br>"
            line += f"▸ 提前续期阈值：<code>{renew_before}</code> 天<br>"
            line += f"▸ 数据来源：<code>{source}</code>"
            domain_lines.append(line)
    elif not domain_lines:
        domain_lines.append("⚠️ 状态文件中无域名数据")

    # 3. 状态映射
    emoji_map = {
        "SUCCESS": "✅",
        "FAILURE": "❌",
        "CANCELLED": "⛔",
        "SKIPPED": "⏭️"
    }
    status_map = {
        "SUCCESS": "执行成功",
        "FAILURE": "执行失败",
        "CANCELLED": "已取消",
        "SKIPPED": "已跳过"
    }
    emoji = emoji_map.get(job_status, "❓")
    status_desc = status_map.get(job_status, "未知状态")

    # 4. 组装企业微信 Markdown 内容（格式清晰，适配手机端）
    content = f"""## {emoji} DNSHE 自动续期任务 {status_desc}
<font color="comment">运行时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC</font><br>
<font color="comment">运行状态：<code>{job_status.upper()}</code></font><br><br>

### 📋 域名状态明细
{"<br><br>".join(domain_lines)}<br><br>

---
🔗 <a href="{run_url}">点击查看完整运行日志</a>
"""

    # 5. 发送请求
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content.strip()}
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
