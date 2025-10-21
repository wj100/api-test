"""
运行优化版SAR策略
"""

import sys
import os
sys.path.append('/Users/wangjun/open_code/okx/api-test')

from okx_http_client import OKXHTTPClient
from trading_strategies.optimized_sar_strategy import OptimizedSARStrategy

def main():
    """主函数"""
    print("🚀 启动优化版SAR策略")
    
    # 初始化客户端
    client = OKXHTTPClient()
    
    # 创建策略实例
    strategy = OptimizedSARStrategy(client)
    
    # 运行策略
    strategy.run()

if __name__ == "__main__":
    main()
