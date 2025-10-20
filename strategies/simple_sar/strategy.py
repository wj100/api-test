#!/usr/bin/env python3
"""
简化SAR策略
- 基于15分钟线SAR信号
- 1小时线趋势确认
- 2倍杠杆合约交易
- 无止盈止损，仅依靠SAR
"""
import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from okx_http_client import OKXHTTPClient

class SimpleSARStrategy:
    """简化SAR策略"""

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
        self.leverage = self.config["investment"]["leverage"]
        self.initial_usdt = self.config["investment"]["initial_usdt"]
        
        # SAR参数
        self.af_start = self.config["sar_params"]["af_start"]
        self.af_increment = self.config["sar_params"]["af_increment"]
        self.af_maximum = self.config["sar_params"]["af_maximum"]
        
        # 交易状态
        self.current_position = None  # 'long', 'short', None
        self.position_size = 0
        self.entry_price = 0
        self.trades = []
        self.current_usdt = self.initial_usdt

        print(f"🚀 简化SAR策略初始化")
        print(f"   交易对: {self.inst_id}")
        print(f"   杠杆倍数: {self.leverage}x")
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

        sar[1] = sar[0] # 第二个SAR值通常与第一个相同

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

            pnl = 0
            if self.current_position == "long":
                pnl = (price - self.entry_price) * self.position_size
                side = "sell"
                print(f"📉 平多仓: {self.position_size:.2f}张 @ ${price:.2f}, PnL: ${pnl:.2f}")
            elif self.current_position == "short":
                pnl = (self.entry_price - price) * self.position_size
                side = "buy"
                print(f"📈 平空仓: {self.position_size:.2f}张 @ ${price:.2f}, PnL: ${pnl:.2f}")

            self.current_usdt += (1000 * self.leverage) + pnl # 回收本金和盈亏

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
        print(f"\n🚀 开始运行简化SAR策略")
        print(f"   交易对: {self.inst_id}")
        print(f"   杠杆: {self.leverage}x")
        print(f"   投资金额: {self.initial_usdt} USDT")
        print("按 Ctrl+C 停止策略")

        try:
            while True:
                # 获取市场数据
                data = self.get_market_data(self.inst_id, "15m", "100")
                if data is None or len(data) < 20:
                    print("❌ 无法获取市场数据")
                    time.sleep(60)
                    continue

                # 分析信号
                signal_info = self.analyze_signal(data)
                signal = signal_info['signal']

                if signal in ['buy', 'sell']:
                    print(f"\n📊 {datetime.now().strftime('%H:%M:%S')} - 价格: ${signal_info['price']:.2f}")
                    print(f"   信号: {signal} - {signal_info['reason']}")
                    print(f"   SAR: ${signal_info.get('sar', 0):.2f}")
                    print(f"   1小时趋势: {signal_info.get('hourly_signal', 'unknown')}")

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
                "name": "简化SAR策略",
                "kline_period": "15m",
                "af_start": self.af_start,
                "af_increment": self.af_increment,
                "af_maximum": self.af_maximum,
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
    strategy = SimpleSARStrategy()
    strategy.run()
