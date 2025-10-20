"""
简单的OKX API测试
基于官方SDK
"""
import okx.Account as Account
import okx.Trade as Trade
import okx.MarketData as MarketData
import okx.PublicData as PublicData
from config import API_KEY, SECRET_KEY, PASSPHRASE, FLAG

def test_basic_connection():
    """测试基本连接"""
    print("=== OKX API 基本连接测试 ===")
    
    try:
        # 测试公共API（不需要认证）
        print("1. 测试公共API...")
        market_api = MarketData.MarketAPI(flag=FLAG)
        
        # 获取BTC行情
        result = market_api.get_ticker(instId="BTC-USDT")
        if result and result.get('code') == '0':
            data = result['data'][0]
            print(f"✅ BTC价格: ${data['last']}")
            print(f"   24h涨跌: {data['chg']}%")
        else:
            print("❌ 获取行情失败")
            return False
        
        # 测试私有API（需要认证）
        print("\n2. 测试私有API...")
        try:
            account_api = Account.AccountAPI(
                api_key=API_KEY,
                api_secret_key=SECRET_KEY,
                passphrase=PASSPHRASE,
                use_server_time=False,
                flag=FLAG
            )
            
            # 获取账户余额
            balance_result = account_api.get_account_balance()
            if balance_result and balance_result.get('code') == '0':
                print("✅ 账户API连接成功")
                print("账户余额:")
                for detail in balance_result['data'][0]['details']:
                    if float(detail['bal']) > 0:
                        print(f"   {detail['ccy']}: {detail['bal']}")
            else:
                print("❌ 账户API连接失败")
                return False
                
        except Exception as e:
            print(f"❌ 私有API测试失败: {e}")
            return False
        
        print("\n✅ 所有API测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_trading_functions():
    """测试交易功能"""
    print("\n=== 交易功能测试 ===")
    
    try:
        # 初始化交易API
        trade_api = Trade.TradeAPI(
            api_key=API_KEY,
            api_secret_key=SECRET_KEY,
            passphrase=PASSPHRASE,
            use_server_time=False,
            flag=FLAG
        )
        
        # 获取订单列表
        print("1. 获取订单列表...")
        orders = trade_api.get_order_list()
        if orders and orders.get('code') == '0':
            print(f"✅ 当前订单数量: {len(orders['data'])}")
        else:
            print("❌ 获取订单列表失败")
        
        # 获取历史订单
        print("\n2. 获取历史订单...")
        history = trade_api.get_orders_history()
        if history and history.get('code') == '0':
            print(f"✅ 历史订单数量: {len(history['data'])}")
        else:
            print("❌ 获取历史订单失败")
        
        print("✅ 交易功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 交易功能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("OKX量化交易系统 - API测试")
    print("基于官方SDK: python-okx")
    print("=" * 50)
    
    # 基本连接测试
    if test_basic_connection():
        # 交易功能测试
        test_trading_functions()
    else:
        print("\n❌ 基本连接测试失败，请检查API配置")
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    main()