#!/usr/bin/env python3
"""
增强版SAR策略运行系统 - 合约交易版本
支持2倍杠杆、真正做空、止盈止损
"""
import os
import json
import time
import signal
import sys
from datetime import datetime
from okx_http_client import client
from trading_strategies.enhanced_sar_strategy_contract import EnhancedSARStrategyContract

class ContractStrategyRunner:
    """合约策略运行器"""
    
    def __init__(self):
        self.strategy = None
        self.running = False
        self.results_folder = "contract_strategy_results"
        self.session_id = None
        
    def create_results_folder(self):
        """创建结果文件夹"""
        if not os.path.exists(self.results_folder):
            os.makedirs(self.results_folder)
    
    def get_user_input(self):
        """使用默认参数，无需用户输入"""
        print("🚀 增强版SAR策略运行系统 (合约交易)")
        print("="*60)
        print("支持2倍杠杆、真正做空、止盈止损")
        print("使用默认参数，1000 USDT，2倍杠杆，15分钟K线")
        
        # 使用默认参数
        return {
            "initial_usdt": 1000,  # 默认投入1000 USDT
            "leverage": 2,  # 默认2倍杠杆
            "kline_period": "15m",  # 默认15分钟K线
            "af_start": 0.02,  # 默认初始加速因子
            "af_increment": 0.02,  # 默认加速因子增量
            "af_maximum": 0.2,  # 默认最大加速因子
            "take_profit_ratio": 0.02,  # 默认止盈比例2%
            "stop_loss_ratio": 0.01,  # 默认止损比例1%
            "atr_period": 14,  # 默认ATR周期
            "volume_threshold": 0.0  # 禁用成交量过滤器
        }
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            print(f"\n🛑 收到停止信号 ({signum})")
            self.stop_strategy()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def create_strategy(self, params):
        """创建策略实例"""
        self.strategy = EnhancedSARStrategyContract(
            client=client,
            kline_period=params["kline_period"],
            af_start=params["af_start"],
            af_increment=params["af_increment"],
            af_maximum=params["af_maximum"],
            take_profit_ratio=params["take_profit_ratio"],
            stop_loss_ratio=params["stop_loss_ratio"],
            atr_period=params["atr_period"],
            volume_threshold=params["volume_threshold"],
            initial_usdt=params["initial_usdt"],
            leverage=params["leverage"]
        )
        
        # 设置杠杆
        if not self.strategy.set_leverage(params["leverage"]):
            print("⚠️ 杠杆设置失败，使用默认杠杆")
        
        # 设置初始余额
        self.strategy.start_balance = params["initial_usdt"]
        self.strategy.current_balance = params["initial_usdt"]
    
    def run_strategy(self):
        """运行策略"""
        print("\n🚀 开始运行合约策略...")
        print("按 Ctrl+C 手动停止策略")
        print("="*60)
        
        self.running = True
        signal_count = 0
        
        while self.running:
            try:
                # 获取市场数据
                data = self.strategy.get_market_data(
                    self.strategy.inst_id, 
                    self.strategy.kline_period, 
                    '100'
                )
                
                if data is None:
                    print("❌ 无法获取市场数据，等待5秒后重试...")
                    time.sleep(5)
                    continue
                
                # 分析信号
                signal = self.strategy.analyze_signal(data)
                
                # 显示当前状态
                current_balance = self.strategy.get_current_balance()
                current_price = data['close'].iloc[-1]
                
                # 获取持仓信息
                positions_info = self.strategy.get_contract_positions()
                position_size = positions_info.get('position_size', 0) if positions_info else 0
                unrealized_pnl = positions_info.get('unrealized_pnl', 0) if positions_info else 0
                
                print(f"\n📊 合约策略状态 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   当前价格: ${current_price:.2f}")
                print(f"   账户余额: ${current_balance:.2f}")
                print(f"   当前持仓: {self.strategy.position or '无'}")
                print(f"   持仓数量: {position_size}")
                print(f"   未实现盈亏: ${unrealized_pnl:.2f}")
                print(f"   杠杆倍数: {self.strategy.leverage}x")
                print(f"   信号: {signal['signal']} - {signal['reason']}")
                
                # 执行交易
                if signal["signal"] != "hold":
                    self.strategy.execute_trade(signal)
                
                # 更新余额
                self.strategy.current_balance = current_balance
                
                # 等待下一个周期
                if self.strategy.kline_period == "15m":
                    wait_time = 900  # 15分钟
                elif self.strategy.kline_period == "1H":
                    wait_time = 3600  # 1小时
                elif self.strategy.kline_period == "4H":
                    wait_time = 14400  # 4小时
                elif self.strategy.kline_period == "1D":
                    wait_time = 86400  # 1天
                else:
                    wait_time = 300  # 默认5分钟
                
                print(f"⏰ 等待 {wait_time//60} 分钟后检查下一个信号...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                print("\n🛑 用户手动停止策略")
                break
            except Exception as e:
                print(f"❌ 策略运行错误: {e}")
                time.sleep(30)  # 错误后等待30秒
    
    def stop_strategy(self):
        """停止策略"""
        self.running = False
        if self.strategy:
            print("\n📊 生成策略运行报告...")
            self.generate_final_report()
    
    def generate_final_report(self):
        """生成最终报告"""
        if not self.strategy:
            return
        
        # 生成报告
        report = self.strategy.generate_report()
        
        # 创建会话ID
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建统一的报告文件夹
        report_dir = "reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        # 只生成Markdown报告
        md_report_file = os.path.join(report_dir, f"contract_strategy_report_{self.session_id}.md")
        self.generate_markdown_report(report, md_report_file)
        
        print(f"\n📁 合约策略运行结果已保存:")
        print(f"   Markdown报告: {md_report_file}")
        
        # 显示摘要
        self.print_summary(report)
    
    def generate_markdown_report(self, report, filename):
        """生成Markdown报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# 📊 合约交易策略结果报告\n\n")
            
            # 策略信息表格
            f.write("## 🎯 策略信息 (Strategy Information)\n\n")
            f.write("| 字段 (Field) | 值 (Value) | 说明 (Description) |\n")
            f.write("|-------------|-----------|------------------|\n")
            
            strategy_info = report["strategy_info"]
            field_translations = {
                "name": ("策略名称", "Strategy Name"),
                "kline_period": ("K线周期", "Kline Period"),
                "af_start": ("初始加速因子", "AF Start"),
                "af_increment": ("加速因子增量", "AF Increment"),
                "af_maximum": ("最大加速因子", "AF Maximum"),
                "take_profit_ratio": ("止盈比例", "Take Profit Ratio"),
                "stop_loss_ratio": ("止损比例", "Stop Loss Ratio"),
                "atr_period": ("ATR周期", "ATR Period"),
                "volume_threshold": ("成交量阈值", "Volume Threshold"),
                "leverage": ("杠杆倍数", "Leverage"),
                "inst_id": ("交易对", "Instrument ID")
            }
            
            for key, value in strategy_info.items():
                if key in field_translations:
                    cn_name, en_name = field_translations[key]
                    if key == "take_profit_ratio" or key == "stop_loss_ratio":
                        value = f"{value:.1%}"
                    elif key == "volume_threshold":
                        value = f"{value}x"
                    elif key == "leverage":
                        value = f"{value}x"
                    f.write(f"| **{cn_name}** ({en_name}) | {value} | {self._get_field_description(key)} |\n")
            
            # 性能指标表格
            f.write("\n## 📈 性能表现 (Performance Metrics)\n\n")
            f.write("| 字段 (Field) | 值 (Value) | 说明 (Description) |\n")
            f.write("|-------------|-----------|------------------|\n")
            
            perf = report["performance"]
            perf_translations = {
                "start_time": ("开始时间", "Start Time"),
                "end_time": ("结束时间", "End Time"),
                "runtime_hours": ("运行时长", "Runtime Hours"),
                "initial_balance": ("初始资金", "Initial Balance"),
                "final_balance": ("最终资金", "Final Balance"),
                "total_return": ("总收益率", "Total Return"),
                "total_trades": ("总交易次数", "Total Trades"),
                "winning_trades": ("盈利交易", "Winning Trades"),
                "losing_trades": ("亏损交易", "Losing Trades"),
                "win_rate": ("胜率", "Win Rate"),
                "current_position": ("当前持仓", "Current Position"),
                "position_size": ("持仓数量", "Position Size"),
                "entry_price": ("入场价格", "Entry Price"),
                "leverage_used": ("使用杠杆", "Leverage Used")
            }
            
            for key, value in perf.items():
                if key in perf_translations:
                    cn_name, en_name = perf_translations[key]
                    if key == "runtime_hours":
                        value = f"{value:.2f}小时 ({value*60:.1f}分钟)"
                    elif key in ["initial_balance", "final_balance", "entry_price"]:
                        value = f"${value:,.2f}"
                    elif key == "total_return":
                        value = f"{value:.2%}"
                    elif key == "win_rate":
                        value = f"{value:.2%}"
                    elif key == "current_position" and value is None:
                        value = "无 (None)"
                    elif key == "leverage_used":
                        value = f"{value}x"
                    f.write(f"| **{cn_name}** ({en_name}) | {value} | {self._get_perf_description(key)} |\n")
            
            # 交易历史
            f.write("\n## 📋 交易历史 (Trade History)\n\n")
            if report["trade_history"]:
                f.write("| 序号 | 时间 | 方向 | 价格 | 数量 | 收益率 | 杠杆 |\n")
                f.write("|------|------|------|------|------|--------|------|\n")
                for i, trade in enumerate(report["trade_history"], 1):
                    f.write(f"| {i} | {trade['timestamp']} | {trade['side']} | ${trade['price']:.2f} | "
                           f"{trade['amount']:.6f} | {trade['profit_rate']:.2%} | {trade['leverage']}x |\n")
            else:
                f.write("| 交易记录 | 说明 |\n")
                f.write("|---------|------|\n")
                f.write("| **空** (Empty) | 本次运行没有执行任何交易 |\n")
            
            # 结果分析
            f.write("\n## 📊 结果分析\n\n")
            perf = report["performance"]
            if perf['total_trades'] == 0:
                f.write("**策略状态**: ⚠️ **无交易执行**\n")
                f.write("- **运行时间**: {:.2f}小时\n".format(perf['runtime_hours']))
                f.write("- **交易执行**: 0次交易\n")
                f.write("- **可能原因**: \n")
                f.write("  - 策略参数过于严格，没有产生交易信号\n")
                f.write("  - 市场波动率不足，被过滤器过滤\n")
                f.write("  - 成交量阈值设置过高\n")
            else:
                f.write("**策略状态**: ✅ **正常运行**\n")
                f.write("- **运行时间**: {:.2f}小时\n".format(perf['runtime_hours']))
                f.write("- **交易执行**: {}次交易\n".format(perf['total_trades']))
                f.write("- **总收益率**: {:.2%}\n".format(perf['total_return']))
                f.write("- **胜率**: {:.2%}\n".format(perf['win_rate']))
    
    def _get_field_description(self, key):
        """获取字段描述"""
        descriptions = {
            "name": "策略名称",
            "kline_period": "K线数据周期",
            "af_start": "抛物线SAR初始加速因子",
            "af_increment": "每次加速因子增加量",
            "af_maximum": "抛物线SAR最大加速因子",
            "take_profit_ratio": "止盈触发比例",
            "stop_loss_ratio": "止损触发比例",
            "atr_period": "平均真实波幅计算周期",
            "volume_threshold": "成交量放大倍数阈值",
            "leverage": "使用的杠杆倍数",
            "inst_id": "交易合约对"
        }
        return descriptions.get(key, "")
    
    def _get_perf_description(self, key):
        """获取性能指标描述"""
        descriptions = {
            "start_time": "策略开始运行时间",
            "end_time": "策略结束运行时间",
            "runtime_hours": "策略总运行时间",
            "initial_balance": "策略开始时的资金",
            "final_balance": "策略结束时的资金",
            "total_return": "总收益百分比",
            "total_trades": "执行的交易总次数",
            "winning_trades": "盈利的交易次数",
            "losing_trades": "亏损的交易次数",
            "win_rate": "盈利交易占总交易的比例",
            "current_position": "当前持仓方向",
            "position_size": "当前持仓数量",
            "entry_price": "当前持仓的入场价格",
            "leverage_used": "实际使用的杠杆倍数"
        }
        return descriptions.get(key, "")
    
    def generate_text_report(self, report, filename):
        """生成文本报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("增强版SAR策略运行报告 (合约交易)\n")
            f.write("="*60 + "\n\n")
            
            # 策略信息
            f.write("策略参数:\n")
            f.write("-"*30 + "\n")
            for key, value in report["strategy_info"].items():
                f.write(f"{key}: {value}\n")
            f.write("\n")
            
            # 性能指标
            f.write("性能指标:\n")
            f.write("-"*30 + "\n")
            perf = report["performance"]
            f.write(f"开始时间: {perf['start_time']}\n")
            f.write(f"结束时间: {perf['end_time']}\n")
            f.write(f"运行时间: {perf['runtime_hours']:.2f} 小时\n")
            f.write(f"初始资金: ${perf['initial_balance']:,.2f}\n")
            f.write(f"最终余额: ${perf['final_balance']:,.2f}\n")
            f.write(f"总收益率: {perf['total_return']:.2%}\n")
            f.write(f"总交易次数: {perf['total_trades']}\n")
            f.write(f"盈利交易: {perf['winning_trades']}\n")
            f.write(f"亏损交易: {perf['losing_trades']}\n")
            f.write(f"胜率: {perf['win_rate']:.2%}\n")
            f.write(f"当前持仓: {perf['current_position'] or '无'}\n")
            f.write(f"持仓数量: {perf['position_size']}\n")
            f.write(f"入场价格: ${perf['entry_price']:.2f}\n")
            f.write(f"使用杠杆: {perf['leverage_used']}x\n\n")
            
            # 交易历史
            f.write("交易历史:\n")
            f.write("-"*30 + "\n")
            for i, trade in enumerate(report["trade_history"], 1):
                f.write(f"{i}. {trade['timestamp']} {trade['side']} @ ${trade['price']:.2f} "
                       f"数量: {trade['amount']:.6f} 收益率: {trade['profit_rate']:.2%} "
                       f"杠杆: {trade['leverage']}x\n")
    
    def print_summary(self, report):
        """打印摘要"""
        perf = report["performance"]
        
        print("\n" + "="*60)
        print("📊 合约策略运行摘要")
        print("="*60)
        print(f"运行时间: {perf['runtime_hours']:.2f} 小时")
        print(f"初始资金: ${perf['initial_balance']:,.2f}")
        print(f"最终余额: ${perf['final_balance']:,.2f}")
        print(f"总收益率: {perf['total_return']:.2%}")
        print(f"总交易次数: {perf['total_trades']}")
        print(f"盈利交易: {perf['winning_trades']}")
        print(f"亏损交易: {perf['losing_trades']}")
        print(f"胜率: {perf['win_rate']:.2%}")
        print(f"当前持仓: {perf['current_position'] or '无'}")
        print(f"持仓数量: {perf['position_size']}")
        print(f"使用杠杆: {perf['leverage_used']}x")
        if perf['entry_price'] > 0:
            print(f"入场价格: ${perf['entry_price']:.2f}")
        print("="*60)
        
        if perf['total_trades'] > 0:
            print(f"\n📈 交易详情:")
            for i, trade in enumerate(report["trade_history"][-5:], 1):
                print(f"   {i}. {trade['timestamp']} {trade['side']} @ ${trade['price']:.2f} "
                      f"收益率: {trade['profit_rate']:.2%} 杠杆: {trade['leverage']}x")

def main():
    """主函数"""
    runner = ContractStrategyRunner()
    
    try:
        # 设置信号处理器
        runner.setup_signal_handlers()
        
        # 获取用户输入
        params = runner.get_user_input()
        
        # 创建策略
        runner.create_strategy(params)
        
        # 运行策略
        runner.run_strategy()
        
    except KeyboardInterrupt:
        print("\n🛑 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")
    finally:
        # 生成最终报告
        if runner.strategy:
            runner.generate_final_report()

if __name__ == "__main__":
    main()
