#!/usr/bin/env python3
"""
简化SAR策略
- 基于15分钟线SAR信号
- 1小时线趋势确认
- 2倍杠杆合约交易
- 无止盈止损，仅依靠SAR
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from okx_http_client import OKXHTTPClient


class SimpleSARStrategy:
    """简化SAR策略"""
    
    def __init__(self, client: OKXHTTPClient, inst_id: str = "BTC-USDT-SWAP", leverage: float = 2):
        self.client = client
        self.inst_id = inst_id
        self.leverage = leverage
        
        # SAR参数
        self.af_start = 0.02
        self.af_increment = 0.02
        self.af_maximum = 0.2
        
        # 交易状态
        self.current_position = None  # 'long', 'short', None
        self.position_size = 0
        self.entry_price = 0
        self.trades = []
        self.initial_usdt = 1000
        self.current_usdt = 1000
        
        print(f"🚀 简化SAR策略初始化")
        print(f"   交易对: {self.inst_id}")
        print(f"   杠杆倍数: {self.leverage}x")
        print(f"   SAR参数: AF={self.af_start}, 增量={self.af_increment}, 最大={self.af_maximum}")
    
    def get_market_data(self, inst_id: str, period: str, limit: str = "100") -> Optional[pd.DataFrame]:
        """获取市场数据"""
        try:
            result = self.client.get_candles(inst_id, period, limit)
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
                
                return df
            else:
                print(f"❌ 获取{period}数据失败: {result}")
                return None
        except Exception as e:
            print(f"❌ 获取{period}数据异常: {e}")
            return None
    
    def calculate_sar(self, data: pd.DataFrame) -> pd.Series:
        """计算抛物线SAR指标"""
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        sar = np.zeros(len(data))
        af = self.af_start
        ep = high[0] if high[0] > low[0] else low[0]
        trend = 1 if high[0] > low[0] else -1
        sar[0] = low[0] if trend == 1 else high[0]
        
        for i in range(1, len(data)):
            if trend == 1:  # 上升趋势
                sar[i] = sar[i-1] + af * (ep - sar[i-1])
                if low[i] <= sar[i]:
                    trend = -1
                    sar[i] = ep
                    ep = low[i]
                    af = self.af_start
                else:
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + self.af_increment, self.af_maximum)
            else:  # 下降趋势
                sar[i] = sar[i-1] + af * (ep - sar[i-1])
                if high[i] >= sar[i]:
                    trend = 1
                    sar[i] = ep
                    ep = high[i]
                    af = self.af_start
                else:
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + self.af_increment, self.af_maximum)
        
        return pd.Series(sar, index=data.index)
    
    def get_hourly_sar(self) -> Dict[str, Any]:
        """获取1小时线SAR信号"""
        try:
            # 获取1小时线数据
            hourly_data = self.get_market_data(self.inst_id, "1H", "50")
            if hourly_data is None or len(hourly_data) < 20:
                return {"signal": "neutral", "sar": 0}
            
            # 计算1小时线SAR
            hourly_sar = self.calculate_sar(hourly_data)
            current_price = hourly_data['close'].iloc[-1]
            current_sar = hourly_sar.iloc[-1]
            prev_sar = hourly_sar.iloc[-2]
            
            # 判断1小时SAR信号 - 简化条件
            if current_price > current_sar:
                return {"signal": "buy", "sar": current_sar}
            elif current_price < current_sar:
                return {"signal": "sell", "sar": current_sar}
            else:
                return {"signal": "neutral", "sar": current_sar}
                
        except Exception as e:
            print(f"⚠️ 获取1小时SAR失败: {e}")
            return {"signal": "neutral", "sar": 0}
    
    def analyze_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析交易信号"""
        try:
            if len(data) < 20:
                return {"signal": "hold", "reason": "数据不足"}
            
            # 计算15分钟SAR
            sar = self.calculate_sar(data)
            current_price = data['close'].iloc[-1]
            current_sar = sar.iloc[-1]
            prev_sar = sar.iloc[-2]
            
            # 获取1小时SAR信号
            hourly_sar_info = self.get_hourly_sar()
            hourly_signal = hourly_sar_info['signal']
            hourly_sar = hourly_sar_info['sar']
            
            # 如果有持仓，检查15分钟SAR反转信号
            if self.current_position is not None:
                # 计算持仓盈亏
                if self.current_position == "long":
                    pnl_ratio = (current_price - self.entry_price) / self.entry_price
                    # 多仓反转条件：价格跌破SAR 或 盈利超过5%
                    if current_price < current_sar or pnl_ratio > 0.05:
                        return {
                            "signal": "sell",
                            "reason": f"多仓SAR反转信号 (盈亏: {pnl_ratio:.2%})",
                            "price": current_price,
                            "sar": current_sar,
                            "hourly_sar": hourly_sar,
                            "hourly_signal": hourly_signal
                        }
                elif self.current_position == "short":
                    pnl_ratio = (self.entry_price - current_price) / self.entry_price
                    # 空仓反转条件：价格突破SAR 或 盈利超过5%
                    if current_price > current_sar or pnl_ratio > 0.05:
                        return {
                            "signal": "buy",
                            "reason": f"空仓SAR反转信号 (盈亏: {pnl_ratio:.2%})",
                            "price": current_price,
                            "sar": current_sar,
                            "hourly_sar": hourly_sar,
                            "hourly_signal": hourly_signal
                        }
                
                return {
                    "signal": "hold",
                    "reason": "持仓中，SAR无反转",
                    "price": current_price,
                    "sar": current_sar,
                    "hourly_sar": hourly_sar,
                    "hourly_signal": hourly_signal
                }
            
            # 无持仓时，需要15分钟SAR和1小时SAR双重确认
            else:
                # 15分钟SAR突破信号 - 简化条件
                if current_price > current_sar:
                    # 15分钟看涨信号
                    if hourly_signal == "buy":
                        return {
                            "signal": "buy",
                            "reason": "15分钟SAR突破+1小时SAR确认",
                            "price": current_price,
                            "sar": current_sar,
                            "hourly_sar": hourly_sar,
                            "hourly_signal": hourly_signal
                        }
                    else:
                        return {
                            "signal": "hold",
                            "reason": f"15分钟SAR突破但1小时SAR不确认({hourly_signal})",
                            "price": current_price,
                            "sar": current_sar,
                            "hourly_sar": hourly_sar,
                            "hourly_signal": hourly_signal
                        }
                
                elif current_price < current_sar:
                    # 15分钟看跌信号
                    if hourly_signal == "sell":
                        return {
                            "signal": "sell",
                            "reason": "15分钟SAR跌破+1小时SAR确认",
                            "price": current_price,
                            "sar": current_sar,
                            "hourly_sar": hourly_sar,
                            "hourly_signal": hourly_signal
                        }
                    else:
                        return {
                            "signal": "hold",
                            "reason": f"15分钟SAR跌破但1小时SAR不确认({hourly_signal})",
                            "price": current_price,
                            "sar": current_sar,
                            "hourly_sar": hourly_sar,
                            "hourly_signal": hourly_signal
                        }
                
                else:
                    return {
                        "signal": "hold",
                        "reason": "15分钟SAR无信号",
                        "price": current_price,
                        "sar": current_sar,
                        "hourly_sar": hourly_sar,
                        "hourly_signal": hourly_signal
                    }
                
        except Exception as e:
            print(f"❌ 信号分析错误: {e}")
            return {"signal": "hold", "reason": f"分析错误: {e}"}
    
    def calculate_contract_size(self, usdt_amount: float, price: float) -> float:
        """计算合约数量"""
        contract_size = usdt_amount / price
        # 按步长0.1调整，确保不小于0.01
        contract_size = max(0.01, round(contract_size * 10) / 10)
        return contract_size
    
    def execute_trade(self, signal: str, price: float) -> bool:
        """执行交易"""
        try:
            if signal == "buy" and self.current_position != "long":
                # 平空仓（如果有）
                if self.current_position == "short":
                    self.close_position(price)
                
                # 开多仓 - 使用固定1000 USDT
                amount = 1000 * self.leverage  # 1000 USDT * 2倍杠杆 = 2000 USDT
                contract_size = self.calculate_contract_size(amount, price)
                
                if contract_size >= 0.01:
                    self.current_position = "long"
                    self.position_size = contract_size
                    self.entry_price = price
                    self.current_usdt -= amount
                    
                    trade = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'side': 'buy',
                        'price': price,
                        'amount': contract_size,
                        'usdt_used': amount,
                        'leverage': self.leverage
                    }
                    self.trades.append(trade)
                    print(f"📈 开多仓: {contract_size:.2f}张 @ ${price:.2f} (使用{amount} USDT)")
                    return True
                    
            elif signal == "sell" and self.current_position != "short":
                # 平多仓（如果有）
                if self.current_position == "long":
                    self.close_position(price)
                
                # 开空仓 - 使用固定1000 USDT
                amount = 1000 * self.leverage  # 1000 USDT * 2倍杠杆 = 2000 USDT
                contract_size = self.calculate_contract_size(amount, price)
                
                if contract_size >= 0.01:
                    self.current_position = "short"
                    self.position_size = contract_size
                    self.entry_price = price
                    self.current_usdt -= amount
                    
                    trade = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'side': 'sell',
                        'price': price,
                        'amount': contract_size,
                        'usdt_used': amount,
                        'leverage': self.leverage
                    }
                    self.trades.append(trade)
                    print(f"📉 开空仓: {contract_size:.2f}张 @ ${price:.2f} (使用{amount} USDT)")
                    return True
                    
        except Exception as e:
            print(f"❌ 交易执行失败: {e}")
            return False
        
        return False
    
    def close_position(self, price: float) -> bool:
        """平仓"""
        try:
            if self.current_position is None:
                return False
            
            # 计算盈亏
            if self.current_position == "long":
                pnl = (price - self.entry_price) * self.position_size
            else:  # short
                pnl = (self.entry_price - price) * self.position_size
            
            # 更新资金
            self.current_usdt += self.trades[-1]['usdt_used'] + pnl
            
            # 记录平仓交易
            trade = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'side': 'close',
                'price': price,
                'amount': self.position_size,
                'pnl': pnl,
                'leverage': self.leverage
            }
            self.trades.append(trade)
            
            print(f"🔄 平仓: {self.position_size:.2f}张 @ ${price:.2f}, PnL: ${pnl:.2f}")
            
            # 重置持仓
            self.current_position = None
            self.position_size = 0
            self.entry_price = 0
            
            return True
            
        except Exception as e:
            print(f"❌ 平仓失败: {e}")
            return False
    
    def get_current_position(self) -> Dict[str, Any]:
        """获取当前持仓信息"""
        return {
            'position': self.current_position,
            'size': self.position_size,
            'entry_price': self.entry_price,
            'current_usdt': self.current_usdt
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """生成策略报告"""
        # 计算最终权益
        final_equity = self.current_usdt
        if self.current_position is not None:
            # 如果有持仓，按当前价格计算未实现盈亏
            try:
                data = self.get_market_data(self.inst_id, "15m", "1")
                if data is not None:
                    current_price = data['close'].iloc[-1]
                    if self.current_position == "long":
                        unrealized_pnl = (current_price - self.entry_price) * self.position_size
                    else:
                        unrealized_pnl = (self.entry_price - current_price) * self.position_size
                    final_equity += unrealized_pnl
            except:
                pass
        
        # 计算性能指标
        total_return = (final_equity - self.initial_usdt) / self.initial_usdt
        winning_trades = len([t for t in self.trades if 'pnl' in t and t['pnl'] > 0])
        losing_trades = len([t for t in self.trades if 'pnl' in t and t['pnl'] < 0])
        total_trades = winning_trades + losing_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            "strategy_info": {
                "name": "简化SAR策略",
                "inst_id": self.inst_id,
                "leverage": self.leverage,
                "af_start": self.af_start,
                "af_increment": self.af_increment,
                "af_maximum": self.af_maximum
            },
            "performance": {
                "initial_usdt": self.initial_usdt,
                "final_equity": final_equity,
                "total_return": total_return,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "current_position": self.current_position,
                "position_size": self.position_size,
                "entry_price": self.entry_price
            },
            "trade_history": self.trades
        }
