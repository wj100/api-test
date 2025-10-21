"""
相对强弱指数 (Relative Strength Index, RSI)
用于判断超买超卖状态，范围0-100
"""

import numpy as np

def calculate_rsi(prices, period=14):
    """
    计算相对强弱指数
    
    参数:
        prices: 价格数组
        period: 周期 (默认14)
    
    返回:
        rsi: RSI值数组
    """
    prices = np.array(prices, dtype=float)
    n = len(prices)
    rsi = np.full(n, np.nan)
    
    # 计算价格变化
    deltas = np.diff(prices)
    
    # 分离上涨和下跌
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # 计算初始平均收益和损失
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    if avg_loss == 0:
        rsi[period] = 100
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100 - (100 / (1 + rs))
    
    # 计算后续RSI值
    for i in range(period + 1, n):
        # 使用平滑移动平均
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        
        if avg_loss == 0:
            rsi[i] = 100
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100 - (100 / (1 + rs))
    
    return rsi

def get_rsi_signal(rsi, overbought=70, oversold=30):
    """
    获取RSI交易信号
    
    参数:
        rsi: 当前RSI值
        overbought: 超买阈值 (默认70)
        oversold: 超卖阈值 (默认30)
    
    返回:
        signal: 交易信号 ('buy', 'sell', 'hold')
    """
    if np.isnan(rsi):
        return 'hold'
    
    if rsi < oversold:
        return 'buy'
    elif rsi > overbought:
        return 'sell'
    else:
        return 'hold'
