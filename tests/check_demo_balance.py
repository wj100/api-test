"""
模拟交易账户余额检查工具
"""
from okx_http_client import client
from config import DEFAULT_INST_ID, FLAG

def check_demo_balance():
    """检查模拟交易账户余额"""
    print("=== OKX模拟交易账户检查 ===")
    print(f"当前模式: {'模拟交易' if FLAG == '1' else '实盘交易'}")
    
    # 获取账户余额
    result = client.get_account_balance()
    if not result or result.get('code') != '0':
        print("❌ 无法获取模拟交易账户余额")
        return
    
    details = result['data'][0]['details']
    
    # 检查USDT和BTC
    usdt_balance = 0
    btc_balance = 0
    
    for detail in details:
        if detail['ccy'] == 'USDT':
            usdt_balance = float(detail['availBal'])
        elif detail['ccy'] == 'BTC':
            btc_balance = float(detail['availBal'])
    
    print(f"\n📊 模拟交易资金状态:")
    print(f"  USDT余额: {usdt_balance}")
    print(f"  BTC余额: {btc_balance}")
    
    # 获取BTC价格
    ticker = client.get_ticker(DEFAULT_INST_ID)
    if ticker and ticker.get('code') == '0':
        btc_price = float(ticker['data'][0]['last'])
        print(f"  BTC价格: ${btc_price}")
        
        # 计算总价值
        total_value = usdt_balance + (btc_balance * btc_price)
        print(f"  总资产价值: ${total_value:.2f}")
    
    # 显示所有余额
    print(f"\n💰 模拟账户所有代币:")
    has_balance = False
    for detail in details:
        avail_bal = float(detail['availBal'])
        if avail_bal > 0:
            has_balance = True
            print(f"  {detail['ccy']}: {avail_bal}")
    
    if not has_balance:
        print("  无任何代币余额")
    
    # 模拟交易建议
    print(f"\n💡 模拟交易建议:")
    if usdt_balance == 0 and btc_balance == 0:
        print("  ⚠️  模拟账户中没有USDT和BTC")
        print("  📝 解决方案:")
        print("     1. 登录OKX网页版")
        print("     2. 切换到模拟交易模式")
        print("     3. 系统会自动分配模拟资金（通常10,000 USDT）")
        print("     4. 或者手动在模拟交易界面充值")
    else:
        if usdt_balance >= 10:
            print("  ✅ 有足够USDT进行BTC模拟交易")
        if btc_balance >= 0.001:
            print("  ✅ 有足够BTC进行模拟交易")
    
    print(f"\n🔧 模拟交易设置:")
    print(f"  API端点: {client.base_url}")
    print(f"  交易模式: {FLAG} ({'模拟' if FLAG == '1' else '实盘'})")
    print(f"  交易对: {DEFAULT_INST_ID}")

if __name__ == "__main__":
    check_demo_balance()
