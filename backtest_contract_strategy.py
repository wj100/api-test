#!/usr/bin/env python3
"""
合约策略历史数据回测系统
使用过去一个月的数据回测增强版SAR策略
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
from trading_strategies.enhanced_sar_strategy_contract import EnhancedSARStrategyContract


class ContractBacktestSystem:
    """合约策略回测系统"""
    
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
        self.strategy = EnhancedSARStrategyContract(
            client=client,
            kline_period='15m',
            af_start=0.02,
            af_increment=0.02,
            af_maximum=0.2,
            take_profit_ratio=0.02,
            stop_loss_ratio=0.01,
            atr_period=14,
            volume_threshold=0.0,
            initial_usdt=initial_usdt,
            leverage=leverage
        )
    
    def get_historical_data(self, days: int = 30) -> pd.DataFrame:
        """获取历史数据"""
        print(f"📊 获取过去{days}天的历史数据...")
        
        # 计算开始时间
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 获取15分钟K线数据 - 使用最大数据量
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
                
                # 转换时间戳
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
                # 开多仓
                amount = self.current_usdt * 0.2 * self.leverage
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
                    print(f"📈 开多仓: {contract_size:.2f}张 @ ${price:.2f}")
                    return True
                    
            elif signal == 'sell' and self.current_btc > 0:
                # 平多仓
                pnl = (price - self.trades[-1]['price']) * self.current_btc
                self.current_usdt += self.trades[-1]['usdt_used'] + pnl
                
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
                # 开空仓
                amount = self.current_usdt * 0.2 * self.leverage
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
                    print(f"📉 开空仓: {contract_size:.2f}张 @ ${price:.2f}")
                    return True
                    
            elif signal == 'cover' and self.current_btc < 0:
                # 平空仓
                pnl = (self.trades[-1]['price'] - price) * abs(self.current_btc)
                self.current_usdt += self.trades[-1]['usdt_used'] + pnl
                
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
        if self.current_btc > 0:  # 多仓
            unrealized_pnl = (price - self.trades[-1]['price']) * self.current_btc
        elif self.current_btc < 0:  # 空仓
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
    
    def run_backtest(self, days: int = 30) -> Dict[str, Any]:
        """运行回测"""
        print("🚀 开始合约策略回测")
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
        
        for i in range(20, len(data)):  # 从第20个数据点开始，确保有足够的历史数据
            # 获取当前数据窗口
            window_data = data.iloc[:i+1].copy()
            current_price = window_data['close'].iloc[-1]
            current_time = window_data['timestamp'].iloc[-1]
            
            # 分析信号
            signal_info = self.strategy.analyze_signal(window_data)
            signal = signal_info['signal']
            
            if signal in ['buy', 'sell', 'short', 'cover']:
                signals_generated += 1
                print(f"\n📊 {current_time} - 价格: ${current_price:.2f}")
                print(f"   信号: {signal} - {signal_info['reason']}")
                
                # 执行交易
                if self.execute_trade(signal, current_price, str(current_time)):
                    trades_executed += 1
            
            # 更新权益曲线
            self.update_equity_curve(current_price, str(current_time))
        
        # 计算最终权益
        final_price = data['close'].iloc[-1]
        if self.current_btc != 0:
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
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"contract_backtest_report_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# 📊 合约策略回测报告\n\n")
            
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
            f.write("| **止盈比例** | 2% | 止盈设置 |\n")
            f.write("| **止损比例** | 1% | 止损设置 |\n")
            f.write("| **ATR周期** | 14 | 波动率计算周期 |\n")
            f.write("| **成交量阈值** | 0.0x | 成交量过滤 |\n")
        
        print(f"\n📁 回测报告已保存: {filename}")
        return filename


def main():
    """主函数"""
    print("🚀 合约策略历史数据回测系统")
    print("="*60)
    
    # 创建回测系统
    backtest = ContractBacktestSystem(
        initial_usdt=10000,
        leverage=2
    )
    
    # 运行回测 - 使用最近10天数据
    results = backtest.run_backtest(days=10)
    
    if results:
        # 生成报告
        report_file = backtest.generate_report(results)
        print(f"\n✅ 回测完成! 报告已保存到: {report_file}")
    else:
        print("\n❌ 回测失败!")


if __name__ == "__main__":
    main()
