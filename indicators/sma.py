"""
简单移动平均线 (Simple Moving Average, SMA)
用于平滑价格数据，识别趋势
"""

import numpy as np

def calculate_sma(prices, period):
    """
    计算简单移动平均线
    
    参数:
        prices: 价格数组
        period: 周期
    
    返回:
        sma: SMA值数组
    """
    prices = np.array(prices, dtype=float)
    n = len(prices)
    sma = np.full(n, np.nan)
    
    for i in range(period - 1, n):
        sma[i] = np.mean(prices[i - period + 1:i + 1])
    
    return sma

def get_sma_signal(price, sma_short, sma_long):
    """
    获取SMA交叉信号
    
    参数:
        price: 当前价格
        sma_short: 短期SMA值
        sma_long: 长期SMA值
    
    返回:
        signal: 交易信号 ('buy', 'sell', 'hold')
    """
    if np.isnan(sma_short) or np.isnan(sma_long):
        return 'hold'
    
    if sma_short > sma_long:
        return 'buy'
    elif sma_short < sma_long:
        return 'sell'
    else:
        return 'hold'
