"""
批量卖出所有币种脚本
将账户中的所有币种（除USDT外）全部卖出为USDT
"""
from okx_http_client import client
from config import TRADING_MODE
import time

def get_all_balances():
    """获取所有币种余额"""
    result = client.get_account_balance()
    if result and result.get('code') == '0':
        details = result['data'][0]['details']
        balances = {}
        for detail in details:
            avail_bal = float(detail['availBal'])
            if avail_bal > 0 and detail['ccy'] != 'USDT':
                balances[detail['ccy']] = avail_bal
        return balances
    return {}

def get_coin_price(ccy):
    """获取币种价格"""
    if ccy == 'BTC':
        inst_id = 'BTC-USDT'
    elif ccy == 'OKB':
        inst_id = 'OKB-USDT'
    elif ccy == 'ETH':
        inst_id = 'ETH-USDT'
    else:
        # 尝试常见的交易对
        inst_id = f'{ccy}-USDT'
    
    try:
        ticker = client.get_ticker(inst_id)
        if ticker and ticker.get('code') == '0':
            return float(ticker['data'][0]['last'])
    except:
        pass
    return None

def sell_coin(ccy, amount):
    """卖出指定币种"""
    if ccy == 'BTC':
        inst_id = 'BTC-USDT'
    elif ccy == 'OKB':
        inst_id = 'OKB-USDT'
    elif ccy == 'ETH':
        inst_id = 'ETH-USDT'
    else:
        inst_id = f'{ccy}-USDT'
    
    try:
        result = client.place_order(
            inst_id=inst_id,
            side="sell",
            ord_type="market",
            sz=str(amount)
        )
        return result
    except Exception as e:
        print(f"卖出{ccy}失败: {e}")
        return None

def main():
    """主函数"""
    print(f"=== 批量卖出所有币种工具 - {TRADING_MODE}模式 ===")
    print()
    
    # 获取所有币种余额
    balances = get_all_balances()
    if not balances:
        print("❌ 账户中没有可卖出的币种")
        return
    
    print("📊 当前账户币种:")
    total_value = 0
    sell_plan = []
    
    for ccy, amount in balances.items():
        price = get_coin_price(ccy)
        if price:
            value = amount * price
            total_value += value
            sell_plan.append((ccy, amount, price, value))
            print(f"  {ccy}: {amount} (价格: ${price:.2f}, 价值: ${value:.2f})")
        else:
            print(f"  {ccy}: {amount} (无法获取价格)")
    
    if not sell_plan:
        print("❌ 无法获取币种价格，无法计算卖出价值")
        return
    
    print(f"\n💰 预计总获得: ${total_value:.2f} USDT")
    
    # 显示交易计划
    print(f"\n📋 卖出计划:")
    for ccy, amount, price, value in sell_plan:
        print(f"  {ccy}: {amount} → ${value:.2f} USDT")
    
    # 确认卖出
    print(f"\n⚠️  准备卖出 {len(sell_plan)} 种币种")
    if TRADING_MODE == "实盘交易":
        print("🚨 警告: 这是实盘交易，将使用真实资金！")
        print("⚠️  自动确认卖出操作...")
    else:
        print("✅ 模拟交易模式，无真实风险")
        print("🔄 自动确认卖出操作...")
    
    # 执行卖出
    success_count = 0
    total_gained = 0
    
    for ccy, amount, price, expected_value in sell_plan:
        print(f"\n🔄 正在卖出 {amount} {ccy}...")
        result = sell_coin(ccy, amount)
        
        if result and result.get('code') == '0':
            print(f"✅ {ccy}卖出成功！")
            print(f"  订单ID: {result['data'][0]['ordId']}")
            print(f"  卖出数量: {amount} {ccy}")
            print(f"  预计获得: ${expected_value:.2f} USDT")
            success_count += 1
            total_gained += expected_value
        else:
            print(f"❌ {ccy}卖出失败")
            if result:
                print(f"  错误信息: {result}")
        
        # 等待1秒避免请求过快
        time.sleep(1)
    
    # 等待几秒后检查最终余额
    print(f"\n⏳ 等待5秒后检查最终账户余额...")
    time.sleep(5)
    
    # 检查最终余额
    final_balances = get_all_balances()
    usdt_result = client.get_account_balance()
    usdt_balance = 0
    if usdt_result and usdt_result.get('code') == '0':
        details = usdt_result['data'][0]['details']
        for detail in details:
            if detail['ccy'] == 'USDT':
                usdt_balance = float(detail['availBal'])
                break
    
    print(f"\n📊 卖出结果:")
    print(f"  成功卖出: {success_count}/{len(sell_plan)} 种币种")
    print(f"  当前USDT余额: {usdt_balance:.2f}")
    
    if final_balances:
        print(f"  剩余币种:")
        for ccy, amount in final_balances.items():
            print(f"    {ccy}: {amount}")
    else:
        print("  🎉 所有币种已全部卖出！")
    
    print(f"\n✅ 批量卖出操作完成！")

if __name__ == "__main__":
    main()
