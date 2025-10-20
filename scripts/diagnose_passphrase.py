"""
诊断Passphrase问题
测试不同的Passphrase
"""
import requests
import time
import hmac
import hashlib
import base64
import json
from config import API_KEY, SECRET_KEY, PASSPHRASE

def test_passphrase(passphrase):
    """测试特定的passphrase"""
    base_url = "https://www.okx.com"
    endpoint = "/api/v5/account/balance"
    url = base_url + endpoint
    
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    method = "GET"
    body = ""
    message = timestamp + method + endpoint + body
    
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature).decode('utf-8')
    
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        
        if response.status_code == 200 and result.get('code') == '0':
            return True, result
        else:
            return False, result
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    print("=== OKX API Passphrase诊断 ===")
    print(f"API Key: {API_KEY}")
    print(f"Secret Key: {SECRET_KEY}")
    print()
    
    # 测试不同的passphrase
    passphrases_to_test = [
        PASSPHRASE,  # 当前配置的
        "one",       # 之前测试过的
        "1",         # 简单数字
        "okx",       # 常见密码
        "test",      # 测试密码
        "123456",    # 常见密码
        "password",  # 常见密码
    ]
    
    for i, passphrase in enumerate(passphrases_to_test, 1):
        print(f"{i}. 测试Passphrase: '{passphrase}'")
        success, result = test_passphrase(passphrase)
        
        if success:
            print(f"   ✅ 成功！正确的Passphrase是: '{passphrase}'")
            print(f"   账户余额: {result}")
            break
        else:
            print(f"   ❌ 失败: {result}")
        print()
    
    print("诊断完成")

if __name__ == "__main__":
    main()
