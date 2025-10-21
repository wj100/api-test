"""
抛物线SAR指标 (Parabolic SAR)
用于判断趋势反转点
"""

import numpy as np

def calculate_sar(high, low, af_start=0.02, af_increment=0.02, af_maximum=0.2):
    """
    计算抛物线SAR指标
    
    参数:
        high: 最高价数组
        low: 最低价数组
        af_start: 初始加速因子 (默认0.02)
        af_increment: 加速因子增量 (默认0.02)
        af_maximum: 最大加速因子 (默认0.2)
    
    返回:
        sar: SAR值数组
        trend: 趋势数组 (1=上升, -1=下降)
    """
    high = np.array(high, dtype=float)
    low = np.array(low, dtype=float)
    n = len(high)
    
    sar = np.zeros(n)
    trend = np.zeros(n, dtype=int)
    
    # 初始化
    sar[0] = low[0]
    trend[0] = 1  # 1表示上升趋势，-1表示下降趋势
    ep = high[0]  # 极值点
    af = af_start
    
    for i in range(1, n):
        if trend[i-1] == 1:  # 上升趋势
            sar[i] = sar[i-1] + af * (ep - sar[i-1])
            # SAR不能高于当前K线的最低价
            if sar[i] > low[i]:
                sar[i] = low[i]
            # 更新极值点和加速因子
            if high[i] > ep:
                ep = high[i]
                af = min(af + af_increment, af_maximum)
            # 检查趋势反转
            if low[i] < sar[i]:
                trend[i] = -1
                sar[i] = ep  # 新SAR点为前一个EP
                ep = low[i]  # 新EP为当前K线最低价
                af = af_start
            else:
                trend[i] = 1
        else:  # 下降趋势
            sar[i] = sar[i-1] + af * (ep - sar[i-1])
            # SAR不能低于当前K线的最高价
            if sar[i] < high[i]:
                sar[i] = high[i]
            # 更新极值点和加速因子
            if low[i] < ep:
                ep = low[i]
                af = min(af + af_increment, af_maximum)
            # 检查趋势反转
            if high[i] > sar[i]:
                trend[i] = 1
                sar[i] = ep  # 新SAR点为前一个EP
                ep = high[i]  # 新EP为当前K线最高价
                af = af_start
            else:
                trend[i] = -1
    
    return sar, trend

def get_sar_signal(sar, trend, price):
    """
    获取SAR交易信号
    
    参数:
        sar: 当前SAR值
        trend: 当前趋势 (1=上升, -1=下降)
        price: 当前价格
    
    返回:
        signal: 交易信号 ('buy', 'sell', 'hold')
    """
    if trend == 1 and price > sar:
        return 'buy'
    elif trend == -1 and price < sar:
        return 'sell'
    else:
        return 'hold'
