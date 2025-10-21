"""
优化版SAR策略
基于base_strategy.py的优化SAR信号策略
"""

import pandas as pd
import numpy as np
import math
import time
from datetime import datetime
from typing import Dict, Any, Optional
from .base_strategy import BaseStrategy
from indicators import calculate_sar
from indicators.sar import get_sar_signal

class OptimizedSARStrategy(BaseStrategy):
    """优化版SAR策略"""
    
    def __init__(self, client, inst_id: str = "BTC-USDT-SWAP", inst_type: str = "SWAP"):
        super().__init__(client, inst_id, inst_type)
        
        # SAR参数优化
        self.sar_af = 0.015  # 加速因子（从0.02降低）
        self.sar_max_af = 0.15  # 最大加速因子（从0.2降低）
        self.sar_initial = 0.015  # 初始加速因子（从0.02降低）
        
        # 止损止盈优化
        self.tp_ratio = 2.5  # 止盈比例
        self.sl_ratio = 0.8   # 止损比例
        
        # 风控参数
        self.max_consecutive_losses = 4  # 最大连续亏损次数
        self.consecutive_losses = 0      # 当前连续亏损次数
        self.last_trade_time = None      # 上次交易时间
        self.min_trade_interval = 0.5    # 最小交易间隔(小时)
        
        # 趋势过滤参数
        self.trend_period = 20  # 趋势判断周期
        self.min_trend_strength = 1.1  # 最小趋势强度
        
        print(f"🚀 初始化优化版SAR策略")
        print(f"   SAR参数: AF={self.sar_af}, MaxAF={self.sar_max_af}")
        print(f"   止损止盈: {self.sl_ratio}%/{self.tp_ratio}%")
        print(f"   趋势过滤: {self.trend_period}周期, 强度{self.min_trend_strength}")
    
    def calculate_atr(self, df, period=14):
        """计算真实波动率ATR"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        n = len(df)
        tr = np.zeros(n)
        
        for i in range(1, n):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
        
        # 计算ATR
        atr = np.full(n, np.nan)
        for i in range(period, n):
            atr[i] = np.mean(tr[i-period+1:i+1])
        
        return atr
    
    def get_trend_filter(self, df):
        """简单趋势过滤"""
        try:
            if len(df) < self.trend_period:
                return True, 1.0
            
            # 计算SMA趋势
            sma_short = df['close'].rolling(window=10).mean()
            sma_long = df['close'].rolling(window=self.trend_period).mean()
            
            if len(sma_short) == 0 or len(sma_long) == 0:
                return True, 1.0
            
            current_price = df['close'].iloc[-1]
            sma_short_val = sma_short.iloc[-1]
            sma_long_val = sma_long.iloc[-1]
            
            if pd.isna(sma_short_val) or pd.isna(sma_long_val):
                return True, 1.0
            
            # 趋势强度计算
            if sma_long_val > 0:
                trend_strength = abs(sma_short_val - sma_long_val) / sma_long_val
            else:
                trend_strength = 1.0
            
            # 趋势方向
            if sma_short_val > sma_long_val:
                trend_direction = 1  # 上升趋势
            elif sma_short_val < sma_long_val:
                trend_direction = -1  # 下降趋势
            else:
                trend_direction = 0  # 横盘
            
            return trend_strength >= self.min_trend_strength, trend_direction
            
        except Exception as e:
            print(f"❌ 趋势过滤失败: {e}")
            return True, 0
    
    def analyze_signal(self) -> Dict[str, Any]:
        """分析交易信号"""
        try:
            # 获取市场数据
            df = self.get_market_data(bar='15m', limit='100')
            if df is None or len(df) < 50:
                return {'signal': 'hold', 'reason': 'insufficient_data'}
            
            # 计算SAR指标
            sar, trend = calculate_sar(df['high'].values, df['low'].values, 
                                     self.sar_initial, self.sar_af, self.sar_max_af)
            
            current_price = df['close'].iloc[-1]
            
            # 1. 连续亏损控制
            if self.consecutive_losses >= self.max_consecutive_losses:
                return {'signal': 'hold', 'reason': 'max_consecutive_losses'}
            
            # 2. 交易间隔控制
            if self.last_trade_time:
                time_diff = (datetime.now() - self.last_trade_time).total_seconds() / 3600
                if time_diff < self.min_trade_interval:
                    return {'signal': 'hold', 'reason': 'trade_interval'}
            
            # 3. 趋势过滤
            trend_ok, trend_direction = self.get_trend_filter(df)
            if not trend_ok:
                return {'signal': 'hold', 'reason': 'weak_trend'}
            
            # 4. SAR信号
            sar_signal = get_sar_signal(sar[-1], trend[-1], current_price)
            
            # 5. 波动率过滤
            atr = self.calculate_atr(df)
            if len(atr) > 0 and not np.isnan(atr[-1]):
                volatility_ok = atr[-1] > (current_price * 0.003)  # 最小波动率0.3%
            else:
                volatility_ok = True
            
            if not volatility_ok:
                return {'signal': 'hold', 'reason': 'low_volatility'}
            
            # 6. 趋势方向确认
            if sar_signal == 'buy' and trend_direction >= 0:
                return {
                    'signal': 'buy',
                    'reason': 'sar_signal_trend_up',
                    'price': current_price,
                    'sar': sar[-1],
                    'trend': trend[-1],
                    'trend_direction': trend_direction
                }
            elif sar_signal == 'sell' and trend_direction <= 0:
                return {
                    'signal': 'sell',
                    'reason': 'sar_signal_trend_down',
                    'price': current_price,
                    'sar': sar[-1],
                    'trend': trend[-1],
                    'trend_direction': trend_direction
                }
            else:
                return {'signal': 'hold', 'reason': 'trend_conflict'}
                
        except Exception as e:
            print(f"❌ 信号分析失败: {e}")
            return {'signal': 'hold', 'reason': 'error'}
    
    def execute_trade(self, signal: Dict[str, Any]):
        """执行交易"""
        try:
            signal_type = signal.get('signal')
            reason = signal.get('reason')
            current_price = signal.get('price', 0)
            
            print(f"📊 信号分析: {signal_type} - {reason}")
            
            if signal_type == 'hold':
                return
            
            # 检查是否已有持仓
            if self.position is not None:
                print("⚠️ 已有持仓，跳过开仓")
                return
            
            # 计算仓位大小
            usdt_balance = 1000  # 固定使用1000 USDT
            position_size = self.calculate_position_size(current_price, usdt_balance)
            
            if position_size < 0.01:
                print("⚠️ 仓位太小，跳过交易")
                return
            
            # 执行开仓
            side = "buy" if signal_type == 'buy' else "sell"
            sz = str(position_size)
            
            # 使用合约交易API
            result = self.client.place_futures_order(
                inst_id=self.inst_id,
                side=side,
                pos_side="long" if side == "buy" else "short",
                ord_type="market",
                sz=sz
            )
            
            if result and result.get('code') == '0':
                print(f"✅ 开仓成功: {side} {sz} {self.inst_id}")
                
                # 记录持仓信息
                self.position = {
                    'side': side,
                    'size': position_size,
                    'entry_price': current_price,
                    'timestamp': datetime.now()
                }
                self.entry_price = current_price
                self.take_profit_ratio = self.tp_ratio
                self.stop_loss_ratio = self.sl_ratio
                self.last_trade_time = datetime.now()
                
                # 设置止损止盈
                self.set_stop_loss_take_profit(current_price, side)
                
            else:
                print(f"❌ 开仓失败: {result}")
                
        except Exception as e:
            print(f"❌ 交易执行失败: {e}")
    
    def calculate_position_size(self, current_price: float, usdt_balance: float) -> float:
        """计算仓位大小"""
        try:
            # 基础风险金额
            base_risk_amount = usdt_balance * 0.01  # 1%风险
            
            # 连续亏损调整
            loss_adjustment = max(0.6, 1 - (self.consecutive_losses * 0.15))
            adjusted_risk_ratio = 0.01 * loss_adjustment
            
            # 计算仓位
            risk_amount = usdt_balance * adjusted_risk_ratio
            base_size = risk_amount / current_price
            
            # 获取合约规格
            instrument_info = self.client.get_instruments("SWAP")
            ct_val = 0.01
            lot_sz = 0.01
            
            if instrument_info and instrument_info.get('code') == '0':
                for inst in instrument_info['data']:
                    if inst['instId'] == self.inst_id:
                        ct_val = float(inst['ctVal'])
                        lot_sz = float(inst['lotSz'])
                        break
            
            # 计算合约张数
            target_btc_amount = base_size
            sz_float = target_btc_amount / ct_val
            sz = math.ceil(sz_float / lot_sz) * lot_sz
            
            return max(0.01, sz)
            
        except Exception as e:
            print(f"❌ 计算仓位失败: {e}")
            return 0.01
    
    def set_stop_loss_take_profit(self, entry_price: float, side: str):
        """设置止损止盈"""
        try:
            if side == "buy":
                stop_loss_price = entry_price * (1 - self.sl_ratio / 100)
                take_profit_price = entry_price * (1 + self.tp_ratio / 100)
            else:
                stop_loss_price = entry_price * (1 + self.sl_ratio / 100)
                take_profit_price = entry_price * (1 - self.tp_ratio / 100)
            
            print(f"📊 止损止盈设置:")
            print(f"   止损: ${stop_loss_price:,.2f}")
            print(f"   止盈: ${take_profit_price:,.2f}")
            
            # 这里可以添加实际的止损止盈订单设置
            # 由于OKX API限制，这里只是记录价格
            
        except Exception as e:
            print(f"❌ 设置止损止盈失败: {e}")
    
    def check_exit_conditions(self, current_price: float) -> Optional[str]:
        """检查平仓条件"""
        if not self.position:
            return None
        
        side = self.position['side']
        entry_price = self.position['entry_price']
        
        # 计算止损止盈价格
        if side == "buy":
            stop_loss_price = entry_price * (1 - self.sl_ratio / 100)
            take_profit_price = entry_price * (1 + self.tp_ratio / 100)
        else:
            stop_loss_price = entry_price * (1 + self.sl_ratio / 100)
            take_profit_price = entry_price * (1 - self.tp_ratio / 100)
        
        # 检查止损止盈
        if side == "buy":
            if current_price <= stop_loss_price:
                return 'stop_loss'
            elif current_price >= take_profit_price:
                return 'take_profit'
        else:  # sell
            if current_price >= stop_loss_price:
                return 'stop_loss'
            elif current_price <= take_profit_price:
                return 'take_profit'
        
        return None
    
    def close_position(self, reason: str = 'manual'):
        """平仓"""
        try:
            if not self.position:
                return
            
            side = self.position['side']
            size = self.position['size']
            
            # 执行平仓
            close_side = "sell" if side == "buy" else "buy"
            sz = str(size)
            
            result = self.client.place_futures_order(
                inst_id=self.inst_id,
                side=close_side,
                pos_side="long" if close_side == "sell" else "short",
                ord_type="market",
                sz=sz
            )
            
            if result and result.get('code') == '0':
                print(f"✅ 平仓成功: {close_side} {sz} {self.inst_id} - {reason}")
                
                # 更新连续亏损计数
                if reason in ['stop_loss']:
                    self.consecutive_losses += 1
                else:
                    self.consecutive_losses = 0
                
                # 清除持仓信息
                self.position = None
                self.entry_price = 0.0
                self.take_profit_ratio = 0.0
                self.stop_loss_ratio = 0.0
                
            else:
                print(f"❌ 平仓失败: {result}")
                
        except Exception as e:
            print(f"❌ 平仓失败: {e}")
    
    def run(self):
        """运行策略"""
        print(f"\n开始运行优化版SAR策略...")
        print("按 Ctrl+C 停止")
        try:
            while True:
                # 检查平仓条件
                if self.position:
                    df = self.get_market_data(bar='15m', limit='1')
                    if df is not None and len(df) > 0:
                        current_price = df['close'].iloc[-1]
                        exit_reason = self.check_exit_conditions(current_price)
                        if exit_reason:
                            self.close_position(exit_reason)
                            continue
                
                # 分析信号
                signal = self.analyze_signal()
                print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 信号分析: {signal}")
                
                # 执行交易
                self.execute_trade(signal)
                
                print("等待15分钟后进行下次分析...")
                time.sleep(900)  # 每15分钟运行一次
                
        except KeyboardInterrupt:
            print(f"\n收到停止信号，正在退出优化版SAR策略...")
        except Exception as e:
            print(f"策略运行错误: {e}")
