# 测试文件说明

## 📁 测试文件

### 基础测试
- `test_http.py` - HTTP客户端API测试
- `simple_test.py` - 简单功能测试

### 账户测试
- `check_balance.py` - 检查账户余额
- `check_demo_balance.py` - 检查模拟账户余额
- `fund_demo_account.py` - 模拟账户充值

### 策略测试
- `test_sar_strategy.py` - SAR策略测试

### 合约交易测试
- `open_btc_short.py` - 开BTC 10倍空单测试
- `open_btc_long.py` - 开BTC 5倍多单测试
- `close_btc_position.py` - 平仓测试（手动输入）
- `close_all_positions.py` - 全平所有仓位测试

## 🚀 运行测试

### 基础功能测试
```bash
# 测试HTTP客户端
python3 tests/test_http.py

# 检查账户余额
python3 tests/check_balance.py

# 测试SAR策略
python3 tests/test_sar_strategy.py
```

### 合约交易测试
```bash
# 开10倍空单
python3 tests/open_btc_short.py

# 开5倍多单
python3 tests/open_btc_long.py

# 平仓（手动输入数量）
python3 tests/close_btc_position.py

# 全平所有仓位
python3 tests/close_all_positions.py
```

## 📊 测试功能说明

### 合约交易测试
- **开空单**: 支持10倍杠杆做空，自动计算合约数量
- **开多单**: 支持5倍杠杆做多，自动计算合约数量
- **平仓**: 支持手动输入平仓数量
- **全平**: 自动尝试平多仓和空仓，无需输入

### 技术特点
- 使用`place_futures_order` API进行合约交易
- 自动计算限价单价格确保成交
- 支持BTC-USDT-SWAP合约交易对
- 合约数量符合最小要求（0.01张，步长0.1）

## ⚠️ 注意事项

- 测试前请确保API配置正确
- 建议先在模拟环境测试
- 合约交易测试会执行真实交易操作
- 注意风险控制，杠杆交易风险较高