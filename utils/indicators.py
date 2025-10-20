"""
技术指标计算
"""
import pandas as pd
import numpy as np
from typing import Dict

def calculate_ma(data: pd.DataFrame, period: int) -> pd.Series:
    """计算移动平均线"""
    return data['close'].rolling(window=period).mean()

def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
    """计算指数移动平均线"""
    return data['close'].ewm(span=period).mean()

def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算RSI指标"""
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """计算MACD指标"""
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
    """计算布林带"""
    ma = calculate_ma(data, period)
    std = data['close'].rolling(window=period).std()
    
    return {
        'upper': ma + (std * std_dev),
        'middle': ma,
        'lower': ma - (std * std_dev)
    }

def calculate_stochastic(data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
    """计算随机指标"""
    low_min = data['low'].rolling(window=k_period).min()
    high_max = data['high'].rolling(window=k_period).max()
    
    k_percent = 100 * ((data['close'] - low_min) / (high_max - low_min))
    d_percent = k_percent.rolling(window=d_period).mean()
    
    return {
        'k': k_percent,
        'd': d_percent
    }

def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算平均真实波幅"""
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = true_range.rolling(window=period).mean()
    
    return atr
