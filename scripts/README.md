# 工具脚本说明

## 📁 脚本文件

### 诊断工具
- `diagnose_passphrase.py` - 诊断API密码问题

### 交易工具
- `sell_eth.py` - 交互式卖出ETH
- `sell_eth_auto.py` - 自动卖出所有ETH
- `sell_all_coins.py` - 卖出所有非USDT币种

## 🚀 使用方法

```bash
# 诊断API问题
python3 scripts/diagnose_passphrase.py

# 卖出ETH (交互式)
python3 scripts/sell_eth.py

# 自动卖出所有ETH
python3 scripts/sell_eth_auto.py

# 卖出所有非USDT币种
python3 scripts/sell_all_coins.py
```

## ⚠️ 注意事项

- 交易脚本会执行真实交易
- 请谨慎使用，建议先小金额测试
- 确保在正确的交易模式下运行