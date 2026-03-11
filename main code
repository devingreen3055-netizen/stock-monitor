import os
import requests

# 配置部分（只需改这里）
STOCK_CODE = "sh600519"      # 股票代码，如：sh600519（上证），sz000858（深证）
TARGET_PRICE = 105.0         # 你的目标价
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")  # 从GitHub Secrets读取

def get_price():
    """获取股票价格（从新浪财经）"""
    url = f"http://hq.sinajs.cn/list={STOCK_CODE}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
    response.encoding = 'gbk'
    data = response.text
    
    # 解析数据：格式是 var hq_str_sh600519="茅台,1950.00,..."
    if '"' in data:
        price_str = data.split('"')[1].split(',')[3]  # 当前价格在第4个位置
        return float(price_str)
    return None

def send_message(msg):
    """发送消息到飞书"""
    data = {"msg_type": "text", "content": {"text": msg}}
    requests.post(FEISHU_WEBHOOK, json=data)

if __name__ == "__main__":
    # 1. 获取当前价格
    current_price = get_price()
    if current_price is None:
        print("获取价格失败")
        exit(1)
    
    print(f"股票 {STOCK_CODE} 当前价格: {current_price} 元")
    
    # 2. 判断是否达到目标
    if current_price >= TARGET_PRICE:
        # 3. 发送消息
        message = f"🚨 提醒：{STOCK_CODE} 当前价格 {current_price} 元，已触及目标价 {TARGET_PRICE} 元！"
        print(message)
        send_message(message)
