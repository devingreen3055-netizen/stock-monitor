import os
import json
import requests
import time
from datetime import datetime, timedelta
import stocks_config
from collections import defaultdict

# 从环境变量读取飞书Webhook
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

class StockMonitor:
    def __init__(self):
        self.stocks = stocks_config.STOCKS_TO_MONITOR
        self.thresholds = stocks_config.THRESHOLDS
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        # 存储状态：{股票代码: {开盘价: xx, 最高涨幅: xx, 已发送提醒: [threshold1, threshold2]}}
        self.state_file = "stock_state.json"
        self.state = self.load_state()
        
        # 当天已触发提醒记录
        self.triggered_today = defaultdict(list)
        
    def load_state(self):
        """加载状态文件"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_state(self):
        """保存状态文件"""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def get_stock_data(self, stock_code):
        """获取股票实时数据（腾讯财经接口）"""
        url = f"https://qt.gtimg.cn/q={stock_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://gu.qq.com/"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'gb2312'
            
            if response.status_code == 200 and response.text:
                # 解析数据格式
                data = response.text
                if "~" in data:
                    parts = data.split("~")
                    
                    if len(parts) > 40:  # 腾讯接口返回完整数据
                        stock_info = {
                            "code": stock_code,
                            "name": parts[1],  # 股票名称
                            "current": float(parts[3]),  # 当前价
                            "open": float(parts[5]),  # 开盘价
                            "high": float(parts[33]),  # 最高价
                            "low": float(parts[34]),  # 最低价
                            "close": float(parts[4]),  # 昨收
                            "change": float(parts[31]),  # 涨跌额
                            "change_percent": float(parts[32]),  # 涨跌幅百分比
                            "volume": parts[6],  # 成交量
                            "amount": parts[37],  # 成交额
                            "time": parts[30],  # 时间
                        }
                        return stock_info
                        
        except Exception as e:
            print(f"获取 {stock_code} 数据失败: {e}")
        
        return None
    
    def calculate_increase(self, stock_code, stock_info, base_price=None):
        """计算相对于基准价的涨跌幅"""
        if base_price is None or base_price == 0:
            # 使用当天开盘价作为基准
            base_price = stock_info.get("open", stock_info.get("close"))
            
        current_price = stock_info["current"]
        
        if base_price and base_price > 0:
            increase = ((current_price - base_price) / base_price) * 100
            increase_amount = current_price - base_price
        else:
            # 使用接口提供的涨跌幅
            increase = stock_info["change_percent"]
            increase_amount = stock_info["change"]
            
        return increase, increase_amount
    
    def check_thresholds(self, stock_code, increase, stock_info):
        """检查是否达到提醒阈值"""
        stock_name = stock_info["name"]
        current_price = stock_info["current"]
        high_price = stock_info["high"]
        low_price = stock_info["low"]
        change_amount = stock_info["change"]
        change_percent = stock_info["change_percent"]
        
        # 获取股票当天的状态
        if stock_code not in self.state:
            self.state[stock_code] = {
                "max_increase": 0,
                "triggered": []
            }
        
        stock_state = self.state[stock_code]
        triggered_levels = []
        
        # 检查每个阈值
        for threshold, message_type in sorted(self.thresholds.items()):
            if increase >= threshold and threshold not in stock_state["triggered"]:
                # 记录已触发
                stock_state["triggered"].append(threshold)
                stock_state["max_increase"] = max(stock_state["max_increase"], increase)
                
                # 构建消息
                message = self.format_message(
                    stock_code, stock_name, current_price, 
                    change_percent, change_amount, 
                    high_price, low_price, increase, 
                    message_type, threshold
                )
                
                triggered_levels.append((threshold, message))
        
        # 更新状态
        self.state[stock_code] = stock_state
        
        return triggered_levels
    
    def format_message(self, code, name, current, change_percent, 
                      change_amount, high, low, real_increase, 
                      message_type, threshold):
        """格式化飞书消息"""
        
        # 确定表情符号
        if threshold >= 10:
            emoji = "🚨"
        elif threshold >= 7.5:
            emoji = "🔥"
        elif threshold >= 5:
            emoji = "🚀"
        else:
            emoji = "📈"
        
        message = f"{emoji} {message_type}\n\n"
        message += f"📊 股票代码: {code}\n"
        message += f"📈 股票名称: {name}\n"
        message += f"💰 当前价格: {current:.2f} 元\n"
        message += f"📈 涨跌幅: {change_percent:+.2f}%\n"
        message += f"📉 涨跌额: {change_amount:+.2f} 元\n"
        message += f"⬆️ 最高价: {high:.2f} 元\n"
        message += f"⬇️ 最低价: {low:.2f} 元\n"
        
        if real_increase > 0:
            message += f"🎯 今日累计涨幅: {real_increase:+.2f}%\n"
        
        message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"🔔 触发阈值: {threshold}%"
        
        return message
    
    def send_feishu_message(self, content):
        """发送消息到飞书"""
        if not FEISHU_WEBHOOK:
            print("未配置飞书Webhook")
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
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 or data.get("StatusCode") == 0:
                    return True
            
        except Exception as e:
            print(f"发送飞书消息失败: {e}")
        
        return False
    
    def reset_daily_state(self):
        """每日重置状态（开盘时调用）"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if self.today != today:
            print(f"新的一天开始: {today}")
            self.today = today
            self.state = {}  # 清空前一天的状态
            self.save_state()
            return True
        
        return False
    
    def is_trading_time(self):
        """判断是否为交易时间"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 检查是否为交易日（周一至周五）
        if now.weekday() >= 5:  # 5=周六, 6=周日
            return False
        
        # 检查是否在交易时间内
        morning_start = stocks_config.TRADING_HOURS["morning_start"]
        morning_end = stocks_config.TRADING_HOURS["morning_end"]
        afternoon_start = stocks_config.TRADING_HOURS["afternoon_start"]
        afternoon_end = stocks_config.TRADING_HOURS["afternoon_end"]
        
        return (morning_start <= current_time <= morning_end) or \
               (afternoon_start <= current_time <= afternoon_end)
    
    def run_monitoring(self):
        """执行监控主循环"""
        print("=" * 60)
        print(f"股票监控系统启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"监控股票数量: {len(self.stocks)}")
        print(f"监控阈值: {list(self.thresholds.keys())}")
        print("=" * 60)
        
        # 每日重置
        self.reset_daily_state()
        
        # 如果不在交易时间，只运行一次测试
        if not self.is_trading_time():
            print("当前非交易时间，运行一次测试")
            self.test_mode = True
        else:
            self.test_mode = False
            print("交易时间内，开始监控...")
        
        # 监控循环
        stocks_triggered = 0
        total_messages = 0
        
        for stock_code, stock_name, base_price in self.stocks:
            print(f"\n🔍 监控 {stock_code} ({stock_name})...")
            
            # 获取股票数据
            stock_info = self.get_stock_data(stock_code)
            if not stock_info:
                print(f"  ❌ 无法获取 {stock_code} 数据")
                continue
            
            # 计算涨跌幅
            increase, increase_amount = self.calculate_increase(
                stock_code, stock_info, base_price
            )
            
            print(f"  ✅ 当前价: {stock_info['current']:.2f}")
            print(f"  📈 涨跌幅: {increase:+.2f}%")
            
            # 检查阈值
            triggered = self.check_thresholds(stock_code, increase, stock_info)
            
            # 发送提醒
            for threshold, message in triggered:
                print(f"  🎯 触发 {threshold}% 阈值提醒")
                
                if not self.test_mode or threshold <= 5:  # 测试模式只发低级别
                    if self.send_feishu_message(message):
                        print(f"  ✅ 提醒发送成功")
                        total_messages += 1
                    else:
                        print(f"  ❌ 提醒发送失败")
            
            if triggered:
                stocks_triggered += 1
        
        # 保存状态
        self.save_state()
        
        # 发送每日汇总（如果有触发）
        if stocks_triggered > 0 and not self.test_mode:
            summary = self.get_daily_summary()
            if summary:
                self.send_feishu_message(summary)
        
        print("\n" + "=" * 60)
        print(f"监控完成")
        print(f"触发股票: {stocks_triggered}/{len(self.stocks)}")
        print(f"发送消息: {total_messages} 条")
        print("=" * 60)
    
    def get_daily_summary(self):
        """获取当日汇总信息"""
        if not self.state:
            return None
        
        summary = "📊 当日监控汇总\n\n"
        for stock_code, stock_state in self.state.items():
            if stock_state["triggered"]:
                # 找到对应的股票名称
                stock_name = None
                for code, name, _ in self.stocks:
                    if code == stock_code:
                        stock_name = name
                        break
                
                if stock_name:
                    max_threshold = max(stock_state["triggered"])
                    summary += f"• {stock_code} ({stock_name}): 最高触发 {max_threshold}%\n"
        
        if summary.count('\n') > 2:  # 有实际内容
            summary += f"\n⏰ 汇总时间: {datetime.now().strftime('%H:%M:%S')}"
            return summary
        
        return None

def main():
    """主函数"""
    monitor = StockMonitor()
    monitor.run_monitoring()

if __name__ == "__main__":
    main()
