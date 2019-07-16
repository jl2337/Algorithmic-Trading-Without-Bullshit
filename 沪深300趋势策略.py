#!/usr/bin/env python
# coding: utf-8

# In[1]:


#!/usr/bin/env python
# coding: utf-8

# In[31]:


# 导包
import numpy as np
import pandas as pd
import datetime as dt
from WindPy import *

# 参数类
'''
请在参数类中设置策略的参数
'''


class para:
    # 回测起始时间
    start_date = pd.datetime.date(pd.Timestamp('2019-07-01'))
    # 交易资产时序OHLC
    w.start()
    # 回测至最新交易日
    if dt.datetime.now().hour >= 15:
        current_date = dt.date.today()
    else:
        current_date = dt.date.today() - dt.timedelta(1)
    # 交易资产为沪深300指数
    error_code,asset = w.wsd("000300.SH", "open,high,low,close", start_date, current_date, "PriceAdj=F",usedf=True)
    asset = asset.loc[start_date:]
    # 交易信号触发阈值
    threshold = 0.05
    # 交易成本
    transaction_cost = 7 / 10000
    # 调仓比例
    adj_percent = 0.05
    # 初始仓位
    start_position = 0.5
    # 组合价值（资产+流动资金），初始资金一百万
    balance = []
    balance.append(10 ** 7)
    # 前次交易价格
    prev_price = asset.OPEN[0]
    # 持仓数量
    asset_count = []
    asset_count.append(balance[-1] * start_position / ((prev_price) * (1 + transaction_cost)))
    # 调仓次数
    adjust_count = 1
    # 手头流动资金
    cash_available = []
    cash_available.append(balance[-1] * (1 - start_position))


'''
策略考虑交易成本，不考虑市场冲击成本，交易滑点
交易资产为沪深300指数，假定交易资产具备完美可分性
'''


# 获取时序数据
def get_TS_list():
    for dt in para.asset.index:
        signal_trigger(dt)
    return para.asset_count, para.cash_available, para.balance


# 触发交易信号
def signal_trigger(dt):
    if para.asset.HIGH.loc[dt] > para.prev_price * (1 + para.threshold):
        long(dt);para.adjust_count += 1
    elif para.asset.LOW.loc[dt] < para.prev_price * (1 - para.threshold):
        short(dt);para.adjust_count += 1
    else:
        para.asset_count.append(para.asset_count[-1])
        para.balance.append(para.cash_available[-1] + para.asset_count[-1] * para.asset.CLOSE.loc[dt])
        para.cash_available.append(para.cash_available[-1])


# 加仓
def long(dt):
    # 最新的投资组合价值
    port_value = para.cash_available[-1] + para.asset_count[-1] * (para.prev_price * (1 + para.threshold))
    # 调仓金额
    temp = port_value * para.adj_percent
    # 判断可用资金是否满足调仓的执行
    if temp > para.cash_available[-1]:
        # 无法满足，用剩余所有可用资金进行增仓
        para.asset_count.append(para.asset_count[-1] + para.cash_available[-1] /                                 (para.prev_price * (1 + para.threshold) * (1 + para.transaction_cost)))
        para.cash_available.append(0);
        para.balance.append(para.asset_count[-1] * para.asset.CLOSE.loc[dt])
    else:
        # 满足，按策略设置的比率增仓
        para.asset_count.append(para.asset_count[-1] + temp /                                 (para.prev_price * (1 + para.threshold) * (1 + para.transaction_cost)))
        # 可用资金
        para.cash_available.append(para.cash_available[-1] - temp)
        # 投资组合价值 = 资产价值 + 可用资金
        para.balance.append(para.cash_available[-1] + para.asset_count[-1] * para.asset.CLOSE.loc[dt])
    para.prev_price *= (1 + para.threshold)


# 减仓
def short(dt):
    # 最新的投资组合价值
    port_value = para.cash_available[-1] + para.asset_count[-1] * (para.prev_price * (1 - para.threshold))
    # 现有交易资产价值
    temp = para.asset_count[-1] * (para.prev_price * (1 - para.threshold))
    # 判断现有仓位是否满足调仓的执行
    if temp < port_value * para.adj_percent:
        # 不满足，卖出所有交易资产
        para.cash_available.append(para.cash_available[-1] + temp * (1 - para.transaction_cost))
        para.asset_count.append(0);
        para.balance.append(para.cash_available[-1])
    else:
        # 满足，按策略设置比例减仓
        para.cash_available.append(para.cash_available[-1] + port_value * para.adj_percent * (1-para.transaction_cost))
        para.asset_count.append(para.asset_count[-1] - port_value*para.adj_percent                                  / (para.prev_price * (1 - para.threshold) * (1 + para.transaction_cost)))
        para.balance.append(para.cash_available[-1] + para.asset_count[-1] * para.asset.CLOSE.loc[dt])
    para.prev_price *= (1 - para.threshold)


# 持仓数量、投资组合价值的时序数据
port_asset_amount, port_cash, port_value = get_TS_list();
start_balance = port_value[0];
del port_asset_amount[0];
del port_value[0];
del port_cash[0]

# 投资组合净值
port_per_value = np.array(port_value) / start_balance

# 指数组合净值
bmark_per_value = np.array(para.asset.CLOSE / para.asset.OPEN[0])

# 超额收益
excess_per_value = port_per_value - bmark_per_value

# 仓位占比
port_position = 1 - np.array(port_cash) / np.array(port_value)

# 收益汇总数据
df = pd.DataFrame({'投资组合净值': port_per_value, '沪深300指数净值': bmark_per_value,                    '超额收益': excess_per_value, '仓位占用比例': port_position},                   index=para.asset.index)
df.to_csv(r"C:\Users\hp\Desktop\JJ\沪深300趋势策略.csv",encoding= 'gbk')

