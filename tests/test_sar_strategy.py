"""
测试SAR策略
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from okx_http_client import client
from strategies import SARStrategy
from config import DEFAULT_INST_ID, TRADING_MODE

def test_sar_strategy():
    """测试SAR策略"""
    print(f"=== SAR策略测试 - {TRADING_MODE}模式 ===")
    
    # 创建SAR策略
    sar_strategy = SARStrategy(client)
    
    # 获取市场数据
    print("获取市场数据...")
    data = sar_strategy.get_market_data(DEFAULT_INST_ID, "1H", 50)
    if data is None:
        print("❌ 无法获取市场数据")
        return
    
    print(f"✅ 获取到 {len(data)} 根K线数据")
    
    # 分析信号
    print("\n分析SAR信号...")
    signal = sar_strategy.analyze(data)
    print(f"信号结果: {signal}")
    
    # 显示持仓信息
    pos_info = sar_strategy.get_position_info()
    print(f"\n持仓信息:")
    print(f"  当前持仓: {pos_info['position']}")
    print(f"  入场价格: ${pos_info['entry_price']}")
    print(f"  止盈比例: {pos_info['take_profit']:.1%}")
    print(f"  止损比例: {pos_info['stop_loss']:.1%}")
    
    # 显示策略参数
    print(f"\n策略参数:")
    print(f"  初始加速因子: {sar_strategy.af_start}")
    print(f"  加速因子增量: {sar_strategy.af_increment}")
    print(f"  最大加速因子: {sar_strategy.af_maximum}")
    
    print("\n✅ SAR策略测试完成")

if __name__ == "__main__":
    test_sar_strategy()
