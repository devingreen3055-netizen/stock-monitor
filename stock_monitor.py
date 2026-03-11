import os
import requests
from datetime import datetime

# ========== 配置 ==========
STOCK_CODE = "sh600519"      # 注意：腾讯接口需要前缀 sh/sz
TARGET_PRICE = 105.0
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

# ========== 获取股价 ==========
def get_price_tencent():
    """使用腾讯财经接口（GitHub Actions兼容）"""
    url = f"https://qt.gtimg.cn/q={STOCK_CODE}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://gu.qq.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    try:
        print(f"请求URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gb2312'
        
        print(f"状态码: {response.status_code}")
        print(f"原始响应: {response.text[:200]}...")
        
        if response.status_code == 200 and response.text:
            # 格式: v_sh600519="1~贵州茅台~1950.00~1950.50~..."
            if "~" in response.text:
                parts = response.text.split("~")
                if len(parts) > 3:
                    price_str = parts[3]  # 当前价格在第4个位置
                    if price_str and price_str != "":
                        price = float(price_str)
                        print(f"解析成功: {price}")
                        return price
                    else:
                        print("价格字符串为空")
                else:
                    print(f"数据格式异常，字段不足: {len(parts)}个字段")
            else:
                print("响应中不包含波浪线分隔符")
        else:
            print(f"请求失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"腾讯接口异常: {type(e).__name__}: {e}")
    
    return None

def get_price_sina():
    """新浪财经接口（备用）"""
    url = f"https://hq.sinajs.cn/list={STOCK_CODE}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.encoding = 'gbk'
        
        if response.status_code == 200 and '"' in response.text:
            data = response.text.split('"')[1]
            price_str = data.split(',')[3]
            return float(price_str)
    except:
        pass
    return None

def get_price():
    """获取股价，带重试"""
    # 先尝试腾讯
    price = get_price_tencent()
    if price is not None:
        return price
    
    print("腾讯接口失败，尝试新浪接口...")
    # 再尝试新浪
    return get_price_sina()

# ========== 发送飞书 ==========
def send_feishu_message(content):
    """发送消息到飞书"""
    if not FEISHU_WEBHOOK:
        print("错误: FEISHU_WEBHOOK 未设置")
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
        print(f"飞书返回: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 or data.get("StatusCode") == 0:
                print("✅ 飞书消息发送成功")
                return True
            else:
                print(f"❌ 飞书返回错误: {data}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 发送消息异常: {type(e).__name__}: {e}")
        return False

# ========== 主程序 ==========
if __name__ == "__main__":
    print("=" * 50)
    print(f"股票监控启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"股票: {STOCK_CODE}, 目标: {TARGET_PRICE}")
    print(f"飞书Webhook配置: {'✅ 已配置' if FEISHU_WEBHOOK else '❌ 未配置'}")
    print("=" * 50)
    
    # 强制测试模式：无论价格如何都发送消息
    TEST_MODE = False  # 设为True强制发送测试消息
    
    # 获取股价
    current_price = get_price()
    
    if current_price is None:
        print("❌ 获取股价失败")
        if TEST_MODE:
            message = "🔧 测试消息\n获取股价失败，但飞书功能正常\n时间: " + datetime.now().strftime("%H:%M:%S")
            send_feishu_message(message)
        exit(1)
    
    print(f"当前价格: {current_price:.2f} 元")
    print(f"目标价格: {TARGET_PRICE:.2f} 元")
    
    # 判断逻辑
    if TEST_MODE or current_price >= TARGET_PRICE:
        if TEST_MODE:
            message = f"🔧 测试消息\n股票: {STOCK_CODE}\n当前: {current_price:.2f}元\n目标: {TARGET_PRICE:.2f}元\n时间: {datetime.now().strftime('%H:%M:%S')}"
            print("🔄 测试模式：发送测试消息")
        else:
            profit = ((current_price - TARGET_PRICE) / TARGET_PRICE * 100)
            message = f"🚨 股价提醒\n\n股票: {STOCK_CODE}\n当前: {current_price:.2f}元\n目标: {TARGET_PRICE:.2f}元\n涨幅: +{profit:.2f}%\n时间: {datetime.now().strftime('%H:%M:%S')}"
            print("🎯 达到目标价！发送提醒...")
        
        if send_feishu_message(message):
            print("✅ 流程完成")
        else:
            print("❌ 发送失败")
    else:
        diff = TARGET_PRICE - current_price
        print(f"📉 未达到目标，还差 {diff:.2f} 元 ({diff/current_price*100:.1f}%)")
    
    print("=" * 50)
