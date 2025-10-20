"""
OKX HTTP客户端
直接使用HTTP请求，不依赖SDK
基于OKX API v5文档
"""
import requests
import time
import hmac
import hashlib
import base64
import json
from config import API_KEY, SECRET_KEY, PASSPHRASE, FLAG, DEFAULT_INST_ID, TRADING_MODE

class OKXHTTPClient:
    """OKX HTTP客户端"""
    
    def __init__(self):
        self.api_key = API_KEY
        self.secret_key = SECRET_KEY
        self.passphrase = PASSPHRASE
        self.flag = FLAG
        self.trading_mode = TRADING_MODE
        
        # API端点
        if self.flag == "0":  # 实盘
            self.base_url = "https://www.okx.com"
        else:  # 模拟
            self.base_url = "https://www.okx.com"
        
        print(f"🔧 初始化OKX客户端 - {self.trading_mode}模式")
    
    def _get_timestamp(self):
        """获取时间戳"""
        return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    
    def _sign(self, timestamp, method, request_path, body=''):
        """生成签名"""
        message = timestamp + method + request_path + body
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def _get_headers(self, method, request_path, body=''):
        """获取请求头"""
        timestamp = self._get_timestamp()
        signature = self._sign(timestamp, method, request_path, body)
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        # 模拟交易需要添加特殊头部
        if self.flag == "1":
            headers['x-simulated-trading'] = '1'
        
        return headers
    
    def _request(self, method, endpoint, params=None, data=None):
        """发送HTTP请求"""
        url = self.base_url + endpoint
        
        if data:
            body = json.dumps(data)
        else:
            body = ''
        
        headers = self._get_headers(method, endpoint, body)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f'不支持的HTTP方法: {method}')
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return None
    
    def get_ticker(self, inst_id=DEFAULT_INST_ID):
        """获取行情数据"""
        endpoint = f'/api/v5/market/ticker?instId={inst_id}'
        return self._request('GET', endpoint)
    
    def get_candles(self, inst_id=DEFAULT_INST_ID, bar="1H", limit=100):
        """获取K线数据"""
        endpoint = f'/api/v5/market/candles?instId={inst_id}&bar={bar}&limit={limit}'
        return self._request('GET', endpoint)
    
    def get_instruments(self, inst_type="SPOT"):
        """获取交易产品信息"""
        endpoint = f'/api/v5/public/instruments?instType={inst_type}'
        return self._request('GET', endpoint)
    
    def get_account_balance(self, ccy=None):
        """获取账户余额"""
        endpoint = '/api/v5/account/balance'
        if ccy:
            endpoint += f'?ccy={ccy}'
        return self._request('GET', endpoint)
    
    def place_order(self, inst_id, side, ord_type, sz, px=None):
        """下单"""
        endpoint = '/api/v5/trade/order'
        data = {
            'instId': inst_id,
            'tdMode': 'cash',  # 现货模式
            'side': side,
            'ordType': ord_type,
            'sz': sz
        }
        
        if px:
            data['px'] = px
        
        return self._request('POST', endpoint, data=data)
    
    def get_orders(self, inst_id=None, state=None):
        """获取订单列表"""
        endpoint = '/api/v5/trade/orders-pending'
        params = {}
        if inst_id:
            params['instId'] = inst_id
        if state:
            params['state'] = state
        
        return self._request('GET', endpoint, params=params)
    
    def get_order_history(self, inst_id=None, state=None):
        """获取历史订单"""
        endpoint = '/api/v5/trade/orders-history'
        params = {}
        if inst_id:
            params['instId'] = inst_id
        if state:
            params['state'] = state
        
        return self._request('GET', endpoint, params=params)
    
    def cancel_order(self, inst_id, ord_id):
        """撤单"""
        endpoint = '/api/v5/trade/cancel-order'
        data = {
            'instId': inst_id,
            'ordId': ord_id
        }
        return self._request('POST', endpoint, data=data)
    
    def place_futures_order(self, inst_id, side, ord_type, sz, px=None, td_mode='cross', pos_side='net'):
        """下期货订单"""
        endpoint = '/api/v5/trade/order'
        data = {
            'instId': inst_id,
            'tdMode': td_mode,  # 保证金模式: cross, isolated
            'side': side,       # buy, sell
            'ordType': ord_type, # market, limit
            'sz': sz,           # 数量
            'posSide': pos_side # 持仓方向: long, short, net
        }
        
        if px:
            data['px'] = px
        
        return self._request('POST', endpoint, data=data)
    
    def get_positions(self, inst_id=None):
        """获取持仓信息"""
        endpoint = '/api/v5/account/positions'
        params = {}
        if inst_id:
            params['instId'] = inst_id
        
        return self._request('GET', endpoint, params=params)
    
    def get_futures_balance(self, ccy=None):
        """获取期货账户余额"""
        endpoint = '/api/v5/account/balance'
        params = {}
        if ccy:
            params['ccy'] = ccy
        
        return self._request('GET', endpoint, params=params)
    
    def set_leverage(self, inst_id, lever, mgn_mode='cross', pos_side='net'):
        """设置杠杆倍数"""
        endpoint = '/api/v5/account/set-leverage'
        data = {
            'instId': inst_id,
            'lever': str(lever),
            'mgnMode': mgn_mode,
            'posSide': pos_side
        }
        return self._request('POST', endpoint, data=data)

# 全局客户端实例
client = OKXHTTPClient()
