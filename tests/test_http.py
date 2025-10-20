"""
OKX HTTP交易系统测试
直接使用HTTP请求，不依赖SDK
"""
from okx_http_client import client
from config import DEFAULT_INST_ID

def test_public_api():
    """测试公共API"""
    print("=== 测试公共API ===")
    
    try:
        # 测试获取行情
        print("1. 获取BTC行情...")
        ticker = client.get_ticker(DEFAULT_INST_ID)
        if ticker and ticker.get('code') == '0':
            data = ticker['data'][0]
            print(f"✅ BTC价格: ${data['last']}")
            if 'chg' in data:
                print(f"   24h涨跌: {data['chg']}%")
            if 'high' in data:
                print(f"   24h最高: ${data['high']}")
            if 'low' in data:
                print(f"   24h最低: ${data['low']}")
        else:
            print("❌ 获取行情失败")
            return False
        
        # 测试获取K线数据
        print("\n2. 获取K线数据...")
        candles = client.get_candles(DEFAULT_INST_ID, "1H", 5)
        if candles and candles.get('code') == '0':
            print(f"✅ 获取到 {len(candles['data'])} 根K线")
            latest = candles['data'][0]
            print(f"   最新K线: 开盘${latest[1]}, 最高${latest[2]}, 最低${latest[3]}, 收盘${latest[4]}")
        else:
            print("❌ 获取K线数据失败")
            return False
        
        # 测试获取交易产品信息
        print("\n3. 获取交易产品信息...")
        instruments = client.get_instruments("SPOT")
        if instruments and instruments.get('code') == '0':
            print(f"✅ 获取到 {len(instruments['data'])} 个现货交易对")
        else:
            print("❌ 获取交易产品信息失败")
            return False
        
        print("✅ 公共API测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 公共API测试失败: {e}")
        return False

def test_private_api():
    """测试私有API"""
    print("\n=== 测试私有API ===")
    
    try:
        # 测试获取账户余额
        print("1. 获取账户余额...")
        balance = client.get_account_balance()
        if balance and balance.get('code') == '0':
            print("✅ 账户余额:")
            for detail in balance['data'][0]['details']:
                avail_bal = float(detail.get('availBal', 0))
                if avail_bal > 0:
                    print(f"   {detail['ccy']}: {avail_bal}")
        else:
            print("❌ 获取账户余额失败")
            return False
        
        # 测试获取订单列表
        print("\n2. 获取订单列表...")
        orders = client.get_orders()
        if orders and orders.get('code') == '0':
            print(f"✅ 当前订单数量: {len(orders['data'])}")
            if orders['data']:
                for order in orders['data'][:3]:
                    print(f"   订单ID: {order['ordId']}, 状态: {order['state']}, 数量: {order['sz']}")
        else:
            print("❌ 获取订单列表失败")
            return False
        
        print("✅ 私有API测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 私有API测试失败: {e}")
        return False

def test_trading_system():
    """测试交易系统"""
    print("\n=== 测试交易系统 ===")
    
    try:
        from http_trader import OKXHTTPTrader
        
        # 创建交易系统
        trader = OKXHTTPTrader()
        
        # 测试获取行情
        print("1. 测试获取行情...")
        ticker = trader.get_ticker()
        if ticker:
            print(f"✅ BTC价格: ${ticker['last']}")
        else:
            print("❌ 获取行情失败")
            return False
        
        # 测试获取账户余额
        print("\n2. 测试获取账户余额...")
        balance = trader.get_balance()
        if balance:
            print("✅ 账户余额:")
            for detail in balance:
                avail_bal = float(detail.get('availBal', 0))
                if avail_bal > 0:
                    print(f"   {detail['ccy']}: {avail_bal}")
        else:
            print("❌ 获取账户余额失败")
            return False
        
        # 测试信号分析
        print("\n3. 测试信号分析...")
        signal = trader.analyze_ma_signal()
        print(f"✅ 信号分析结果: {signal}")
        
        print("✅ 交易系统测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 交易系统测试失败: {e}")
        return False

def main():
    """主函数"""
    print("OKX量化交易系统 - HTTP版本测试")
    print("直接使用HTTP请求，不依赖SDK")
    print("=" * 60)
    
    # 测试公共API
    if not test_public_api():
        print("\n❌ 公共API测试失败，请检查网络连接")
        return
    
    # 测试私有API
    if not test_private_api():
        print("\n❌ 私有API测试失败，请检查API配置")
        return
    
    # 测试交易系统
    if not test_trading_system():
        print("\n❌ 交易系统测试失败")
        return
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！系统可以正常使用")
    print("\n运行交易系统: python http_trader.py")

if __name__ == "__main__":
    main()
