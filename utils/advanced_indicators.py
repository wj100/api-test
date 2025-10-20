"""
高级技术指标计算模块
基于pandas和numpy优化的技术指标实现
提供更多技术指标和优化算法
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class AdvancedIndicators:
    """高级技术指标计算类"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """简单移动平均线"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """指数移动平均线"""
        return data.ewm(span=period).mean()
    
    @staticmethod
    def wma(data: pd.Series, period: int) -> pd.Series:
        """加权移动平均线"""
        weights = np.arange(1, period + 1)
        return data.rolling(window=period).apply(lambda x: np.average(x, weights=weights), raw=True)
    
    @staticmethod
    def dema(data: pd.Series, period: int) -> pd.Series:
        """双重指数移动平均线"""
        ema1 = data.ewm(span=period).mean()
        ema2 = ema1.ewm(span=period).mean()
        return 2 * ema1 - ema2
    
    @staticmethod
    def tema(data: pd.Series, period: int) -> pd.Series:
        """三重指数移动平均线"""
        ema1 = data.ewm(span=period).mean()
        ema2 = ema1.ewm(span=period).mean()
        ema3 = ema2.ewm(span=period).mean()
        return 3 * ema1 - 3 * ema2 + ema3
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """相对强弱指标"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD指标"""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """布林带"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        
        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }
    
    @staticmethod
    def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20, multiplier: float = 2) -> Dict[str, pd.Series]:
        """肯特纳通道"""
        typical_price = (high + low + close) / 3
        middle = typical_price.rolling(window=period).mean()
        atr = AdvancedIndicators.atr(high, low, close, period)
        
        return {
            'upper': middle + (multiplier * atr),
            'middle': middle,
            'lower': middle - (multiplier * atr)
        }
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """平均真实波幅"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(window=period).mean()
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """随机指标"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """威廉指标"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        return -100 * ((highest_high - close) / (highest_high - lowest_low))
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """商品通道指数"""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
        return (typical_price - sma_tp) / (0.015 * mean_deviation)
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """平均方向指数"""
        # 计算方向移动
        high_diff = high.diff()
        low_diff = -low.diff()
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        plus_dm = pd.Series(plus_dm, index=high.index)
        minus_dm = pd.Series(minus_dm, index=high.index)
        
        # 计算真实波幅
        atr = AdvancedIndicators.atr(high, low, close, period)
        
        # 计算方向指标
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # 计算ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = pd.Series(dx, index=high.index).rolling(window=period).mean()
        
        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }
    
    @staticmethod
    def parabolic_sar(high: pd.Series, low: pd.Series, close: pd.Series, 
                     initial_af: float = 0.02, af_increment: float = 0.02, max_af: float = 0.2) -> pd.Series:
        """抛物线SAR"""
        length = len(high)
        sar = np.zeros(length)
        trend = np.zeros(length, dtype=int)
        af = np.zeros(length)
        ep = np.zeros(length)
        
        # 初始化
        sar[0] = low.iloc[0]
        trend[0] = 1
        af[0] = initial_af
        ep[0] = high.iloc[0]
        
        for i in range(1, length):
            if trend[i-1] == 1:  # 上升趋势
                sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
                if low.iloc[i] <= sar[i]:
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    af[i] = initial_af
                    ep[i] = low.iloc[i]
                else:
                    trend[i] = 1
                    if high.iloc[i] > ep[i-1]:
                        af[i] = min(af[i-1] + af_increment, max_af)
                        ep[i] = high.iloc[i]
                    else:
                        af[i] = af[i-1]
                        ep[i] = ep[i-1]
            else:  # 下降趋势
                sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
                if high.iloc[i] >= sar[i]:
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    af[i] = initial_af
                    ep[i] = high.iloc[i]
                else:
                    trend[i] = -1
                    if low.iloc[i] < ep[i-1]:
                        af[i] = min(af[i-1] + af_increment, max_af)
                        ep[i] = low.iloc[i]
                    else:
                        af[i] = af[i-1]
                        ep[i] = ep[i-1]
        
        return pd.Series(sar, index=high.index)
    
    @staticmethod
    def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series, 
                tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52) -> Dict[str, pd.Series]:
        """一目均衡表"""
        # 转换线
        tenkan_sen = (high.rolling(window=tenkan_period).max() + low.rolling(window=tenkan_period).min()) / 2
        
        # 基准线
        kijun_sen = (high.rolling(window=kijun_period).max() + low.rolling(window=kijun_period).min()) / 2
        
        # 先行带A
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
        
        # 先行带B
        senkou_span_b = ((high.rolling(window=senkou_b_period).max() + low.rolling(window=senkou_b_period).min()) / 2).shift(kijun_period)
        
        # 滞后线
        chikou_span = close.shift(-kijun_period)
        
        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }
    
    @staticmethod
    def fibonacci_retracement(high: pd.Series, low: pd.Series) -> Dict[str, float]:
        """斐波那契回撤"""
        max_price = high.max()
        min_price = low.min()
        diff = max_price - min_price
        
        return {
            '0%': max_price,
            '23.6%': max_price - 0.236 * diff,
            '38.2%': max_price - 0.382 * diff,
            '50%': max_price - 0.5 * diff,
            '61.8%': max_price - 0.618 * diff,
            '100%': min_price
        }
    
    @staticmethod
    def pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, float]:
        """枢轴点"""
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'pivot': pivot,
            'r1': r1,
            'r2': r2,
            'r3': r3,
            's1': s1,
            's2': s2,
            's3': s3
        }

# 便捷函数
def calculate_all_indicators(data: pd.DataFrame) -> Dict[str, Any]:
    """计算所有技术指标"""
    indicators = AdvancedIndicators()
    
    result = {}
    
    # 基础指标
    result['sma_20'] = indicators.sma(data['close'], 20)
    result['ema_20'] = indicators.ema(data['close'], 20)
    result['rsi'] = indicators.rsi(data['close'])
    
    # MACD
    macd_result = indicators.macd(data['close'])
    result.update(macd_result)
    
    # 布林带
    bb_result = indicators.bollinger_bands(data['close'])
    result.update(bb_result)
    
    # 随机指标
    stoch_result = indicators.stochastic(data['high'], data['low'], data['close'])
    result.update(stoch_result)
    
    # ATR
    result['atr'] = indicators.atr(data['high'], data['low'], data['close'])
    
    # ADX
    adx_result = indicators.adx(data['high'], data['low'], data['close'])
    result.update(adx_result)
    
    # 抛物线SAR
    result['sar'] = indicators.parabolic_sar(data['high'], data['low'], data['close'])
    
    return result
