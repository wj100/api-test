#!/usr/bin/env python3
"""
临时脚本 - 开BTC 10倍空单
"""
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from okx_http_client import client
from trading_strategies.enhanced_sar_strategy_contract import EnhancedSARStrategyContract

def open_btc_short():
    """开BTC 10倍空单"""
    print("🚀 开BTC 10倍空单")
    print("="*50)
    
    # 获取用户输入
    try:
        usdt_amount = float(input("请输入投入的USDT金额: "))
        if usdt_amount <= 0:
            print("❌ 金额必须大于0")
            return
    except ValueError:
        print("❌ 请输入有效的数字")
        return
    
    print(f"\n📊 创建10倍杠杆合约策略...")
    
    # 创建策略实例
    strategy = EnhancedSARStrategyContract(
        client=client,
        kline_period="15m",
        af_start=0.02,
        af_increment=0.02,
        af_maximum=0.2,
        take_profit_ratio=0.02,
        stop_loss_ratio=0.01,
        atr_period=14,
        volume_threshold=0.5,  # 降低阈值增加交易机会
        initial_usdt=usdt_amount,
        leverage=10  # 10倍杠杆
    )
    
    # 设置杠杆
    print("🔧 设置10倍杠杆...")
    if not strategy.set_leverage(10):
        print("⚠️ 杠杆设置失败，继续尝试...")
    
    print("\n📈 获取市场数据...")
    data = strategy.get_market_data("BTC-USDT-SWAP", "15m", "100")
    if data is None:
        print("❌ 无法获取市场数据")
        return
    
    current_price = data['close'].iloc[-1]
    print(f"当前BTC价格: ${current_price:.2f}")
    
    print("\n🚀 直接开BTC 10倍空单 (跳过信号检查)...")
    
    # 获取账户余额
    balance_info = strategy.get_contract_balance()
    usdt_balance = balance_info.get('USDT', {}).get('available', 0)
    print(f"可用USDT余额: ${usdt_balance:.2f}")
    
    # 模拟账户余额为0是正常的，使用用户输入的金额
    if usdt_balance <= 0:
        print("⚠️ 模拟账户余额为0，使用用户输入金额")
        usdt_balance = usdt_amount
    
    # 计算合约数量
    amount = usdt_balance * 0.8 * 10  # 使用80%资金，10倍杠杆
    # BTC-USDT-SWAP最小数量0.01，步长0.1
    contract_size = round(amount / current_price, 1)  # 保留1位小数
    if contract_size < 0.01:
        contract_size = 0.01  # 最小数量
    sz = str(contract_size)
    print(f"计划开仓数量: {sz} 张合约")
    print(f"使用资金: ${amount:.2f}")
    print(f"杠杆倍数: 10x")
    
    # 执行开空单
    print("\n🚀 执行开空单...")
    # 计算限价单价格（稍微低一点确保成交）
    limit_price = str(round(current_price * 0.999, 2))
    print(f"限价单价格: ${limit_price}")
    
    result = strategy.client.place_futures_order(
        inst_id="BTC-USDT-SWAP",
        side="sell",
        ord_type="limit",
        sz=sz,
        px=limit_price,
        td_mode="cross",  # 全仓模式
        pos_side="short"  # 做空
    )
    
    if result and result.get('code') == '0':
        print("✅ 开空单成功!")
        print(f"订单ID: {result.get('data', [{}])[0].get('ordId', 'N/A')}")
        print(f"开仓价格: ${current_price:.2f}")
        print(f"合约数量: {sz} 张")
        print(f"杠杆倍数: 10x")
        
        # 记录交易
        strategy.record_trade("sell_open", current_price, float(sz), 0)
        strategy.position = "short"
        strategy.entry_price = current_price
        strategy.position_size = -float(sz)
        
        print(f"\n📊 持仓信息:")
        print(f"持仓方向: 空")
        print(f"入场价格: ${strategy.entry_price:.2f}")
        print(f"持仓数量: {strategy.position_size}")
        print(f"杠杆倍数: 10x")
        
    else:
        print(f"❌ 开空单失败: {result}")

def main():
    """主函数"""
    try:
        open_btc_short()
    except KeyboardInterrupt:
        print("\n🛑 操作被用户中断")
    except Exception as e:
        print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    main()
