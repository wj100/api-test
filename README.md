# OKX 增强版SAR策略 (合约交易版本)

这是一个基于OKX API的增强版SAR策略，支持合约交易、2倍杠杆和真正做空功能。

## 🚀 功能特性

### ✅ 核心功能
- **合约交易**: 使用BTC-USDT-SWAP合约交易对
- **真正做空**: 支持开空仓和平空仓操作
- **杠杆交易**: 默认2倍杠杆，可自定义1-10倍
- **止盈止损**: 完整的止盈止损机制
- **用户输入**: 运行时输入投入的USDT金额
- **手动停止**: 按Ctrl+C手动停止策略
- **结果记录**: 自动生成详细的运行报告

### 📊 策略参数
- **K线周期**: 15m, 1H, 4H, 1D
- **加速因子**: 初始值、增量、最大值
- **止盈止损**: 可自定义比例
- **ATR周期**: 波动率计算周期
- **成交量阈值**: 成交量放大倍数
- **杠杆倍数**: 1-10倍可调

## 🎯 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API密钥
```bash
cp env.example .env
# 编辑 .env 文件，填入您的API密钥
```

### 3. 启动合约策略
```bash
python3 start_contract_strategy.py
```

### 4. 输入参数
- 投入的USDT金额
- 杠杆倍数 (默认2倍)
- 策略参数 (可选，有默认值)

## 📁 项目结构

```
├── trading_strategies/
│   ├── base_strategy.py                    # 基础策略类
│   └── enhanced_sar_strategy_contract.py   # 合约交易策略
├── utils/                                  # 工具函数
│   ├── indicators.py                      # 技术指标
│   └── advanced_indicators.py             # 高级指标
├── tests/                                  # 测试文件
├── scripts/                                # 脚本文件
├── config.py                              # 配置文件
├── okx_http_client.py                     # OKX HTTP客户端
├── start_contract_strategy.py              # 合约策略启动器
├── run_enhanced_sar_contract.py            # 合约策略运行器
└── CONTRACT_STRATEGY_USAGE.md             # 使用说明
```

## 📊 结果文件

运行结束后，会在 `contract_strategy_results/` 文件夹中生成：

```
contract_strategy_results/
├── contract_strategy_report_20241020_143022.json    # 详细JSON报告
└── contract_strategy_summary_20241020_143022.txt     # 文本摘要报告
```

## ⚠️ 注意事项

### 交易模式
- 当前使用**模拟交易**模式
- 如需实盘交易，请修改 `config.py` 中的 `USE_DEMO_TRADING = False`

### 风险提示
- **杠杆风险**: 杠杆交易可能放大亏损
- **强制平仓**: 保证金不足时可能被强制平仓
- **策略风险**: 策略存在亏损风险
- **市场风险**: 加密货币市场波动较大

### 合约交易特点
- **真正做空**: 支持真正的做空操作
- **杠杆交易**: 使用杠杆放大收益和风险
- **资金效率**: 比现货交易资金利用率更高
- **交易成本**: 合约交易手续费相对较低

## 📞 技术支持

如有问题，请检查：
1. API配置是否正确
2. 网络连接是否正常
3. 账户权限是否充足
4. 策略参数是否合理
5. 杠杆设置是否合适

## 📖 详细说明

更多详细信息请查看 [CONTRACT_STRATEGY_USAGE.md](CONTRACT_STRATEGY_USAGE.md)