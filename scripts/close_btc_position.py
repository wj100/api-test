#!/usr/bin/env python3
"""
临时脚本 - 平BTC仓位
"""
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from okx_http_client import client
from trading_strategies.enhanced_sar_strategy_contract import EnhancedSARStrategyContract

def close_btc_position():
    """平BTC仓位"""
    print("🚀 平BTC仓位")
    print("="*50)
    
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
        initial_usdt=10000,
        leverage=5
    )
    
    print("\n📈 获取市场数据...")
    data = strategy.get_market_data("BTC-USDT-SWAP", "15m", "100")
    if data is None:
        print("❌ 无法获取市场数据")
        return
    
    current_price = data['close'].iloc[-1]
    print(f"当前BTC价格: ${current_price:.2f}")
    
    print("\n🚀 自动全平所有仓位...")
    
    # 尝试获取持仓信息，如果失败则使用默认值
    try:
        positions_info = strategy.get_contract_positions()
        if positions_info and positions_info.get('position_size', 0) != 0:
            position_size = positions_info.get('position_size', 0)
            print(f"检测到持仓: {position_size} 张合约")
            
            if position_size > 0:
                # 多仓，需要卖出平仓
                close_side = "sell"
                close_pos_side = "long"
                sz = str(abs(position_size))
                print(f"🚀 平多仓 {sz} 张合约...")
            elif position_size < 0:
                # 空仓，需要买入平仓
                close_side = "buy"
                close_pos_side = "short"
                sz = str(abs(position_size))
                print(f"🚀 平空仓 {sz} 张合约...")
            else:
                print("❌ 没有持仓")
                return
        else:
            print("⚠️ 无法获取持仓信息，使用默认平仓")
            # 默认平仓设置
            close_side = "sell"
            close_pos_side = "long"
            sz = "0.1"  # 默认平仓数量
            print(f"🚀 默认平多仓 {sz} 张合约...")
    except Exception as e:
        print(f"⚠️ 获取持仓信息失败: {e}")
        print("使用默认平仓设置")
        close_side = "sell"
        close_pos_side = "long"
        sz = "0.1"  # 默认平仓数量
        print(f"🚀 默认平多仓 {sz} 张合约...")
    
    print(f"平仓数量: {sz} 张合约")
    
    # 执行平仓
    print(f"\n🚀 执行平仓...")
    # 计算限价单价格
    if close_side == "buy":
        # 买入平仓，价格稍微高一点确保成交
        limit_price = str(round(current_price * 1.001, 2))
    else:
        # 卖出平仓，价格稍微低一点确保成交
        limit_price = str(round(current_price * 0.999, 2))
    
    print(f"限价单价格: ${limit_price}")
    
    result = strategy.client.place_futures_order(
        inst_id="BTC-USDT-SWAP",
        side=close_side,
        ord_type="limit",
        sz=sz,
        px=limit_price,
        td_mode="cross",  # 全仓模式
        pos_side=close_pos_side  # 平仓方向
    )
    
    if result and result.get('code') == '0':
        print("✅ 平仓成功!")
        print(f"订单ID: {result.get('data', [{}])[0].get('ordId', 'N/A')}")
        print(f"平仓价格: ${current_price:.2f}")
        print(f"平仓数量: {sz} 张合约")
        
        print(f"\n📊 交易结果:")
        print(f"平仓价格: ${current_price:.2f}")
        print(f"平仓数量: {sz} 张合约")
        print(f"平仓方向: {close_pos_side}")
        
    else:
        print(f"❌ 平仓失败: {result}")

def main():
    """主函数"""
    try:
        close_btc_position()
    except KeyboardInterrupt:
        print("\n🛑 操作被用户中断")
    except Exception as e:
        print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    main()
