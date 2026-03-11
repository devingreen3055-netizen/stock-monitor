import requests

url = "https://qt.gtimg.cn/q=sh600519"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://gu.qq.com/"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"编码: {response.encoding}")
    print(f"内容: {response.text[:500]}")
    
    if "~" in response.text:
        price = response.text.split("~")[3]
        print(f"解析价格: {price}")
    else:
        print("格式错误")
except Exception as e:
    print(f"错误: {e}")
