"""
MACD指标 (Moving Average Convergence Divergence)
用于判断趋势变化和买卖信号
"""

import numpy as np

def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
    """
    计算MACD指标
    
    参数:
        prices: 价格数组
        fast_period: 快线周期 (默认12)
        slow_period: 慢线周期 (默认26)
        signal_period: 信号线周期 (默认9)
    
    返回:
        macd_line: MACD线
        signal_line: 信号线
        histogram: 柱状图
    """
    prices = np.array(prices, dtype=float)
    n = len(prices)
    
    # 计算快线和慢线EMA
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)
    
    # 计算MACD线
    macd_line = fast_ema - slow_ema
    
    # 计算信号线 (MACD的EMA)
    # 找到第一个非NaN的MACD值
    valid_start = slow_period - 1
    valid_macd = macd_line[valid_start:]
    
    # 计算信号线
    signal_line = calculate_ema(valid_macd, signal_period)
    
    # 对齐长度
    signal_line_full = np.full(n, np.nan)
    signal_start = valid_start + signal_period - 1
    
    # 确保长度匹配
    available_length = len(signal_line)
    target_length = n - signal_start
    if available_length > target_length:
        signal_line = signal_line[:target_length]
    elif available_length < target_length:
        # 如果信号线长度不足，用NaN填充
        signal_line = np.concatenate([signal_line, np.full(target_length - available_length, np.nan)])
    
    signal_line_full[signal_start:] = signal_line
    
    # 计算柱状图
    histogram = macd_line - signal_line_full
    
    return macd_line, signal_line_full, histogram

def calculate_ema(prices, period):
    """计算EMA的辅助函数"""
    prices = np.array(prices, dtype=float)
    n = len(prices)
    ema = np.full(n, np.nan)
    
    multiplier = 2 / (period + 1)
    ema[period - 1] = np.mean(prices[:period])
    
    for i in range(period, n):
        ema[i] = (prices[i] * multiplier) + (ema[i - 1] * (1 - multiplier))
    
    return ema

def get_macd_signal(macd_line, signal_line, histogram):
    """
    获取MACD交易信号
    
    参数:
        macd_line: MACD线值
        signal_line: 信号线值
        histogram: 柱状图值
    
    返回:
        signal: 交易信号 ('buy', 'sell', 'hold')
    """
    if np.isnan(macd_line) or np.isnan(signal_line) or np.isnan(histogram):
        return 'hold'
    
    # MACD线在信号线上方且柱状图为正
    if macd_line > signal_line and histogram > 0:
        return 'buy'
    # MACD线在信号线下方且柱状图为负
    elif macd_line < signal_line and histogram < 0:
        return 'sell'
    else:
        return 'hold'
