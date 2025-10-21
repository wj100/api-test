# 简单技术指标库

这是一个轻量级的技术指标库，包含5个常用的技术分析指标。

## 包含指标

### 1. 抛物线SAR (Parabolic SAR)
- **文件**: `sar.py`
- **用途**: 判断趋势反转点
- **参数**: 
  - `af_start`: 初始加速因子 (默认0.02)
  - `af_increment`: 加速因子增量 (默认0.02)
  - `af_maximum`: 最大加速因子 (默认0.2)

### 2. 简单移动平均线 (SMA)
- **文件**: `sma.py`
- **用途**: 平滑价格数据，识别趋势
- **参数**: `period`: 周期

### 3. 指数移动平均线 (EMA)
- **文件**: `ema.py`
- **用途**: 对近期价格给予更高权重，反应更敏感
- **参数**: `period`: 周期

### 4. 相对强弱指数 (RSI)
- **文件**: `rsi.py`
- **用途**: 判断超买超卖状态
- **参数**: 
  - `period`: 周期 (默认14)
  - `overbought`: 超买阈值 (默认70)
  - `oversold`: 超卖阈值 (默认30)

### 5. MACD指标
- **文件**: `macd.py`
- **用途**: 判断趋势变化和买卖信号
- **参数**:
  - `fast_period`: 快线周期 (默认12)
  - `slow_period`: 慢线周期 (默认26)
  - `signal_period`: 信号线周期 (默认9)

## 使用方法

```python
from indicators import calculate_sar, calculate_sma, calculate_ema, calculate_rsi, calculate_macd

# 计算SAR指标
sar, trend = calculate_sar(high, low)

# 计算SMA指标
sma_20 = calculate_sma(prices, 20)

# 计算EMA指标
ema_12 = calculate_ema(prices, 12)

# 计算RSI指标
rsi = calculate_rsi(prices, 14)

# 计算MACD指标
macd_line, signal_line, histogram = calculate_macd(prices)
```

## 信号函数

每个指标都提供了对应的信号函数：

```python
from indicators.sar import get_sar_signal
from indicators.sma import get_sma_signal
from indicators.ema import get_ema_signal
from indicators.rsi import get_rsi_signal
from indicators.macd import get_macd_signal

# 获取交易信号
signal = get_sar_signal(sar_value, trend, current_price)
```

## 信号说明

- `'buy'`: 买入信号
- `'sell'`: 卖出信号
- `'hold'`: 持有/等待信号
