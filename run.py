#!/usr/bin/env python3
"""
简化启动脚本
快速启动策略管理器
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from strategy_manager import StrategyManager

def main():
    """主函数"""
    print("🚀 OKX 策略管理器")
    print("="*50)
    
    # 创建策略管理器
    manager = StrategyManager()
    
    # 从文件夹注册策略
    manager.register_strategy_from_folder("enhanced_sar", "strategies/enhanced_sar")
    manager.register_strategy_from_folder("simple_sar", "strategies/simple_sar")
    
    # 显示菜单
    while True:
        print("\n📋 策略管理器")
        print("="*30)
        print("1. 列出策略")
        print("2. 运行增强版SAR策略")
        print("3. 运行简化SAR策略")
        print("4. 回测增强版SAR策略")
        print("5. 回测简化SAR策略")
        print("6. 查看报告")
        print("7. 退出")
        
        choice = input("\n请选择操作 (1-7): ").strip()
        
        if choice == "1":
            manager.list_strategies()
        
        elif choice == "2":
            print("\n🚀 启动增强版SAR策略...")
            manager.run_strategy("enhanced_sar", "live")
        
        elif choice == "3":
            print("\n🚀 启动简化SAR策略...")
            manager.run_strategy("simple_sar", "live")
        
        elif choice == "4":
            print("\n📊 回测增强版SAR策略...")
            days = input("回测天数 (默认10): ").strip()
            days = int(days) if days.isdigit() else 10
            manager.run_strategy("enhanced_sar", "backtest", days=days)
        
        elif choice == "5":
            print("\n📊 回测简化SAR策略...")
            days = input("回测天数 (默认10): ").strip()
            days = int(days) if days.isdigit() else 10
            manager.run_strategy("simple_sar", "backtest", days=days)
        
        elif choice == "6":
            manager.list_reports()
        
        elif choice == "7":
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()
