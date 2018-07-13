#!-*-coding:utf-8 -*-

from enum import Enum
import schedule


# 价格提升
class StategDown():
    # 0.2%的价格区间进行处理
    # 量尽量小，amount设置到100，不影响

    def __init__(self):
        self.order_id = None
        self.stategy_status = None

    def set_app(self, app):
        self.app = app

    # 执行周期
    def schedule(self):
        schedule.every(1).seconds.do(self.stategy)

    # 执行的策略
    def stategy(self):
        print(1)

    # 执行购买
    def buy(self):
        pass

    # 买入
    def sell(self):
        pass

    # 停止
    def stop(self):
        pass


stategy_quick = StategDown()
