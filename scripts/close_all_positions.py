#!/usr/bin/env python3
"""
全平所有仓位脚本
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from okx_http_client import client

def close_all_positions():
    """全平所有仓位"""
    print("🚀 全平所有仓位")
    print("="*50)
    
    print("\n📈 获取市场数据...")
    try:
        # 获取当前价格
        result = client.get_candles("BTC-USDT-SWAP", "15m", "1")
        if result and result.get('code') == '0':
            data = result['data'][0]
            # 数据格式: [timestamp, open, high, low, close, vol, volCcy, volCcy2, confirm]
            current_price = float(data[4])  # close价格在第5个位置
            print(f"当前BTC价格: ${current_price:.2f}")
        else:
            print("❌ 无法获取市场数据")
            return
    except Exception as e:
        print(f"❌ 获取市场数据失败: {e}")
        return
    
    print("\n🚀 尝试平多仓...")
    # 尝试平多仓
    try:
        limit_price = str(round(current_price * 0.999, 2))
        print(f"限价单价格: ${limit_price}")
        
        result = client.place_futures_order(
            inst_id="BTC-USDT-SWAP",
            side="sell",
            ord_type="limit",
            sz="0.1",  # 尝试平0.1张合约
            px=limit_price,
            td_mode="cross",
            pos_side="long"
        )
        
        if result and result.get('code') == '0':
            print("✅ 平多仓成功!")
            print(f"订单ID: {result.get('data', [{}])[0].get('ordId', 'N/A')}")
        else:
            print(f"⚠️ 平多仓失败: {result.get('msg', 'Unknown error')}")
    except Exception as e:
        print(f"⚠️ 平多仓异常: {e}")
    
    print("\n🚀 尝试平空仓...")
    # 尝试平空仓
    try:
        limit_price = str(round(current_price * 1.001, 2))
        print(f"限价单价格: ${limit_price}")
        
        result = client.place_futures_order(
            inst_id="BTC-USDT-SWAP",
            side="buy",
            ord_type="limit",
            sz="0.1",  # 尝试平0.1张合约
            px=limit_price,
            td_mode="cross",
            pos_side="short"
        )
        
        if result and result.get('code') == '0':
            print("✅ 平空仓成功!")
            print(f"订单ID: {result.get('data', [{}])[0].get('ordId', 'N/A')}")
        else:
            print(f"⚠️ 平空仓失败: {result.get('msg', 'Unknown error')}")
    except Exception as e:
        print(f"⚠️ 平空仓异常: {e}")
    
    print("\n✅ 全平操作完成!")

def main():
    """主函数"""
    try:
        close_all_positions()
    except KeyboardInterrupt:
        print("\n🛑 操作被用户中断")
    except Exception as e:
        print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    main()
