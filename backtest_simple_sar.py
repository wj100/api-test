#!/usr/bin/env python3
"""
简化SAR策略回测系统
- 基于15分钟线SAR信号
- 1小时线趋势确认
- 2倍杠杆合约交易
- 无止盈止损
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
from typing import Dict, List, Tuple, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from okx_http_client import client
from trading_strategies.simple_sar_strategy import SimpleSARStrategy


class SimpleSARBacktest:
    """简化SAR策略回测系统"""
    
    def __init__(self, initial_usdt: float = 10000, leverage: float = 2):
        self.initial_usdt = initial_usdt
        self.leverage = leverage
        self.current_usdt = initial_usdt
        self.current_btc = 0
        self.trades = []
        self.equity_curve = []
        self.max_drawdown = 0
        self.peak_equity = initial_usdt
        
        # 策略参数
        self.strategy = SimpleSARStrategy(
            client=client,
            inst_id="BTC-USDT-SWAP",
            leverage=leverage
        )
    
    def get_historical_data(self, days: int = 10) -> pd.DataFrame:
        """获取历史数据"""
        print(f"📊 获取过去{days}天的历史数据...")
        
        try:
            result = client.get_candles(
                "BTC-USDT-SWAP", 
                "15m", 
                "3000"  # 获取最大数据点
            )
            
            if result and result.get('code') == '0':
                data = result['data']
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 
                    'vol', 'volCcy', 'volCcy2', 'confirm'
                ])
                
                # 转换数据类型
                for col in ['open', 'high', 'low', 'close', 'vol', 'volCcy']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 转换时间戳并排序
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                print(f"✅ 获取到 {len(df)} 条历史数据")
                print(f"📅 数据时间范围: {df['timestamp'].iloc[0]} 到 {df['timestamp'].iloc[-1]}")
                return df
            else:
                print(f"❌ 获取历史数据失败: {result}")
                return None
                
        except Exception as e:
            print(f"❌ 获取历史数据异常: {e}")
            return None
    
    def calculate_contract_size(self, usdt_amount: float, price: float) -> float:
        """计算合约数量"""
        contract_size = usdt_amount / price
        # 按步长0.1调整，确保不小于0.01
        contract_size = max(0.01, round(contract_size * 10) / 10)
        return contract_size
    
    def execute_trade(self, signal: str, price: float, timestamp: str) -> bool:
        """执行交易"""
        try:
            if signal == 'buy' and self.current_btc == 0:
                # 开多仓 - 使用固定1000 USDT
                amount = 1000 * self.leverage  # 1000 USDT * 2倍杠杆 = 2000 USDT
                contract_size = self.calculate_contract_size(amount, price)
                
                if contract_size >= 0.01:
                    self.current_btc = contract_size
                    self.current_usdt -= amount
                    
                    trade = {
                        'timestamp': timestamp,
                        'side': 'buy',
                        'price': price,
                        'amount': contract_size,
                        'usdt_used': amount,
                        'leverage': self.leverage
                    }
                    self.trades.append(trade)
                    print(f"📈 开多仓: {contract_size:.2f}张 @ ${price:.2f} (使用{amount} USDT)")
                    return True
                    
            elif signal == 'sell' and self.current_btc > 0:
                # 平多仓
                # 找到开仓价格（最近的开仓交易）
                entry_price = None
                for trade in reversed(self.trades):
                    if trade['side'] == 'buy':
                        entry_price = trade['price']
                        break
                
                if entry_price:
                    pnl = (price - entry_price) * self.current_btc
                else:
                    pnl = 0
                
                # 找到开仓时使用的USDT
                entry_usdt = 0
                for trade in reversed(self.trades):
                    if trade['side'] == 'buy':
                        entry_usdt = trade.get('usdt_used', 0)
                        break
                
                self.current_usdt += entry_usdt + pnl
                
                trade = {
                    'timestamp': timestamp,
                    'side': 'sell',
                    'price': price,
                    'amount': self.current_btc,
                    'pnl': pnl,
                    'leverage': self.leverage
                }
                self.trades.append(trade)
                print(f"📉 平多仓: {self.current_btc:.2f}张 @ ${price:.2f}, PnL: ${pnl:.2f}")
                self.current_btc = 0
                return True
                
            elif signal == 'short' and self.current_btc == 0:
                # 开空仓 - 使用固定1000 USDT
                amount = 1000 * self.leverage  # 1000 USDT * 2倍杠杆 = 2000 USDT
                contract_size = self.calculate_contract_size(amount, price)
                
                if contract_size >= 0.01:
                    self.current_btc = -contract_size  # 负数表示空仓
                    self.current_usdt -= amount
                    
                    trade = {
                        'timestamp': timestamp,
                        'side': 'short',
                        'price': price,
                        'amount': contract_size,
                        'usdt_used': amount,
                        'leverage': self.leverage
                    }
                    self.trades.append(trade)
                    print(f"📉 开空仓: {contract_size:.2f}张 @ ${price:.2f} (使用{amount} USDT)")
                    return True
                    
            elif signal == 'cover' and self.current_btc < 0:
                # 平空仓
                # 找到开仓价格（最近的开仓交易）
                entry_price = None
                for trade in reversed(self.trades):
                    if trade['side'] == 'short':
                        entry_price = trade['price']
                        break
                
                if entry_price:
                    pnl = (entry_price - price) * abs(self.current_btc)
                else:
                    pnl = 0
                
                # 找到开仓时使用的USDT
                entry_usdt = 0
                for trade in reversed(self.trades):
                    if trade['side'] == 'short':
                        entry_usdt = trade.get('usdt_used', 0)
                        break
                
                self.current_usdt += entry_usdt + pnl
                
                trade = {
                    'timestamp': timestamp,
                    'side': 'cover',
                    'price': price,
                    'amount': abs(self.current_btc),
                    'pnl': pnl,
                    'leverage': self.leverage
                }
                self.trades.append(trade)
                print(f"📈 平空仓: {abs(self.current_btc):.2f}张 @ ${price:.2f}, PnL: ${pnl:.2f}")
                self.current_btc = 0
                return True
                
        except Exception as e:
            print(f"❌ 交易执行失败: {e}")
            return False
        
        return False
    
    def update_equity_curve(self, price: float, timestamp: str):
        """更新权益曲线"""
        # 计算当前权益
        if self.current_btc > 0 and self.trades:  # 多仓
            unrealized_pnl = (price - self.trades[-1]['price']) * self.current_btc
        elif self.current_btc < 0 and self.trades:  # 空仓
            unrealized_pnl = (self.trades[-1]['price'] - price) * abs(self.current_btc)
        else:
            unrealized_pnl = 0
        
        current_equity = self.current_usdt + unrealized_pnl
        
        # 更新最大回撤
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        drawdown = (self.peak_equity - current_equity) / self.peak_equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': current_equity,
            'drawdown': drawdown
        })
    
    def run_backtest(self, days: int = 10) -> Dict[str, Any]:
        """运行回测"""
        print("🚀 开始简化SAR策略回测")
        print("="*60)
        
        # 获取历史数据
        data = self.get_historical_data(days)
        if data is None:
            return None
        
        print(f"\n📊 回测参数:")
        print(f"   初始资金: ${self.initial_usdt:,.2f}")
        print(f"   杠杆倍数: {self.leverage}x")
        print(f"   数据点数: {len(data)}")
        print(f"   时间范围: {data['timestamp'].iloc[0]} 到 {data['timestamp'].iloc[-1]}")
        
        # 运行回测
        print(f"\n🔄 开始回测...")
        signals_generated = 0
        trades_executed = 0
        
        for i in range(20, len(data)):  # 从第20个数据点开始
            # 获取当前数据窗口
            window_data = data.iloc[:i+1].copy()
            current_price = window_data['close'].iloc[-1]
            current_time = window_data['timestamp'].iloc[-1]
            
            # 同步策略持仓状态
            if self.current_btc > 0:
                self.strategy.current_position = "long"
                self.strategy.position_size = self.current_btc
                self.strategy.entry_price = self.trades[-1]['price'] if self.trades else current_price
            elif self.current_btc < 0:
                self.strategy.current_position = "short"
                self.strategy.position_size = abs(self.current_btc)
                self.strategy.entry_price = self.trades[-1]['price'] if self.trades else current_price
            else:
                self.strategy.current_position = None
                self.strategy.position_size = 0
                self.strategy.entry_price = 0
            
            # 分析信号
            signal_info = self.strategy.analyze_signal(window_data)
            signal = signal_info['signal']
            
            if signal in ['buy', 'sell', 'short', 'cover']:
                signals_generated += 1
                print(f"\n📊 {current_time} - 价格: ${current_price:.2f}")
                print(f"   信号: {signal} - {signal_info['reason']}")
                print(f"   SAR: ${signal_info.get('sar', 0):.2f}")
                print(f"   1小时趋势: {signal_info.get('trend', 'unknown')}")
                
                # 执行交易 - 使用回测系统自己的execute_trade方法
                if self.execute_trade(signal, current_price, str(current_time)):
                    trades_executed += 1
            
            # 更新权益曲线
            self.update_equity_curve(current_price, str(current_time))
        
        # 计算最终权益
        final_price = data['close'].iloc[-1]
        if self.current_btc != 0 and self.trades:
            # 平仓
            if self.current_btc > 0:
                pnl = (final_price - self.trades[-1]['price']) * self.current_btc
                self.current_usdt += self.trades[-1]['usdt_used'] + pnl
            else:
                pnl = (self.trades[-1]['price'] - final_price) * abs(self.current_btc)
                self.current_usdt += self.trades[-1]['usdt_used'] + pnl
            
            self.current_btc = 0
        
        final_equity = self.current_usdt
        
        # 计算性能指标
        total_return = (final_equity - self.initial_usdt) / self.initial_usdt
        winning_trades = len([t for t in self.trades if 'pnl' in t and t['pnl'] > 0])
        losing_trades = len([t for t in self.trades if 'pnl' in t and t['pnl'] < 0])
        total_trades = winning_trades + losing_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 计算夏普比率
        if len(self.equity_curve) > 1:
            returns = pd.Series([self.equity_curve[i]['equity'] / self.equity_curve[i-1]['equity'] - 1 
                               for i in range(1, len(self.equity_curve))])
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(365 * 24 * 4) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        print(f"\n📈 回测完成!")
        print(f"   信号生成: {signals_generated}次")
        print(f"   交易执行: {trades_executed}次")
        print(f"   最终权益: ${final_equity:,.2f}")
        print(f"   总收益率: {total_return:.2%}")
        print(f"   最大回撤: {self.max_drawdown:.2%}")
        print(f"   胜率: {win_rate:.2%}")
        print(f"   夏普比率: {sharpe_ratio:.2f}")
        
        return {
            'initial_usdt': self.initial_usdt,
            'final_equity': final_equity,
            'total_return': total_return,
            'max_drawdown': self.max_drawdown,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'signals_generated': signals_generated,
            'trades_executed': trades_executed
        }
    
    def generate_report(self, results: Dict[str, Any], filename: str = None):
        """生成回测报告"""
        # 创建报告文件夹
        report_dir = "reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simple_sar_backtest_report_{timestamp}.md"
        
        # 将文件保存到reports文件夹
        filepath = os.path.join(report_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 📊 简化SAR策略回测报告\n\n")
            
            # 回测概览
            f.write("## 🎯 回测概览\n\n")
            f.write("| 指标 | 数值 | 说明 |\n")
            f.write("|------|------|------|\n")
            f.write(f"| **初始资金** | ${results['initial_usdt']:,.2f} | 回测开始时的资金 |\n")
            f.write(f"| **最终权益** | ${results['final_equity']:,.2f} | 回测结束时的权益 |\n")
            f.write(f"| **总收益率** | {results['total_return']:.2%} | 总收益百分比 |\n")
            f.write(f"| **最大回撤** | {results['max_drawdown']:.2%} | 最大亏损百分比 |\n")
            f.write(f"| **夏普比率** | {results['sharpe_ratio']:.2f} | 风险调整后收益 |\n")
            
            # 交易统计
            f.write("\n## 📈 交易统计\n\n")
            f.write("| 指标 | 数值 | 说明 |\n")
            f.write("|------|------|------|\n")
            f.write(f"| **总交易次数** | {results['total_trades']} | 执行的总交易数 |\n")
            f.write(f"| **盈利交易** | {results['winning_trades']} | 盈利的交易数 |\n")
            f.write(f"| **亏损交易** | {results['losing_trades']} | 亏损的交易数 |\n")
            f.write(f"| **胜率** | {results['win_rate']:.2%} | 盈利交易占比 |\n")
            f.write(f"| **信号生成** | {results['signals_generated']} | 策略生成的信号数 |\n")
            f.write(f"| **交易执行** | {results['trades_executed']} | 实际执行的交易数 |\n")
            
            # 交易明细
            if results['trades']:
                f.write("\n## 📋 交易明细\n\n")
                f.write("| 时间 | 方向 | 价格 | 数量 | 盈亏 | 杠杆 |\n")
                f.write("|------|------|------|------|------|------|\n")
                
                for trade in results['trades']:
                    if 'pnl' in trade:
                        pnl_str = f"${trade['pnl']:.2f}" if trade['pnl'] != 0 else "-"
                    else:
                        pnl_str = "-"
                    
                    f.write(f"| {trade['timestamp']} | {trade['side']} | "
                           f"${trade['price']:.2f} | {trade['amount']:.2f} | "
                           f"{pnl_str} | {trade.get('leverage', 2)}x |\n")
            
            # 策略参数
            f.write("\n## ⚙️ 策略参数\n\n")
            f.write("| 参数 | 数值 | 说明 |\n")
            f.write("|------|------|------|\n")
            f.write("| **K线周期** | 15m | 数据时间周期 |\n")
            f.write("| **杠杆倍数** | 2x | 交易杠杆 |\n")
            f.write("| **初始加速因子** | 0.02 | SAR参数 |\n")
            f.write("| **加速因子增量** | 0.02 | SAR参数 |\n")
            f.write("| **最大加速因子** | 0.2 | SAR参数 |\n")
            f.write("| **趋势确认** | 1小时线 | 趋势过滤 |\n")
            f.write("| **止盈止损** | 无 | 仅依靠SAR信号 |\n")
        
        print(f"\n📁 回测报告已保存: {filepath}")
        return filepath


def main():
    """主函数"""
    print("🚀 简化SAR策略回测系统")
    print("="*60)
    
    # 创建回测系统
    backtest = SimpleSARBacktest(
        initial_usdt=10000,
        leverage=2
    )
    
    # 运行回测
    results = backtest.run_backtest(days=10)
    
    if results:
        # 生成报告
        report_file = backtest.generate_report(results)
        print(f"\n✅ 回测完成! 报告已保存到: {report_file}")
    else:
        print("\n❌ 回测失败!")


if __name__ == "__main__":
    main()
