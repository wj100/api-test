#!/usr/bin/env python3
"""
统一策略管理器
管理所有交易策略的运行、回测和监控
"""
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from okx_http_client import OKXHTTPClient
from trading_strategies.enhanced_sar_strategy_contract import EnhancedSARStrategyContract
from trading_strategies.simple_sar_strategy import SimpleSARStrategy
from config import DEFAULT_INST_ID, DEFAULT_LEVERAGE

class StrategyManager:
    """统一策略管理器"""
    
    def __init__(self):
        self.client = OKXHTTPClient()
        self.strategies = {}
        self.active_strategies = {}
        self.reports_dir = "reports"
        
        # 确保报告目录存在
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        
        print("🚀 策略管理器初始化完成")
        print("="*60)
    
    def register_strategy(self, name: str, strategy_class, **kwargs):
        """注册策略"""
        self.strategies[name] = {
            'class': strategy_class,
            'params': kwargs
        }
        print(f"✅ 策略 '{name}' 已注册")
    
    def register_strategy_from_folder(self, name: str, folder_path: str):
        """从文件夹注册策略"""
        try:
            strategy_path = os.path.join(folder_path, "strategy.py")
            if os.path.exists(strategy_path):
                # 动态导入策略类
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"{name}_strategy", strategy_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 获取策略类 - 根据实际类名
                if name == "enhanced_sar":
                    strategy_class = getattr(module, "EnhancedSARStrategy")
                elif name == "simple_sar":
                    strategy_class = getattr(module, "SimpleSARStrategy")
                else:
                    # 通用规则
                    strategy_class = getattr(module, f"{name.title().replace('_', '')}Strategy")
                
                self.strategies[name] = {
                    'class': strategy_class,
                    'params': {},
                    'folder_path': folder_path
                }
                print(f"✅ 策略 '{name}' 已从文件夹注册: {folder_path}")
                return True
            else:
                print(f"❌ 策略文件不存在: {strategy_path}")
                return False
        except Exception as e:
            print(f"❌ 注册策略失败: {e}")
            return False
    
    def list_strategies(self):
        """列出所有可用策略"""
        print("\n📋 可用策略列表:")
        print("-" * 40)
        for name, info in self.strategies.items():
            print(f"  • {name}")
        print(f"\n总计: {len(self.strategies)} 个策略")
    
    def run_strategy(self, name: str, mode: str = "live", **kwargs):
        """运行策略"""
        if name not in self.strategies:
            print(f"❌ 策略 '{name}' 不存在")
            return False
        
        try:
            strategy_info = self.strategies[name]
            strategy_class = strategy_info['class']
            default_params = strategy_info['params']
            
            # 合并参数
            params = {**default_params, **kwargs}
            
            print(f"\n🚀 启动策略: {name}")
            print(f"   模式: {mode}")
            print(f"   参数: {params}")
            
            # 创建策略实例
            strategy = strategy_class(self.client, **params)
            
            if mode == "live":
                return self._run_live_strategy(strategy, name)
            elif mode == "backtest":
                return self._run_backtest_strategy(strategy, name, **kwargs)
            else:
                print(f"❌ 不支持的模式: {mode}")
                return False
                
        except Exception as e:
            print(f"❌ 运行策略失败: {e}")
            return False
    
    def _run_live_strategy(self, strategy, name: str):
        """运行实盘策略"""
        try:
            print(f"\n📊 开始运行实盘策略: {name}")
            print("按 Ctrl+C 停止策略")
            
            # 运行策略
            strategy.run()
            
            # 生成报告
            self._generate_report(strategy, name, "live")
            return True
            
        except KeyboardInterrupt:
            print(f"\n⏹️ 策略 {name} 已停止")
            self._generate_report(strategy, name, "live")
            return True
        except Exception as e:
            print(f"❌ 策略运行失败: {e}")
            return False
    
    def _run_backtest_strategy(self, strategy, name: str, **kwargs):
        """运行回测策略"""
        try:
            print(f"\n📊 开始回测策略: {name}")
            
            # 获取回测参数
            days = kwargs.get('days', 10)
            initial_usdt = kwargs.get('initial_usdt', 10000)
            
            # 运行回测
            results = strategy.run_backtest(days=days, initial_usdt=initial_usdt)
            
            if results:
                # 生成回测报告
                self._generate_backtest_report(results, name)
                return True
            else:
                print("❌ 回测失败")
                return False
                
        except Exception as e:
            print(f"❌ 回测失败: {e}")
            return False
    
    def _generate_report(self, strategy, name: str, mode: str):
        """生成策略报告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.reports_dir, f"{name}_{mode}_report_{timestamp}.md")
            
            # 生成报告内容
            report_content = self._create_report_content(strategy, name, mode)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"\n📁 策略报告已保存: {report_file}")
            return report_file
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")
            return None
    
    def _generate_backtest_report(self, results: Dict[str, Any], name: str):
        """生成回测报告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.reports_dir, f"{name}_backtest_report_{timestamp}.md")
            
            # 生成回测报告内容
            report_content = self._create_backtest_report_content(results, name)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"\n📁 回测报告已保存: {report_file}")
            return report_file
            
        except Exception as e:
            print(f"❌ 生成回测报告失败: {e}")
            return None
    
    def _create_report_content(self, strategy, name: str, mode: str) -> str:
        """创建策略报告内容"""
        content = f"# 📊 {name} 策略报告\n\n"
        content += f"**运行模式**: {mode}\n"
        content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 策略信息
        content += "## 🎯 策略信息\n\n"
        content += f"- **策略名称**: {name}\n"
        content += f"- **交易对**: {getattr(strategy, 'inst_id', 'N/A')}\n"
        content += f"- **杠杆倍数**: {getattr(strategy, 'leverage', 'N/A')}x\n"
        
        # 性能指标
        if hasattr(strategy, 'trades') and strategy.trades:
            content += "\n## 📈 交易统计\n\n"
            content += f"- **总交易次数**: {len(strategy.trades)}\n"
            
            # 计算胜率
            winning_trades = sum(1 for trade in strategy.trades if trade.get('pnl', 0) > 0)
            total_trades = len([trade for trade in strategy.trades if 'pnl' in trade])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            content += f"- **胜率**: {win_rate:.2%}\n"
        
        return content
    
    def _create_backtest_report_content(self, results: Dict[str, Any], name: str) -> str:
        """创建回测报告内容"""
        content = f"# 📊 {name} 回测报告\n\n"
        content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 回测概览
        content += "## 🎯 回测概览\n\n"
        content += f"- **初始资金**: ${results.get('initial_usdt', 0):,.2f}\n"
        content += f"- **最终权益**: ${results.get('final_equity', 0):,.2f}\n"
        content += f"- **总收益率**: {results.get('total_return', 0):.2%}\n"
        content += f"- **最大回撤**: {results.get('max_drawdown', 0):.2%}\n"
        content += f"- **夏普比率**: {results.get('sharpe_ratio', 0):.2f}\n"
        
        # 交易统计
        content += "\n## 📈 交易统计\n\n"
        content += f"- **总交易次数**: {results.get('total_trades', 0)}\n"
        content += f"- **盈利交易**: {results.get('winning_trades', 0)}\n"
        content += f"- **亏损交易**: {results.get('losing_trades', 0)}\n"
        content += f"- **胜率**: {results.get('win_rate', 0):.2%}\n"
        
        return content
    
    def stop_strategy(self, name: str):
        """停止策略"""
        if name in self.active_strategies:
            # 这里可以添加停止策略的逻辑
            del self.active_strategies[name]
            print(f"⏹️ 策略 '{name}' 已停止")
        else:
            print(f"⚠️ 策略 '{name}' 未在运行")
    
    def get_strategy_status(self, name: str):
        """获取策略状态"""
        if name in self.active_strategies:
            return "运行中"
        else:
            return "未运行"
    
    def list_reports(self):
        """列出所有报告"""
        if not os.path.exists(self.reports_dir):
            print("📁 暂无报告文件")
            return
        
        reports = [f for f in os.listdir(self.reports_dir) if f.endswith('.md')]
        if not reports:
            print("📁 暂无报告文件")
            return
        
        print(f"\n📁 报告文件 ({len(reports)} 个):")
        print("-" * 40)
        for report in sorted(reports):
            print(f"  • {report}")

