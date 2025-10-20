#!/usr/bin/env python3
"""
合约策略启动脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_enhanced_sar_contract import ContractStrategyRunner

def main():
    """主函数"""
    print("🚀 增强版SAR策略启动器 (合约交易)")
    print("支持2倍杠杆、真正做空、止盈止损")
    print("="*50)
    
    try:
        runner = ContractStrategyRunner()
        runner.setup_signal_handlers()
        
        # 获取用户输入
        params = runner.get_user_input()
        
        # 创建策略
        runner.create_strategy(params)
        
        # 运行策略
        runner.run_strategy()
        
    except KeyboardInterrupt:
        print("\n🛑 策略已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
    finally:
        if runner.strategy:
            runner.generate_final_report()

if __name__ == "__main__":
    main()
