#!/usr/bin/env python3
"""
增强版SAR策略 - 合约交易版本
支持2倍杠杆、真正做空、止盈止损
"""
import sys
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import time
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from okx_http_client import OKXHTTPClient
from trading_strategies.base_strategy import BaseStrategy
from utils.advanced_indicators import AdvancedIndicators

class EnhancedSARStrategy:
    """增强版SAR策略 - 合约交易版本"""

    def __init__(self, config_file: str = None):
        """初始化策略"""
        # 加载配置
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), "config.json")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 初始化客户端
        self.client = OKXHTTPClient()
        
        # 策略参数
        self.inst_id = self.config["trading"]["inst_id"]
        self.kline_period = self.config["trading"]["kline_period"]
        self.leverage = self.config["investment"]["leverage"]
        self.initial_usdt = self.config["investment"]["initial_usdt"]
        
        # SAR参数
        self.af_start = self.config["sar_params"]["af_start"]
        self.af_increment = self.config["sar_params"]["af_increment"]
        self.af_maximum = self.config["sar_params"]["af_maximum"]
        
        # 风险管理
        self.take_profit_ratio = self.config["risk_management"]["take_profit_ratio"]
        self.stop_loss_ratio = self.config["risk_management"]["stop_loss_ratio"]
        self.atr_period = self.config["risk_management"]["atr_period"]
        
        # 过滤器
        self.volume_threshold = self.config["filters"]["volume_threshold"]
        self.volatility_threshold = self.config["filters"]["volatility_threshold"]
        self.trend_confirmation = self.config["filters"]["trend_confirmation"]
        
        # 交易状态
        self.current_position = None
        self.position_size = 0
        self.entry_price = 0
        self.trades = []
        self.current_usdt = self.initial_usdt
        
        # 技术指标计算器
        self.indicators = AdvancedIndicators()
        
        print(f"🚀 增强版SAR策略初始化完成")
        print(f"   交易对: {self.inst_id}")
        print(f"   杠杆: {self.leverage}x")
        print(f"   投资金额: {self.initial_usdt} USDT")
        print(f"   SAR参数: AF={self.af_start}, 增量={self.af_increment}, 最大={self.af_maximum}")

    def get_market_data(self, inst_id: str, bar: str, limit: str) -> pd.DataFrame:
        """获取K线数据"""
        try:
            result = self.client.get_candles(inst_id, bar, limit)
            if result and result.get('code') == '0':
                data = result['data']
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'vol', 'volCcy', 'volCcy2', 'confirm'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df[['open', 'high', 'low', 'close', 'vol', 'volCcy', 'volCcy2']] = df[['open', 'high', 'low', 'close', 'vol', 'volCcy', 'volCcy2']].astype(float)
                df = df.sort_values('timestamp')
                return df
            else:
                print(f"❌ 获取K线数据失败: {result}")
                return None
        except Exception as e:
            print(f"获取K线数据异常: {e}")
            return None

    def calculate_sar(self, data: pd.DataFrame) -> pd.Series:
        """计算抛物线SAR指标"""
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        sar = [0] * len(data)
        ep = 0  # Extreme Point
        af = self.af_start  # Acceleration Factor
        trend = 0  # 1 for uptrend, -1 for downtrend

        # 初始化前两个SAR值
        if close[1] > close[0]:
            trend = 1
            sar[0] = low[0]
            ep = high[0]
        else:
            trend = -1
            sar[0] = high[0]
            ep = low[0]

        sar[1] = sar[0]

        for i in range(2, len(data)):
            if trend == 1:  # 上升趋势
                sar[i] = sar[i-1] + af * (ep - sar[i-1])
                if sar[i] > low[i]:
                    sar[i] = low[i]
                if sar[i] > low[i-1]:
                    sar[i] = low[i-1]
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + self.af_increment, self.af_maximum)
                if low[i] < sar[i]:
                    trend = -1
                    sar[i] = ep
                    ep = low[i]
                    af = self.af_start
            else:  # 下降趋势
                sar[i] = sar[i-1] + af * (ep - sar[i-1])
                if sar[i] < high[i]:
                    sar[i] = high[i]
                if sar[i] < high[i-1]:
                    sar[i] = high[i-1]
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + self.af_increment, self.af_maximum)
                if high[i] >= sar[i]:
                    trend = 1
                    sar[i] = ep
                    ep = high[i]
                    af = self.af_start

        return pd.Series(sar, index=data.index)

    def get_trend_filter(self, data: pd.DataFrame) -> Dict[str, Any]:
        """获取趋势过滤器"""
        try:
            # 获取1小时线数据
            hourly_data = self.get_market_data(self.inst_id, "1H", "50")
            if hourly_data is None or len(hourly_data) < 20:
                return {"trend": "neutral", "strength": 0}

            # 计算1小时线SAR
            hourly_sar = self.calculate_sar(hourly_data)
            current_price = hourly_data['close'].iloc[-1]
            current_sar = hourly_sar.iloc[-1]

            # 判断1小时趋势
            if current_price > current_sar:
                return {"trend": "bullish", "strength": 0.8}
            elif current_price < current_sar:
                return {"trend": "bearish", "strength": 0.8}
            else:
                return {"trend": "neutral", "strength": 0.5}

        except Exception as e:
            print(f"⚠️ 趋势过滤器失败: {e}")
            return {"trend": "neutral", "strength": 0.5}

    def get_volatility_filter(self, data: pd.DataFrame) -> bool:
        """获取波动率过滤器"""
        try:
            if len(data) < self.atr_period + 1:
                return False

            # 计算ATR
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values

            tr = np.maximum(high[1:] - low[1:], 
                           np.maximum(np.abs(high[1:] - close[:-1]), 
                                    np.abs(low[1:] - close[:-1])))
            
            atr = np.mean(tr[-self.atr_period:])
            current_price = close[-1]
            volatility = atr / current_price

            return volatility >= self.volatility_threshold

        except Exception as e:
            print(f"⚠️ 波动率过滤器失败: {e}")
            return False

    def get_volume_confirmation(self, data: pd.DataFrame) -> bool:
        """获取成交量确认"""
        try:
            if len(data) < 10:
                return True

            # 计算平均成交量
            avg_volume = data['vol'].rolling(window=10).mean().iloc[-1]
            current_volume = data['vol'].iloc[-1]

            # 成交量放大倍数
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            return volume_ratio >= self.volume_threshold

        except Exception as e:
            print(f"⚠️ 成交量确认失败: {e}")
            return True

    def analyze_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析交易信号"""
        try:
            if len(data) < 20:
                return {"signal": "hold", "reason": "数据不足"}

            # 计算SAR
            sar = self.calculate_sar(data)
            current_price = data['close'].iloc[-1]
            current_sar = sar.iloc[-1]
            prev_sar = sar.iloc[-2]

            # 获取过滤器结果
            trend_filter = self.get_trend_filter(data)
            volatility_filter = self.get_volatility_filter(data)
            volume_filter = self.get_volume_confirmation(data)

            # 如果有持仓，检查止盈止损
            if self.current_position is not None:
                pnl_ratio = 0
                if self.current_position == "long":
                    pnl_ratio = (current_price - self.entry_price) / self.entry_price
                elif self.current_position == "short":
                    pnl_ratio = (self.entry_price - current_price) / self.entry_price

                # 止盈止损检查
                if pnl_ratio >= self.take_profit_ratio:
                    return {
                        "signal": "close",
                        "reason": f"止盈触发 ({pnl_ratio:.2%})",
                        "price": current_price,
                        "sar": current_sar,
                        "pnl_ratio": pnl_ratio
                    }
                elif pnl_ratio <= -self.stop_loss_ratio:
                    return {
                        "signal": "close",
                        "reason": f"止损触发 ({pnl_ratio:.2%})",
                        "price": current_price,
                        "sar": current_sar,
                        "pnl_ratio": pnl_ratio
                    }

                # SAR反转信号
                if (self.current_position == "long" and current_price < current_sar) or \
                   (self.current_position == "short" and current_price > current_sar):
                    return {
                        "signal": "close",
                        "reason": "SAR反转信号",
                        "price": current_price,
                        "sar": current_sar,
                        "pnl_ratio": pnl_ratio
                    }

                return {
                    "signal": "hold",
                    "reason": "持仓中，无反转信号",
                    "price": current_price,
                    "sar": current_sar,
                    "pnl_ratio": pnl_ratio
                }

            # 无持仓时，检查开仓信号
            else:
                # 检查所有过滤器
                if not volatility_filter:
                    return {
                        "signal": "hold",
                        "reason": "波动率不足",
                        "price": current_price,
                        "sar": current_sar
                    }

                if not volume_filter:
                    return {
                        "signal": "hold",
                        "reason": "成交量不足",
                        "price": current_price,
                        "sar": current_sar
                    }

                # SAR突破信号
                if current_price > current_sar and prev_sar >= prev_sar:
                    if trend_filter["trend"] == "bullish":
                        return {
                            "signal": "buy",
                            "reason": "SAR突破+趋势确认",
                            "price": current_price,
                            "sar": current_sar,
                            "trend": trend_filter["trend"]
                        }

                elif current_price < current_sar and prev_sar <= prev_sar:
                    if trend_filter["trend"] == "bearish":
                        return {
                            "signal": "sell",
                            "reason": "SAR跌破+趋势确认",
                            "price": current_price,
                            "sar": current_sar,
                            "trend": trend_filter["trend"]
                        }

                return {
                    "signal": "hold",
                    "reason": "等待信号",
                    "price": current_price,
                    "sar": current_sar
                }

        except Exception as e:
            print(f"❌ 信号分析错误: {e}")
            return {"signal": "hold", "reason": f"分析错误: {e}"}

    def calculate_position_size(self, price: float) -> float:
        """计算仓位大小"""
        try:
            # 使用固定1000 USDT
            usdt_balance = self.initial_usdt
            
            # 计算合约数量
            amount = usdt_balance * 1.0 * self.leverage  # 使用100%资金
            contract_size = amount / price
            
            # 按步长0.1调整，确保不小于0.01
            contract_size = max(0.01, round(contract_size * 10) / 10)
            
            return contract_size

        except Exception as e:
            print(f"❌ 仓位计算错误: {e}")
            return 0.01

    def execute_trade(self, signal: str, price: float) -> bool:
        """执行交易"""
        try:
            if signal == "buy" and self.current_position != "long":
                # 平空仓（如果有）
                if self.current_position == "short":
                    self.close_position(price)

                # 开多仓
                contract_size = self.calculate_position_size(price)
                
                if contract_size >= 0.01:
                    self.current_position = "long"
                    self.position_size = contract_size
                    self.entry_price = price
                    
                    trade = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'side': 'buy',
                        'price': price,
                        'amount': contract_size,
                        'leverage': self.leverage
                    }
                    self.trades.append(trade)
                    print(f"📈 开多仓: {contract_size:.2f}张 @ ${price:.2f}")
                    return True

            elif signal == "sell" and self.current_position != "short":
                # 平多仓（如果有）
                if self.current_position == "long":
                    self.close_position(price)

                # 开空仓
                contract_size = self.calculate_position_size(price)
                
                if contract_size >= 0.01:
                    self.current_position = "short"
                    self.position_size = contract_size
                    self.entry_price = price
                    
                    trade = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'side': 'sell',
                        'price': price,
                        'amount': contract_size,
                        'leverage': self.leverage
                    }
                    self.trades.append(trade)
                    print(f"📉 开空仓: {contract_size:.2f}张 @ ${price:.2f}")
                    return True

            elif signal == "close" and self.current_position is not None:
                self.close_position(price)
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

            pnl = 0
            if self.current_position == "long":
                pnl = (price - self.entry_price) * self.position_size
                side = "sell"
                print(f"📉 平多仓: {self.position_size:.2f}张 @ ${price:.2f}, PnL: ${pnl:.2f}")
            elif self.current_position == "short":
                pnl = (self.entry_price - price) * self.position_size
                side = "buy"
                print(f"📈 平空仓: {self.position_size:.2f}张 @ ${price:.2f}, PnL: ${pnl:.2f}")

            trade = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'side': side + "_close",
                'price': price,
                'amount': self.position_size,
                'pnl': pnl,
                'leverage': self.leverage
            }
            self.trades.append(trade)

            self.current_position = None
            self.position_size = 0
            self.entry_price = 0
            return True

        except Exception as e:
            print(f"❌ 平仓失败: {e}")
            return False

    def run(self):
        """运行策略"""
        print(f"\n🚀 开始运行增强版SAR策略")
        print(f"   交易对: {self.inst_id}")
        print(f"   杠杆: {self.leverage}x")
        print(f"   投资金额: {self.initial_usdt} USDT")
        print("按 Ctrl+C 停止策略")

        try:
            while True:
                # 获取市场数据
                data = self.get_market_data(self.inst_id, self.kline_period, "100")
                if data is None or len(data) < 20:
                    print("❌ 无法获取市场数据")
                    time.sleep(60)
                    continue

                # 分析信号
                signal_info = self.analyze_signal(data)
                signal = signal_info['signal']

                if signal in ['buy', 'sell', 'close']:
                    print(f"\n📊 {datetime.now().strftime('%H:%M:%S')} - 价格: ${signal_info['price']:.2f}")
                    print(f"   信号: {signal} - {signal_info['reason']}")
                    print(f"   SAR: ${signal_info.get('sar', 0):.2f}")

                    # 执行交易
                    self.execute_trade(signal, signal_info['price'])

                time.sleep(60)  # 每分钟检查一次

        except KeyboardInterrupt:
            print(f"\n⏹️ 策略已停止")
            if self.current_position:
                print(f"⚠️ 当前持仓: {self.current_position} {self.position_size:.2f}张")
                print("请手动平仓或等待下次信号")

    def generate_report(self) -> Dict[str, Any]:
        """生成策略报告"""
        total_trades = len(self.trades)
        winning_trades = sum(1 for trade in self.trades if trade.get('pnl', 0) > 0)
        losing_trades = sum(1 for trade in self.trades if trade.get('pnl', 0) < 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        return {
            "strategy_info": {
                "name": "增强版SAR策略",
                "kline_period": self.kline_period,
                "af_start": self.af_start,
                "af_increment": self.af_increment,
                "af_maximum": self.af_maximum,
                "take_profit_ratio": self.take_profit_ratio,
                "stop_loss_ratio": self.stop_loss_ratio,
                "atr_period": self.atr_period,
                "volume_threshold": self.volume_threshold,
                "leverage": self.leverage,
                "inst_id": self.inst_id
            },
            "performance": {
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "runtime_hours": 0,
                "initial_balance": self.initial_usdt,
                "final_balance": self.current_usdt,
                "total_return": (self.current_usdt - self.initial_usdt) / self.initial_usdt,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "current_position": self.current_position,
                "position_size": self.position_size,
                "entry_price": self.entry_price,
                "leverage_used": self.leverage
            },
            "trade_history": self.trades
        }

if __name__ == "__main__":
    strategy = EnhancedSARStrategy()
    strategy.run()