def main():
    """主函数 - 交互式策略管理器"""
    manager = StrategyManager()
    
    # 从文件夹注册策略
    manager.register_strategy_from_folder("enhanced_sar", "strategies/enhanced_sar")
    manager.register_strategy_from_folder("simple_sar", "strategies/simple_sar")
    
    print("\n🎯 策略管理器")
    print("="*60)
    
    while True:
        print("\n📋 可用操作:")
        print("  1. 列出策略")
        print("  2. 运行策略")
        print("  3. 停止策略")
        print("  4. 查看报告")
        print("  5. 退出")
        
        choice = input("\n请选择操作 (1-5): ").strip()
        
        if choice == "1":
            manager.list_strategies()
        
        elif choice == "2":
            manager.list_strategies()
            strategy_name = input("\n请输入策略名称: ").strip()
            
            print("\n运行模式:")
            print("  1. 实盘运行")
            print("  2. 回测")
            
            mode_choice = input("请选择模式 (1-2): ").strip()
            mode = "live" if mode_choice == "1" else "backtest"
            
            if mode == "backtest":
                days = input("回测天数 (默认10): ").strip()
                days = int(days) if days.isdigit() else 10
                manager.run_strategy(strategy_name, mode, days=days)
            else:
                manager.run_strategy(strategy_name, mode)
        
        elif choice == "3":
            strategy_name = input("请输入要停止的策略名称: ").strip()
            manager.stop_strategy(strategy_name)
        
        elif choice == "4":
            manager.list_reports()
        
        elif choice == "5":
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()
