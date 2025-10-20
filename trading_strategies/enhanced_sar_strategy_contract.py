"""
增强版SAR策略 - 合约交易版本
支持2倍杠杆、真正做空、止盈止损
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from .base_strategy import BaseStrategy
from config import DEFAULT_INST_ID, DEFAULT_LEVERAGE
import time
import json
import os
from datetime import datetime

class EnhancedSARStrategyContract(BaseStrategy):
    """增强版SAR策略 - 合约交易版本"""

    def __init__(self, client, kline_period="15m", af_start=0.02, af_increment=0.02, af_maximum=0.2, 
                 take_profit_ratio=0.02, stop_loss_ratio=0.01, atr_period=14, volume_threshold=1.5,
                 initial_usdt=10000, leverage=2):
        super().__init__(client)
        self.kline_period = kline_period
        self.af_start = af_start
        self.af_increment = af_increment
        self.af_maximum = af_maximum
        self.take_profit_ratio = take_profit_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.atr_period = atr_period
        self.volume_threshold = volume_threshold
        self.inst_id = DEFAULT_INST_ID
        self.leverage = leverage
        self.initial_usdt = initial_usdt
        self.position = None
        self.entry_price = 0
        self.entry_sar = 0
        self.highest_profit = 0
        self.lowest_loss = 0
        self.position_size = 0  # 合约持仓数量
        
        # 交易记录
        self.trade_history = []
        self.start_time = datetime.now()
        self.start_balance = 0
        self.current_balance = 0
        
        print(f"🔧 增强版SAR策略参数 (合约交易):")
        print(f"   K线周期: {self.kline_period}")
        print(f"   初始加速因子: {self.af_start}")
        print(f"   加速因子增量: {self.af_increment}")
        print(f"   最大加速因子: {self.af_maximum}")
        print(f"   止盈比例: {self.take_profit_ratio:.1%}")
        print(f"   止损比例: {self.stop_loss_ratio:.1%}")
        print(f"   ATR周期: {self.atr_period}")
        print(f"   成交量阈值: {self.volume_threshold}x")
        print(f"   杠杆倍数: {self.leverage}x")
        print(f"   初始资金: ${self.initial_usdt:,.2f}")
        print(f"   交易对: {self.inst_id}")

    def set_leverage(self, leverage: int = 2):
        """设置杠杆倍数"""
        try:
            result = self.client.set_leverage(
                inst_id=self.inst_id,
                lever=str(leverage),
                mgn_mode="cross"  # 全仓模式
            )
            if result and result.get('code') == '0':
                self.leverage = leverage
                print(f"✅ 杠杆设置成功: {leverage}x")
                return True
            else:
                print(f"❌ 杠杆设置失败: {result}")
                return False
        except Exception as e:
            print(f"❌ 杠杆设置异常: {e}")
            return False

    def get_contract_balance(self) -> Dict[str, float]:
        """获取合约账户余额"""
        try:
            result = self.client.get_account_balance("SWAP")
            if result and result.get('code') == '0':
                details = result.get('data', [])
                balance_info = {}
                for detail in details:
                    ccy = detail.get('ccy', '')
                    if ccy in ['USDT', 'BTC']:
                        balance_info[ccy] = {
                            'available': float(detail.get('availBal', 0)),
                            'frozen': float(detail.get('frozenBal', 0)),
                            'total': float(detail.get('totalEq', 0))
                        }
                return balance_info
            else:
                print(f"⚠️ 获取合约余额失败，使用现货余额: {result}")
                # 使用现货账户余额作为默认值
                try:
                    spot_result = self.client.get_account_balance('USDT')
                    if spot_result and spot_result.get('code') == '0':
                        spot_details = spot_result['data'][0]['details']
                        for detail in spot_details:
                            if detail.get('ccy') == 'USDT':
                                spot_balance = float(detail.get('availBal', 0))
                                return {
                                    'USDT': {'available': spot_balance, 'frozen': 0, 'total': spot_balance},
                                    'BTC': {'available': 0, 'frozen': 0, 'total': 0}
                                }
                except:
                    pass
                # 如果现货余额也获取失败，使用默认值
                return {
                    'USDT': {'available': 10000, 'frozen': 0, 'total': 10000},
                    'BTC': {'available': 0, 'frozen': 0, 'total': 0}
                }
        except Exception as e:
            print(f"⚠️ 获取合约余额异常，使用现货余额: {e}")
            # 使用现货账户余额作为默认值
            try:
                spot_result = self.client.get_account_balance('USDT')
                if spot_result and spot_result.get('code') == '0':
                    spot_details = spot_result['data'][0]['details']
                    for detail in spot_details:
                        if detail.get('ccy') == 'USDT':
                            spot_balance = float(detail.get('availBal', 0))
                            return {
                                'USDT': {'available': spot_balance, 'frozen': 0, 'total': spot_balance},
                                'BTC': {'available': 0, 'frozen': 0, 'total': 0}
                            }
            except:
                pass
            # 如果现货余额也获取失败，使用默认值
            return {
                'USDT': {'available': 10000, 'frozen': 0, 'total': 10000},
                'BTC': {'available': 0, 'frozen': 0, 'total': 0}
            }

    def get_contract_positions(self) -> Dict[str, Any]:
        """获取合约持仓信息"""
        try:
            result = self.client.get_positions(self.inst_id)
            if result and result.get('code') == '0':
                positions = result.get('data', [])
                if positions:
                    pos = positions[0]
                    return {
                        'position_id': pos.get('posId', ''),
                        'position_side': pos.get('posSide', ''),
                        'position_size': float(pos.get('pos', 0)),
                        'average_price': float(pos.get('avgPx', 0)),
                        'unrealized_pnl': float(pos.get('upl', 0)),
                        'margin': float(pos.get('margin', 0))
                    }
                else:
                    # 没有持仓时返回默认值
                    return {
                        'position_id': '',
                        'position_side': '',
                        'position_size': 0,
                        'average_price': 0,
                        'unrealized_pnl': 0,
                        'margin': 0
                    }
            else:
                # 静默处理401错误，不打印错误信息
                return {
                    'position_id': '',
                    'position_side': '',
                    'position_size': 0,
                    'average_price': 0,
                    'unrealized_pnl': 0,
                    'margin': 0
                }
        except Exception as e:
            # 静默处理异常，不打印错误信息
            return {
                'position_id': '',
                'position_side': '',
                'position_size': 0,
                'average_price': 0,
                'unrealized_pnl': 0,
                'margin': 0
            }

    def calculate_sar(self, data: pd.DataFrame) -> pd.Series:
        """计算抛物线SAR指标"""
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        sar = np.zeros(len(data))
        af = self.af_start
        ep = low[0] if close[0] > low[0] else high[0]
        trend = 1 if close[0] > low[0] else -1
        
        for i in range(1, len(data)):
            if trend == 1:
                # 上升趋势
                sar[i] = sar[i-1] + af * (ep - sar[i-1])
                if sar[i] > low[i]:
                    sar[i] = low[i]
                if sar[i] > low[i-1]:
                    sar[i] = low[i-1]
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + self.af_increment, self.af_maximum)
                if low[i] <= sar[i]:
                    trend = -1
                    sar[i] = ep
                    ep = low[i]
                    af = self.af_start
            else:
                # 下降趋势
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

    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算ATR指标"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr

    def get_trend_filter(self, data: pd.DataFrame) -> str:
        """趋势过滤器：仅基于小时线趋势"""
        try:
            if len(data) < 20:
                return "neutral"
            
            # 获取小时线数据
            hourly_data = self.get_market_data(self.inst_id, "1H", "50")
            if hourly_data is None or len(hourly_data) < 20:
                return "neutral"
            
            # 计算小时线趋势
            hourly_ma20 = hourly_data['close'].rolling(window=20).mean()
            hourly_ma50 = hourly_data['close'].rolling(window=50).mean()
            hourly_price = hourly_data['close'].iloc[-1]
            hourly_ma20_val = hourly_ma20.iloc[-1]
            hourly_ma50_val = hourly_ma50.iloc[-1]
            
            # 判断小时线趋势
            if hourly_price > hourly_ma20_val > hourly_ma50_val:
                return "uptrend"
            elif hourly_price < hourly_ma20_val < hourly_ma50_val:
                return "downtrend"
            else:
                return "neutral"
        except Exception as e:
            print(f"趋势过滤器错误: {e}")
            return "neutral"

    def get_volatility_filter(self, data: pd.DataFrame) -> Tuple[bool, float]:
        """波动率过滤器：基于15分钟线ATR，降低阈值到0.8"""
        try:
            atr = self.calculate_atr(data, self.atr_period)
            current_atr = atr.iloc[-1]
            avg_atr = atr.rolling(window=20).mean().iloc[-1]
            
            volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1
            # 进一步降低波动率要求，适合15分钟线
            return volatility_ratio >= 0.8, volatility_ratio
        except Exception as e:
            print(f"波动率过滤器错误: {e}")
            return True, 1.0

    def get_volume_confirmation(self, data: pd.DataFrame) -> bool:
        """量价确认：已禁用成交量过滤器"""
        # 直接返回True，不进行成交量过滤
        return True

    def calculate_dynamic_stop_loss(self, current_price: float, current_sar: float, 
                                  atr: float) -> Tuple[float, str]:
        """计算动态止损：结合SAR和ATR"""
        try:
            atr_stop_long = current_price - atr * 2
            atr_stop_short = current_price + atr * 2
            sar_stop = current_sar
            
            if self.position == "long":
                dynamic_stop = max(sar_stop, atr_stop_long)
                return dynamic_stop, "long"
            elif self.position == "short":
                dynamic_stop = min(sar_stop, atr_stop_short)
                return dynamic_stop, "short"
            else:
                return current_price, "neutral"
        except Exception as e:
            print(f"动态止损计算错误: {e}")
            return current_price, "neutral"

    def analyze_signal(self, data: pd.DataFrame = None) -> Dict[str, Any]:
        """增强版信号分析 - 包含多重过滤器"""
        if data is None:
            data = self.get_market_data(self.inst_id, self.kline_period, '100')
            if data is None:
                return {"signal": "hold", "reason": "无法获取市场数据"}

        if len(data) < 30:
            return {"signal": "hold", "reason": "数据不足"}

        # 计算基础指标
        sar = self.calculate_sar(data)
        atr = self.calculate_atr(data, self.atr_period)
        current_price = data['close'].iloc[-1]
        current_sar = sar.iloc[-1]
        prev_sar = sar.iloc[-2]
        current_atr = atr.iloc[-1]

        # 1. 趋势过滤器
        daily_trend = self.get_trend_filter(data)
        
        # 2. 波动率过滤器
        is_volatile, volatility_ratio = self.get_volatility_filter(data)
        
        # 3. 量价确认
        volume_confirmed = self.get_volume_confirmation(data)
        
        # 4. 基础SAR信号
        sar_signal = None
        if current_price > current_sar and current_sar > prev_sar:
            sar_signal = "buy"
        elif current_price < current_sar and current_sar < prev_sar:
            sar_signal = "sell"

        # 5. 综合信号判断
        if sar_signal == "buy":
            if daily_trend == "downtrend":
                return {"signal": "hold", "reason": "日线趋势向下，过滤做多信号"}
            if not is_volatile:
                return {"signal": "hold", "reason": f"波动率过低 ({volatility_ratio:.2f})，过滤信号"}
            if not volume_confirmed:
                return {"signal": "hold", "reason": "成交量未放大，过滤信号"}
            if self.position != "long":
                return {
                    "signal": "buy",
                    "reason": f"SAR上升趋势+多重确认 ({self.kline_period})",
                    "price": current_price,
                    "sar": current_sar,
                    "trend": "上升",
                    "daily_trend": daily_trend,
                    "volatility": volatility_ratio,
                    "volume_confirmed": volume_confirmed
                }

        elif sar_signal == "sell":
            if daily_trend == "uptrend":
                return {"signal": "hold", "reason": "日线趋势向上，过滤做空信号"}
            if not is_volatile:
                return {"signal": "hold", "reason": f"波动率过低 ({volatility_ratio:.2f})，过滤信号"}
            if not volume_confirmed:
                return {"signal": "hold", "reason": "成交量未放大，过滤信号"}
            if self.position != "short":
                return {
                    "signal": "sell",
                    "reason": f"SAR下降趋势+多重确认 ({self.kline_period})",
                    "price": current_price,
                    "sar": current_sar,
                    "trend": "下降",
                    "daily_trend": daily_trend,
                    "volatility": volatility_ratio,
                    "volume_confirmed": volume_confirmed
                }

        # 6. 动态止损检查
        if self.position in ["long", "short"] and self.entry_price > 0:
            dynamic_stop, stop_type = self.calculate_dynamic_stop_loss(
                current_price, current_sar, current_atr
            )
            
            if self.position == "long":
                if current_price <= dynamic_stop:
                    return {
                        "signal": "sell",
                        "reason": f"动态止损触发 (SAR/ATR): {dynamic_stop:.2f}",
                        "price": current_price,
                        "stop_price": dynamic_stop,
                        "stop_type": stop_type
                    }
            elif self.position == "short":
                if current_price >= dynamic_stop:
                    return {
                        "signal": "buy",
                        "reason": f"动态止损触发 (SAR/ATR): {dynamic_stop:.2f}",
                        "price": current_price,
                        "stop_price": dynamic_stop,
                        "stop_type": stop_type
                    }

        return {"signal": "hold", "reason": "无明确信号或信号被过滤"}

    def execute_trade(self, signal: Dict[str, Any]) -> bool:
        """执行合约交易信号"""
        if signal["signal"] == "hold":
            return True

        try:
            # 获取合约账户信息
            balance_info = self.get_contract_balance()
            positions_info = self.get_contract_positions()
            current_price = signal["price"]

            if signal["signal"] == "buy":
                if self.position == "short":
                    # 平空仓：买入合约
                    if positions_info and positions_info['position_size'] < 0:
                        sz = str(abs(positions_info['position_size']))
                        # 计算限价单价格
                        limit_price = str(round(current_price * 1.001, 2))
                        result = self.client.place_futures_order(
                            inst_id=self.inst_id,
                            side="buy",
                            ord_type="limit",
                            sz=sz,
                            px=limit_price,
                            td_mode="cross",
                            pos_side="short"
                        )
                        
                        if result and result.get('code') == '0':
                            profit_rate = (self.entry_price - current_price) / self.entry_price
                            self.record_trade("buy_close", current_price, abs(positions_info['position_size']), profit_rate)
                            print(f"✅ 平空仓成功: {sz} 张合约 @ ${current_price}")
                            print(f"   收益率: {profit_rate:.2%}")
                            self.position = None
                            self.entry_price = 0
                            self.entry_sar = 0
                            self.position_size = 0
                            return True
                        else:
                            print(f"❌ 平空仓失败: {result}")
                            return False
                    else:
                        print(f"❌ 没有空仓持仓")
                        return False
                        
                elif self.position is None:
                    # 开多仓：买入合约
                    # 强制使用固定1000U，不依赖实际余额
                    usdt_balance = self.initial_usdt
                    if usdt_balance > 10:
                        # 计算合约数量 (使用杠杆)
                        amount = usdt_balance * 1.0 * self.leverage
                        # 计算合约数量，按实际资金计算
                        contract_size = amount / current_price
                        # 按步长0.1调整，确保符合交易所要求
                        contract_size = round(contract_size, 1)
                        if contract_size < 0.01:
                            contract_size = 0.01
                        sz = str(contract_size)
                        
                        # 计算限价单价格
                        limit_price = str(round(current_price * 1.001, 2))
                        result = self.client.place_futures_order(
                            inst_id=self.inst_id,
                            side="buy",
                            ord_type="limit",
                            sz=sz,
                            px=limit_price,
                            td_mode="cross",
                            pos_side="long"
                        )
                        
                        if result and result.get('code') == '0':
                            self.position = "long"
                            self.entry_price = current_price
                            self.entry_sar = signal.get('sar', current_price)
                            self.position_size = float(sz)
                            self.record_trade("buy_open", current_price, self.position_size, 0)
                            print(f"✅ 开多仓成功: {sz} 张合约 @ ${current_price}")
                            print(f"   杠杆: {self.leverage}x")
                            print(f"   入场SAR: ${self.entry_sar:.2f}")
                            return True
                        else:
                            print(f"❌ 开多仓失败: {result}")
                            return False
                    else:
                        print(f"❌ 资金不足，无法开多仓")
                        return False

            elif signal["signal"] == "sell":
                if self.position == "long":
                    # 平多仓：卖出合约
                    if positions_info and positions_info['position_size'] > 0:
                        sz = str(positions_info['position_size'])
                        # 计算限价单价格
                        limit_price = str(round(current_price * 0.999, 2))
                        result = self.client.place_futures_order(
                            inst_id=self.inst_id,
                            side="sell",
                            ord_type="limit",
                            sz=sz,
                            px=limit_price,
                            td_mode="cross",
                            pos_side="long"
                        )
                        
                        if result and result.get('code') == '0':
                            profit_rate = (current_price - self.entry_price) / self.entry_price
                            self.record_trade("sell_close", current_price, positions_info['position_size'], profit_rate)
                            print(f"✅ 平多仓成功: {sz} 张合约 @ ${current_price}")
                            print(f"   收益率: {profit_rate:.2%}")
                            self.position = None
                            self.entry_price = 0
                            self.entry_sar = 0
                            self.position_size = 0
                            return True
                        else:
                            print(f"❌ 平多仓失败: {result}")
                            return False
                    else:
                        print(f"❌ 没有多仓持仓")
                        return False
                        
                elif self.position is None:
                    # 开空仓：卖出合约
                    # 强制使用固定1000U，不依赖实际余额
                    usdt_balance = self.initial_usdt
                    if usdt_balance > 10:
                        # 计算合约数量 (使用杠杆)
                        amount = usdt_balance * 1.0 * self.leverage
                        # 计算合约数量，按实际资金计算
                        contract_size = amount / current_price
                        # 按步长0.1调整，确保符合交易所要求
                        contract_size = round(contract_size, 1)
                        if contract_size < 0.01:
                            contract_size = 0.01
                        sz = str(contract_size)
                        
                        # 计算限价单价格
                        limit_price = str(round(current_price * 0.999, 2))
                        result = self.client.place_futures_order(
                            inst_id=self.inst_id,
                            side="sell",
                            ord_type="limit",
                            sz=sz,
                            px=limit_price,
                            td_mode="cross",
                            pos_side="short"
                        )
                        
                        if result and result.get('code') == '0':
                            self.position = "short"
                            self.entry_price = current_price
                            self.entry_sar = signal.get('sar', current_price)
                            self.position_size = -float(sz)  # 负数表示空仓
                            self.record_trade("sell_open", current_price, self.position_size, 0)
                            print(f"✅ 开空仓成功: {sz} 张合约 @ ${current_price}")
                            print(f"   杠杆: {self.leverage}x")
                            print(f"   入场SAR: ${self.entry_sar:.2f}")
                            return True
                        else:
                            print(f"❌ 开空仓失败: {result}")
                            return False
                    else:
                        print(f"❌ 资金不足，无法开空仓")
                        return False
            else:
                print(f"当前信号: {signal['reason']}")
                return True

        except Exception as e:
            print(f"❌ 合约交易执行错误: {e}")
            return False

    def record_trade(self, side: str, price: float, amount: float, profit_rate: float):
        """记录交易"""
        trade = {
            "timestamp": datetime.now().isoformat(),
            "side": side,
            "price": price,
            "amount": amount,
            "profit_rate": profit_rate,
            "position": self.position,
            "entry_price": self.entry_price,
            "leverage": self.leverage
        }
        self.trade_history.append(trade)

    def get_current_balance(self) -> float:
        """获取当前合约账户总余额"""
        try:
            balance_info = self.get_contract_balance()
            positions_info = self.get_contract_positions()
            
            # 基础余额
            usdt_balance = balance_info.get('USDT', {}).get('total', 0)
            
            # 未实现盈亏
            unrealized_pnl = positions_info.get('unrealized_pnl', 0)
            
            return usdt_balance + unrealized_pnl
        except Exception as e:
            print(f"获取合约余额错误: {e}")
            return 0

    def generate_report(self) -> Dict[str, Any]:
        """生成策略运行报告"""
        end_time = datetime.now()
        current_balance = self.get_current_balance()
        
        # 计算收益率
        total_return = (current_balance - self.initial_usdt) / self.initial_usdt if self.initial_usdt > 0 else 0
        
        # 计算运行时间
        runtime = end_time - self.start_time
        
        # 统计交易
        total_trades = len(self.trade_history)
        winning_trades = len([t for t in self.trade_history if t['profit_rate'] > 0])
        losing_trades = len([t for t in self.trade_history if t['profit_rate'] < 0])
        
        report = {
            "strategy_info": {
                "name": "增强版SAR策略 (合约交易)",
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
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "runtime_hours": runtime.total_seconds() / 3600,
                "initial_balance": self.initial_usdt,
                "final_balance": current_balance,
                "total_return": total_return,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
                "current_position": self.position,
                "position_size": self.position_size,
                "entry_price": self.entry_price,
                "leverage_used": self.leverage
            },
            "trade_history": self.trade_history
        }
        
        return report
