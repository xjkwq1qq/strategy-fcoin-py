#!-*-coding:utf-8 -*-

from enum import Enum
import schedule
from .stategy_status import stategy_status


class StategUp():
    # 0.2%的价格区间进行处理
    # 量尽量小，amount设置到100，不影响

    def __init__(self):
        self.order_id = None
        self.stategy_status = None
        self.is_exceute = False

    def set_app(self, app):
        self.app = app

    # 执行周期
    def schedule(self):
        schedule.every(10).seconds.do(self.stategy)

    # 执行的策略
    def stategy(self):
        if self.stategy_status is None:
            # 检测 买或者卖
            if self.app.check_could_sell_price <= self.app.get_must_buy_ticker():
                self.sell()
            elif self.app.check_could_buy_price >= self.app.get_must_sell_ticker():
                self.buy()
        elif self.stategy_status == stategy_status(1):
            # 已经卖出，执行买入
            if self.app.check_could_buy_price >= self.app.get_must_buy_ticker():
                self.buy()
        elif self.stategy_status == stategy_status(2):
            # 已经买入，执行卖出
            if self.app.check_could_sell_price <= self.app.get_must_sell_ticker():
                self.sell()

    # 执行购买
    def buy(self):
        # 当前价格
        self.app.get_market_ticker()
        price = self.app.get_must_sell_ticker()
        dic_balance = self.app.get_blance()
        usdt = dic_balance["usdt"]

    # 买入
    def sell(self):

        dic_balance = self.app.get_blance()
        ft = dic_balance["ft"]
        # 执行卖出
        if ft.available > 5:
            self.app.get_market_ticker()
            price = self.app.get_must_buy_ticker()
            amount = ft.available
            self.log.error('sell price--[%s] amout--[%s]' % (price, amount))
            data = self.fcoin.sell(self.symbol, price, amount, 'limit')
            if data:
                success = self.check_order(data, 20)

    # 检查order是否执行完成,超时时间：s
    def check_order(self, data, timeout):
        return True

    # 停止
    def stop(self):
        pass


stategy_quick = StategUp()
