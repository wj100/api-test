'''
Author: 汪骏
Date: 2025-10-19 14:57:00
LastEditors: wangjun
LastEditTime: 2025-10-20 10:50:17
Description: 请填写简介
'''
'''
Author: 汪骏
Date: 2025-10-19 14:57:00
LastEditors: wangjun
LastEditTime: 2025-10-19 15:04:34
Description: 请填写简介
'''
"""
OKX API配置
基于官方文档: https://www.okx.com/zh-hans/help/how-can-i-do-spot-trading-with-the-jupyter-notebook
"""
import os

# ==================== 交易模式配置 ====================
# 通过修改这个参数来切换交易模式
# True = 模拟交易, False = 实盘交易
USE_DEMO_TRADING = True

# ==================== 实盘交易配置 ====================
LIVE_API_KEY = "a9ff9f08-39bb-4f22-9524-ff30de7b1473"
LIVE_SECRET_KEY = "757CD71958675B4A2981F76C97480A51"
LIVE_PASSPHRASE = "Capf@0804"

# ==================== 模拟交易配置 ====================
DEMO_API_KEY = "81de265c-97d0-4ead-8590-15ca171e63d4"
DEMO_SECRET_KEY = "F66740056DD81B3241A7971406C48588"
DEMO_PASSPHRASE = "Capf@0804"

# ==================== 自动选择配置 ====================
if USE_DEMO_TRADING:
    # 模拟交易配置
    API_KEY = DEMO_API_KEY
    SECRET_KEY = DEMO_SECRET_KEY
    PASSPHRASE = DEMO_PASSPHRASE
    FLAG = "1"  # 模拟模式
    TRADING_MODE = "模拟交易"
else:
    # 实盘交易配置
    API_KEY = LIVE_API_KEY
    SECRET_KEY = LIVE_SECRET_KEY
    PASSPHRASE = LIVE_PASSPHRASE
    FLAG = "0"  # 实盘模式
    TRADING_MODE = "实盘交易"

# 交易配置
DEFAULT_INST_ID = "BTC-USDT-SWAP"
DEFAULT_INST_TYPE = "SWAP"
DEFAULT_LEVERAGE = 10  # 默认10倍杠杆

# 风险控制
MAX_POSITION_RATIO = 0.8  # 最大仓位比例
MAX_DAILY_LOSS = 0.05     # 最大日亏损比例
MAX_ORDER_AMOUNT = 1000   # 最大单笔订单金额(USDT)

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "trading.log"