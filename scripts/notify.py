import os
import json
from datetime import datetime, timezone

def send_wecom_notification(job_status, run_url):
    """发送企业微信通知（完全适配你的状态文件结构）"""
    webhook_url = os.environ.get("WECOM_WEBHOOK")
    if not webhook_url:
        print("⚠️ 未配置 WECOM_WEBHOOK，跳过通知")
        return

    state_path = "state/domains-state.json"
    domain_lines = []
    raw_state = "文件不存在"

    # 1. 读取并解析状态文件（你的状态文件结构是：key=域名，value=域名详情）
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                raw_state = f.read()
                if not raw_state.strip():
                    domain_lines.append("⚠️ 状态文件为空")
                else:
                    state = json.loads(raw_state)
                    # 你的状态文件 key 就是域名，所以直接遍历 items()
                    for domain, info in state.items():
                        exp_str = info.get("expires_at", "N/A")
                        renewed_at = info.get("last_renewed_at", "")
                        
                        # 计算剩余天数（适配你的日期格式：YYYY-MM-DD HH:MM）
                        days_left = "N/A"
                        if exp_str != "N/A":
                            try:
                                exp_dt = datetime.strptime(exp_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                                now = datetime.now(timezone.utc)
                                days_left = (exp_dt - now).days
                            except Exception as e:
                                days_left = f"解析失败: {e}"

                        # 拼接单行信息（用<br>换行，企业微信 markdown 支持）
                        line = f"### 🔹 域名：`{domain}`<br>"
                        line += f"&emsp;到期时间：`{exp_str}`<br>"
                        if isinstance(days_left, int):
                            # 剩余天数预警标识
                            if days_left < 30:
                                warn = "🔴 即将过期！"
                            elif days_left < 90:
                                warn = "🟡 即将进入续期窗口"
                            else:
                                warn = "🟢 状态正常"
                            line += f"&emsp;剩余天数：**{days_left}** 天 {warn}<br>"
                        if renewed_at:
                            line += f"&emsp;最近续期时间：`{renewed_at}`<br>"
                        domain_lines.append(line)
        except Exception as e:
            domain_lines.append(f"❌ 解析状态文件失败: {e}<br>原始内容：{raw_state[:500]}...")
    else:
        domain_lines.append("⚠️ 状态文件不存在（首次运行/脚本执行异常）")

    # 2. 状态映射（对应 GitHub Actions 的 job.status）
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

    # 3. 组装企业微信 Markdown 内容（完全适配手机端阅读）
    content = f"""## {emoji} DNSHE 自动续期任务 {status_desc}
**运行时间**：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC<br>
**运行状态**：`{job_status.upper()}`<br><br>

### 📋 域名状态明细
{''.join(domain_lines) if domain_lines else '❌ 无域名数据'}<br><br>

---
"""
    # 4. 发送请求
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
        print(f"❌ 发送通知异常: {e}")

if __name__ == "__main__":
    JOB_STATUS = os.environ.get("STATUS", "UNKNOWN")
    RUN_URL = os.environ.get("RUN_URL", "#")
    send_wecom_notification(JOB_STATUS, RUN_URL)
