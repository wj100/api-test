"""
基础策略类
所有交易策略的基类
"""
import pandas as pd
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from okx_http_client import OKXHTTPClient
from config import DEFAULT_INST_ID, DEFAULT_INST_TYPE, TRADING_MODE
from utils.advanced_indicators import AdvancedIndicators

class BaseStrategy(ABC):
    """
    策略基类，定义了所有交易策略应实现的基本接口和通用功能。
    """
    def __init__(self, client: OKXHTTPClient, inst_id: str = DEFAULT_INST_ID, inst_type: str = DEFAULT_INST_TYPE):
        self.client = client
        self.inst_id = inst_id
        self.inst_type = inst_type
        self.position: Optional[Dict[str, Any]] = None  # 记录当前持仓信息
        self.entry_price: float = 0.0
        self.take_profit_ratio: float = 0.0
        self.stop_loss_ratio: float = 0.0
        self.indicators = AdvancedIndicators()
        print(f"初始化策略: {self.__class__.__name__} (交易对: {self.inst_id}, 模式: {TRADING_MODE})")

    def get_market_data(self, inst_id: str = None, bar: str = '1H', limit: str = '50') -> Optional[pd.DataFrame]:
        """获取K线数据"""
        try:
            if inst_id is None:
                inst_id = self.inst_id
            result = self.client.get_candles(inst_id, bar, limit)
            if result and result.get('code') == '0':
                data = result['data']
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'vol', 'volCcy', 'volCcy2', 'confirm'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df[['open', 'high', 'low', 'close', 'vol', 'volCcy', 'volCcy2']] = df[['open', 'high', 'low', 'close', 'vol', 'volCcy', 'volCcy2']].astype(float)
                df = df.sort_values('timestamp')
                return df
            else:
                print(f"❌ 获取K线数据失败: {result}")
                return None
        except Exception as e:
            print(f"获取K线数据异常: {e}")
            return None

    def get_account_balance(self, ccy: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取账户余额"""
        try:
            result = self.client.get_account_balance(ccy)
            if result and result.get('code') == '0':
                return result['data'][0]['details']
            else:
                print(f"❌ 获取账户余额失败: {result}")
                return None
        except Exception as e:
            print(f"获取账户余额异常: {e}")
            return None

    def place_order(self, inst_id: str, side: str, ord_type: str, sz: str, px: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """下单"""
        try:
            result = self.client.place_order(inst_id, side, ord_type, sz, px)
            if result and result.get('code') == '0':
                print(f"✅ 下单成功: {side} {sz} {inst_id}")
                return result
            else:
                print(f"❌ 下单失败: {result}")
                return None
        except Exception as e:
            print(f"下单异常: {e}")
            return None

    @abstractmethod
    def analyze_signal(self) -> Dict[str, Any]:
        """分析交易信号"""
        pass

    @abstractmethod
    def execute_trade(self, signal: Dict[str, Any]):
        """执行交易"""
        pass

    def run(self):
        """运行策略"""
        print(f"\n开始运行 {self.__class__.__name__} 策略...")
        print("按 Ctrl+C 停止")
        try:
            while True:
                signal = self.analyze_signal()
                print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 信号分析: {signal}")
                self.execute_trade(signal)
                print("等待1小时后进行下次分析...")
                time.sleep(3600)  # 每小时运行一次
        except KeyboardInterrupt:
            print(f"\n收到停止信号，正在退出 {self.__class__.__name__} 策略...")
        except Exception as e:
            print(f"策略运行错误: {e}")

    def get_position_info(self) -> Dict[str, Any]:
        """获取持仓信息"""
        return {
            "position": self.position,
            "entry_price": self.entry_price,
            "take_profit_ratio": self.take_profit_ratio,
            "stop_loss_ratio": self.stop_loss_ratio
        }
    
    def validate_order_amount(self, usdt_amount: float, btc_amount: float, current_price: float) -> bool:
        """验证订单金额是否满足最小要求"""
        # 检查最小订单金额（OKX BTC-USDT最小订单金额通常是10 USDT）
        min_order_value = 10  # 最小订单金额10 USDT
        if usdt_amount < min_order_value:
            print(f"⚠️ 订单金额 ${usdt_amount:.2f} 小于最小订单金额 ${min_order_value}")
            return False
        
        # 检查最小BTC数量（通常最小0.00001 BTC）
        min_btc_amount = 0.00001
        if btc_amount < min_btc_amount:
            print(f"⚠️ BTC数量 {btc_amount:.8f} 小于最小数量 {min_btc_amount}")
            return False
        
        return True
    
    def place_limit_order(self, inst_id: str, side: str, sz: str, current_price: float) -> Optional[Dict[str, Any]]:
        """下限价单，自动计算合适的价格"""
        # 计算限价单价格
        if side == "buy":
            # 买入时价格稍微高一点确保成交
            limit_price = str(round(current_price * 1.001, 2))
        else:
            # 卖出时价格稍微低一点确保成交
            limit_price = str(round(current_price * 0.999, 2))
        
        print(f"限价单价格: ${limit_price}")
        
        return self.place_order(
            inst_id=inst_id,
            side=side,
            ord_type="limit",
            sz=sz,
            px=limit_price
        )
