"""
账户余额检查工具
"""
from okx_http_client import client
from config import DEFAULT_INST_ID

def check_balance():
    """检查账户余额"""
    print("=== OKX账户余额检查 ===")
    
    # 获取账户余额
    result = client.get_account_balance()
    if not result or result.get('code') != '0':
        print("❌ 无法获取账户余额")
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
    
    print(f"\n📊 交易资金状态:")
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
    
    # 交易建议
    print(f"\n💡 交易建议:")
    if usdt_balance < 10:
        print("  ⚠️  USDT余额不足，建议充值USDT进行交易")
    if btc_balance < 0.001:
        print("  ⚠️  BTC余额不足，建议充值BTC或先买入BTC")
    
    if usdt_balance >= 10:
        print("  ✅ 有足够USDT进行BTC交易")
    if btc_balance >= 0.001:
        print("  ✅ 有足够BTC进行交易")
    
    # 显示所有余额
    print(f"\n💰 所有代币余额:")
    has_balance = False
    for detail in details:
        avail_bal = float(detail['availBal'])
        if avail_bal > 0:
            has_balance = True
            print(f"  {detail['ccy']}: {avail_bal}")
    
    if not has_balance:
        print("  无任何代币余额")
    
    print(f"\n📝 操作建议:")
    print("1. 如需交易BTC，请先充值USDT")
    print("2. 或者将现有代币兑换成USDT")
    print("3. 充值后重新运行交易系统")

if __name__ == "__main__":
    check_balance()
