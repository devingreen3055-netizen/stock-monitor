import os
import akshare as ak
import requests
from datetime import datetime

# ====== 配置部分（只需改这里）======
STOCK_CODE = "600519"        # 股票代码（AKShare 不需要前缀，直接数字）
TARGET_PRICE = 105.0         # 你的目标价（根据实际股价调整）
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")  # 从GitHub Secrets读取

# ====== 工具函数 ======
def get_price():
    """获取股票价格（使用AKShare）"""
    try:
        # 调用 AKShare 接口获取实时行情
        stock_df = ak.stock_zh_a_spot_em()
        # 筛选目标股票（注意：AKShare 返回的代码是字符串，如 "600519"）
        stock_info = stock_df[stock_df["代码"] == STOCK_CODE]
        if stock_info.empty:
            print(f"[错误] 未找到股票代码 {STOCK_CODE} 的行情数据")
            return None
        # 提取当前价格（AKShare 中“最新价”列的字段是“最新价”）
        current_price = float(stock_info.iloc[0]["最新价"])
        print(f"[调试] 股票 {STOCK_CODE} 当前价格：{current_price}")
        return current_price
    except Exception as e:
        print(f"[错误] 获取股价失败：{str(e)}")
        return None

def send_feishu_message(content):
    """发送消息到飞书机器人"""
    if not FEISHU_WEBHOOK:
        print("[错误] 飞书 Webhook 未配置（FEISHU_WEBHOOK 为空）")
        return False
    try:
        payload = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        response = requests.post(
            FEISHU_WEBHOOK,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"[调试] 飞书响应：{response.status_code}, {response.text}")
        if response.status_code == 200:
            print("[调试] 飞书消息发送成功")
            return True
        else:
            print(f"[错误] 飞书消息发送失败，状态码：{response.status_code}")
            return False
    except Exception as e:
        print(f"[错误] 发送飞书消息时异常：{str(e)}")
        return False

# ====== 主逻辑 ======
if __name__ == "__main__":
    print(f"===== 股票监控启动时间：{datetime.now()} =====")
    current_price = get_price()
    if current_price is None:
        print("[错误] 无法获取股价，监控终止")
    else:
        # 检查是否达到目标价
        if current_price >= TARGET_PRICE:
            message = f"【股票监控提醒】股票 {STOCK_CODE} 当前价格 {current_price}，已达到目标价 {TARGET_PRICE}！"
            print(f"[触发] {message}")
            send_feishu_message(message)
        else:
            print(f"[正常] 当前价格 {current_price} < 目标价 {TARGET_PRICE}，暂不提醒")
    print("===== 监控结束 =====")
