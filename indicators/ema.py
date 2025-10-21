"""
指数移动平均线 (Exponential Moving Average, EMA)
对近期价格给予更高权重，反应更敏感
"""

import numpy as np

def calculate_ema(prices, period):
    """
    计算指数移动平均线
    
    参数:
        prices: 价格数组
        period: 周期
    
    返回:
        ema: EMA值数组
    """
    prices = np.array(prices, dtype=float)
    n = len(prices)
    ema = np.full(n, np.nan)
    
    # 计算平滑因子
    multiplier = 2 / (period + 1)
    
    # 第一个EMA值使用SMA
    ema[period - 1] = np.mean(prices[:period])
    
    # 计算后续EMA值
    for i in range(period, n):
        ema[i] = (prices[i] * multiplier) + (ema[i - 1] * (1 - multiplier))
    
    return ema

def get_ema_signal(price, ema_short, ema_long):
    """
    获取EMA交叉信号
    
    参数:
        price: 当前价格
        ema_short: 短期EMA值
        ema_long: 长期EMA值
    
    返回:
        signal: 交易信号 ('buy', 'sell', 'hold')
    """
    if np.isnan(ema_short) or np.isnan(ema_long):
        return 'hold'
    
    if ema_short > ema_long:
        return 'buy'
    elif ema_short < ema_long:
        return 'sell'
    else:
        return 'hold'
