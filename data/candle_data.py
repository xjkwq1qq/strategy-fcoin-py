#!-*-coding:utf-8 -*-
import schedule
import config


class CandleData():
    def __init__(self):
        self.candle_M1 = None
        self.candle_H1 = None

    def set_app(self, app):
        self.app = app

    # 定时任务
    def schedule(self):
        schedule.every(20).seconds.do(self.sync_candle_M1)
        schedule.every(10).minutes.do(self.sync_candle_H1)

    def get_candle_M1(self):
        if self.candle_M1 is None:
            self.sync_candle_M1()
        return self.candle_M1

    def sync_candle_M1(self):
        self.candle_M1 = self.app.fcoin.get_candle("M1", config.symbol)

    def get_candle_H1(self):
        if self.candle_H1 is None:
            self.sync_candle_M1()
        return self.candle_H1

    def sync_candle_H1(self):
        self.candle_H1 = self.app.fcoin.get_candle("H1", config.symbol)

candle_data = CandleData()