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
# 在文件最底部，找到 if __name__ == "__main__": 部分
# 修改后的主程序如下：

if __name__ == "__main__":
    print("=" * 50)
    print(f"股票监控程序启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监控股票: {STOCK_CODE}, 目标价格: {TARGET_PRICE}")
    print("=" * 50)
    
    # 获取当前价格
    current_price = get_price()
    
    if current_price is None:
        print("❌ 无法获取股价，程序退出")
        # 测试：即使获取失败，也发送测试消息
        message = f"🔧 飞书消息发送测试（当前无法获取股价）\n" \
                 f"时间: {datetime.now().strftime('%H:%M:%S')}\n" \
                 f"股票: {STOCK_CODE}\n\n" \
                 f"✅ 此消息仅用于测试飞书推送功能是否正常"
        print("测试模式：尝试发送飞书测试消息...")
        if send_feishu_message(message):
            print("✅ 测试消息发送完成")
        else:
            print("❌ 测试消息发送失败")
        exit(1)
    
    print(f"当前价格: {current_price:.2f} 元")
    print(f"目标价格: {TARGET_PRICE:.2f} 元")
    
    # 修改这里：强制触发消息发送（用于测试）
    # 无论股价是否达标，都发送一条测试消息
    test_mode = True  # 设为True强制发送测试消息
    
    if test_mode or current_price >= TARGET_PRICE:
        if test_mode:
            profit_rate = 5.5  # 模拟收益率
            message = f"🔧 飞书消息发送测试\n\n" \
                     f"股票代码: {STOCK_CODE}\n" \
                     f"模拟价格: {current_price:.2f} 元\n" \
                     f"模拟目标: {TARGET_PRICE:.2f} 元\n" \
                     f"模拟收益率: +{profit_rate:.2f}%\n\n" \
                     f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                     f"📱 此消息仅用于测试推送功能是否正常"
            print("🔄 测试模式：强制发送测试消息...")
        else:
            profit_rate = ((current_price - TARGET_PRICE) / TARGET_PRICE * 100)
            message = f"🚨 股价提醒\n\n" \
                     f"股票代码: {STOCK_CODE}\n" \
                     f"当前价格: {current_price:.2f} 元\n" \
                     f"目标价格: {TARGET_PRICE:.2f} 元\n" \
                     f"收益率: +{profit_rate:.2f}%\n\n" \
                     f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            print("🎯 达到目标价！准备发送提醒...")
        
        # 发送飞书消息
        if send_feishu_message(message):
            print("✅ 消息发送完成")
        else:
            print("❌ 消息发送失败")
    else:
        print(f"📉 未达到目标价，还差 {TARGET_PRICE - current_price:.2f} 元")
    
    print("=" * 50)
    print("程序执行完成")
