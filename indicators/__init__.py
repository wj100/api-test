"""
简单技术指标库
包含5个常用技术指标：SAR、SMA、EMA、RSI、MACD
"""

from .sar import calculate_sar
from .sma import calculate_sma
from .ema import calculate_ema
from .rsi import calculate_rsi
from .macd import calculate_macd

__version__ = "1.0.0"
__author__ = "OKX Trading Bot"

__all__ = [
    'calculate_sar',
    'calculate_sma', 
    'calculate_ema',
    'calculate_rsi',
    'calculate_macd'
]
