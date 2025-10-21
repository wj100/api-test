#!/usr/bin/env python3
"""
临时脚本 - 开BTC 10倍空单
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from okx_http_client import client
from trading_strategies.enhanced_sar_strategy_contract import EnhancedSARStrategyContract
import math

def open_btc_short():
    """开BTC 10倍空单"""
    print("🚀 开BTC 10倍空单")
    print("="*50)
    
    # 使用硬编码金额
    usdt_amount = 1000
    print(f"使用硬编码金额: {usdt_amount} USDT")
    
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
        volume_threshold=0.5,
        initial_usdt=usdt_amount,
        leverage=10
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
    
    print("\n🚀 直接开BTC 10倍空单 (严格使用1000U本金，10x杠杆)...")
    
    # 使用固定本金1000U，不读取账户余额
    amount = usdt_amount * 10  # 1000U 本金 * 10倍杠杆 = 10000U 名义
    
    # 获取合约规格用于换算张数
    inst_id = "BTC-USDT-SWAP"
    insts = client.get_instruments("SWAP")
    ct_val = 0.01  # 默认每张面值 0.01 BTC（兜底）
    lot_sz = 1.0   # 默认下单步长 1 张
    if insts and insts.get('code') == '0':
        for it in insts['data']:
            if it.get('instId') == inst_id:
                try:
                    ct_val = float(it.get('ctVal', ct_val))
                    lot_sz = float(it.get('lotSz', lot_sz))
                except Exception:
                    pass
                break
    print(f"合约面值 ctVal: {ct_val} { 'BTC' }")
    print(f"下单步长 lotSz: {lot_sz} 张")

    # 目标BTC数量 = 名义/价格
    target_btc = amount / current_price
    # 目标张数 = 目标BTC数量 / ctVal
    raw_sz = target_btc / ct_val
    # 按步长取整（向上取整，保证名义不少于目标）
    sz_num = math.ceil(raw_sz / lot_sz) * lot_sz
    # 张数必须为整数或步长倍数
    if abs(sz_num - round(sz_num)) < 1e-9:
        sz_str = str(int(round(sz_num)))
    else:
        sz_str = f"{sz_num:.8f}".rstrip('0').rstrip('.')

    est_notional = sz_num * ct_val * current_price
    est_margin = est_notional / 10

    print(f"计划开仓张数: {sz_str} 张 (目标名义≈${amount:.2f}，预估名义≈${est_notional:.2f}，预估保证金≈${est_margin:.2f})")
    print(f"杠杆倍数: 10x")
    
    # 执行开空单
    print("\n🚀 执行开空单...")
    # 计算限价单价格（稍微低一点确保成交）
    limit_price = str(round(current_price * 0.999, 2))
    print(f"限价单价格: ${limit_price}")
    
    result = strategy.client.place_futures_order(
        inst_id=inst_id,
        side="sell",
        ord_type="limit",
        sz=sz_str,
        px=limit_price,
        td_mode="cross",
        pos_side="short"
    )
    
    if result and result.get('code') == '0':
        print("✅ 开空单成功!")
        print(f"订单ID: {result.get('data', [{}])[0].get('ordId', 'N/A')}")
        print(f"开仓价格: ${current_price:.2f}")
        print(f"合约数量: {sz_str} 张")
        print(f"杠杆倍数: 10x")
        
        # 记录交易
        strategy.record_trade("sell_open", current_price, float(sz_str), 0)
        strategy.position = "short"
        strategy.entry_price = current_price
        strategy.position_size = -float(sz_str)
        
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
