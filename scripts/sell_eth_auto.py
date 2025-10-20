"""
自动卖出ETH脚本
将账户中的所有ETH卖出为USDT (自动确认)
"""
from okx_http_client import client
from config import TRADING_MODE
import time

def get_eth_balance():
    """获取ETH余额"""
    result = client.get_account_balance()
    if result and result.get('code') == '0':
        details = result['data'][0]['details']
        for detail in details:
            if detail['ccy'] == 'ETH':
                return float(detail['availBal'])
    return 0

def get_eth_price():
    """获取ETH价格"""
    ticker = client.get_ticker("ETH-USDT")
    if ticker and ticker.get('code') == '0':
        return float(ticker['data'][0]['last'])
    return None

def sell_eth(amount):
    """卖出ETH"""
    try:
        result = client.place_order(
            inst_id="ETH-USDT",
            side="sell",
            ord_type="market",
            sz=str(amount)
        )
        return result
    except Exception as e:
        print(f"卖出ETH失败: {e}")
        return None

def main():
    """主函数"""
    print(f"=== ETH自动卖出工具 - {TRADING_MODE}模式 ===")
    print()
    
    # 检查ETH余额
    eth_balance = get_eth_balance()
    if eth_balance <= 0:
        print("❌ 账户中没有ETH可卖出")
        return
    
    print(f"📊 当前ETH余额: {eth_balance}")
    
    # 获取ETH价格
    eth_price = get_eth_price()
    if not eth_price:
        print("❌ 无法获取ETH价格")
        return
    
    print(f"💰 当前ETH价格: ${eth_price}")
    print(f"💵 预计获得: ${eth_balance * eth_price:.2f} USDT")
    
    # 显示交易信息
    print(f"\n📋 交易信息:")
    print(f"  交易对: ETH-USDT")
    print(f"  卖出数量: {eth_balance} ETH")
    print(f"  订单类型: 市价单")
    print(f"  交易模式: {TRADING_MODE}")
    
    if TRADING_MODE == "实盘交易":
        print("🚨 警告: 这是实盘交易，将使用真实资金！")
        print("⚠️  自动确认卖出操作...")
    else:
        print("✅ 模拟交易模式，无真实风险")
        print("🔄 自动确认卖出操作...")
    
    # 执行卖出
    print(f"\n🔄 正在卖出 {eth_balance} ETH...")
    result = sell_eth(eth_balance)
    
    if result and result.get('code') == '0':
        print("✅ ETH卖出成功！")
        print(f"订单ID: {result['data'][0]['ordId']}")
        print(f"卖出数量: {eth_balance} ETH")
        print(f"预计获得: ${eth_balance * eth_price:.2f} USDT")
        
        # 等待几秒后检查余额
        print("\n⏳ 等待3秒后检查账户余额...")
        time.sleep(3)
        
        # 检查新的余额
        new_eth_balance = get_eth_balance()
        print(f"📊 卖出后ETH余额: {new_eth_balance}")
        
        if new_eth_balance == 0:
            print("🎉 ETH已全部卖出！")
        else:
            print(f"⚠️  还有 {new_eth_balance} ETH 未卖出")
        
    else:
        print("❌ ETH卖出失败")
        if result:
            print(f"错误信息: {result}")

if __name__ == "__main__":
    main()
