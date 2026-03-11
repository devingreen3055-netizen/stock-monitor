import os
import akshare as ak
import requests

# 配置部分（只需改这里）
STOCK_CODE = "600519"        # 股票代码，注意：去掉前缀 sh/sz，直接写数字代码
TARGET_PRICE = 105.0         # 你的目标价
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")  # 从GitHub Secrets读取

def get_price():
    """获取股票价格（使用AKShare库）"""
    try:
        # 调用 AKShare 接口获取实时行情
        stock_df = ak.stock_zh_a_spot_em()
        
        # 根据股票代码筛选数据（注意：AKShare 返回的代码列是字符串格式）
        stock_info = stock_df[stock_df["代码"] == STOCK_CODE]
        
        # 检查是否获取到了数据
        if stock_info.empty:
            print(f"[错误] 未找到股票代码 {STOCK_CODE}，请检查代码是否正确。")
            return None
            
        # 提取最新价（通常是第4列，索引为3）
        current_price = float(stock_info.iloc[0, 3])
        print(f"[调试] 成功获取 {STOCK_CODE} 价格: {current_price}")
        return current_price
        
    except Exception as e:
        print(f"[错误] 获取股价失败: {e}")
        return None

def send_feishu_message(msg):
    """发送消息到飞书（与原脚本保持一致）"""
    if not FEISHU_WEBHOOK:
        print("[错误] 飞书Webhook未配置！")
        return False
        
    payload = {
        "msg_type": "text",
        "content": {
            "text": msg
        }
    }
    
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=payload, timeout=5)
        print(f"[调试] 飞书响应: {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        print(f"[错误] 发送飞书消息失败: {e}")
        return False

if __name__ == "__main__":
    price = get_price()
    if price is None:
        print("[错误] 获取股价失败，任务终止。")
    else:
        print(f"股票 {STOCK_CODE} 当前价格: {price} 元")
        if price >= TARGET_PRICE:
            msg = f"🚨 股价提醒：{STOCK_CODE} 当前价格 {price} 元，已达到目标价 {TARGET_PRICE} 元！"
            print(f"[调试] 准备发送消息: {msg}")
            send_feishu_message(msg)
        else:
            print(f"当前价格 {price} 元，未达到目标价 {TARGET_PRICE} 元，不发送消息。")
