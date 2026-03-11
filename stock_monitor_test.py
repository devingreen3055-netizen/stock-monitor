"""
股票监控测试脚本 - 强制发送测试消息
用于验证飞书推送功能是否正常
"""

import os
import requests
from datetime import datetime

# 从环境变量读取飞书Webhook
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

# 测试股票列表
[
    ["sh600343", "航天动力", None],      # 价格设为None表示使用当日开盘价
    ["sz000547", "航天发展", None],
    ["sh601698", "中国卫通", None],
    ["sh603993", "洛阳钼业", None],
    ["sh601138", "工业富联", None],
]
def send_feishu_message(content):
    """发送消息到飞书"""
    if not FEISHU_WEBHOOK:
        print("❌ 未配置飞书Webhook")
        return False
    
    payload = {
        "msg_type": "text",
        "content": {
            "text": content
        }
    }
    
    try:
        response = requests.post(
            FEISHU_WEBHOOK,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"飞书响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 or data.get("StatusCode") == 0:
                return True
        
    except Exception as e:
        print(f"❌ 发送失败: {e}")
    
    return False

def create_test_message(stock_code, stock_name, test_type="normal"):
    """创建测试消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if test_type == "normal":
        emoji = "🔧"
        title = "股票监控系统测试"
    elif test_type == "alert":
        emoji = "🚨"
        title = "模拟股价提醒测试"
    else:
        emoji = "✅"
        title = "系统功能验证测试"
    
    # 模拟一些数据
    current_price = 100.50
    change_percent = 5.25
    change_amount = 5.00
    high_price = 102.00
    low_price = 99.50
    
    message = f"{emoji} {title}\n\n"
    message += f"📊 股票代码: {stock_code}\n"
    message += f"📈 股票名称: {stock_name}\n"
    message += f"💰 模拟当前价: {current_price:.2f} 元\n"
    message += f"📈 模拟涨跌幅: {change_percent:+.2f}%\n"
    message += f"📉 模拟涨跌额: {change_amount:+.2f} 元\n"
    message += f"⬆️ 模拟最高价: {high_price:.2f} 元\n"
    message += f"⬇️ 模拟最低价: {low_price:.2f} 元\n"
    message += f"⏰ 测试时间: {timestamp}\n\n"
    
    if test_type == "alert":
        message += f"🎯 模拟触发: 5% 涨幅阈值\n"
        message += f"💡 这是模拟的股价提醒消息\n"
    else:
        message += f"💡 这是系统功能测试消息\n"
    
    message += f"✅ 如果收到此消息，说明飞书推送功能正常"
    
    return message

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 股票监控系统 - 功能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试股票数量: {len(TEST_STOCKS)}")
    print("=" * 60)
    
    if not FEISHU_WEBHOOK:
        print("❌ 错误: 未配置飞书Webhook")
        print("请在GitHub Secrets中设置FEISHU_WEBHOOK")
        return
    
    print(f"✅ 飞书Webhook已配置: {FEISHU_WEBHOOK[:50]}...")
    print("")
    
    # 发送三种类型的测试消息
    test_types = [
        ("normal", "🔧 普通测试"),
        ("alert", "🚨 预警测试"),
    ]
    
    total_sent = 0
    total_failed = 0
    
    for stock_code, stock_name in TEST_STOCKS[:2]:  # 只测试前2只，避免消息过多
        for test_type, test_desc in test_types:
            print(f"发送 {test_desc} - {stock_code} ({stock_name})...")
            
            message = create_test_message(stock_code, stock_name, test_type)
            
            if send_feishu_message(message):
                print(f"  ✅ 发送成功")
                total_sent += 1
            else:
                print(f"  ❌ 发送失败")
                total_failed += 1
            
            # 短暂延迟，避免频率限制
            import time
            time.sleep(1)
    
    # 发送汇总消息
    summary = f"📊 测试运行汇总\n\n"
    summary += f"测试时间: {datetime.now().strftime('%H:%M:%S')}\n"
    summary += f"测试股票: {len(TEST_STOCKS[:2])} 只\n"
    summary += f"测试类型: {len(test_types)} 种\n"
    summary += f"成功发送: {total_sent} 条\n"
    summary += f"发送失败: {total_failed} 条\n"
    summary += f"成功率: {total_sent/(total_sent+total_failed)*100:.1f}%\n\n"
    
    if total_failed == 0:
        summary += f"🎉 所有测试消息发送成功！\n"
        summary += f"✅ 系统功能正常"
    else:
        summary += f"⚠️ 部分消息发送失败\n"
        summary += f"❌ 请检查飞书机器人配置"
    
    print(f"\n发送汇总消息...")
    send_feishu_message(summary)
    
    print("\n" + "=" * 60)
    print(f"测试完成")
    print(f"成功: {total_sent}, 失败: {total_failed}")
    print("=" * 60)

if __name__ == "__main__":
    main()
