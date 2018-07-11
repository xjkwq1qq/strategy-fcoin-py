#!-*-coding:utf-8 -*-
import math
import time
from fcoin3 import Fcoin
from collections import defaultdict
import config
from threading import Thread
from balance import balance
from log_back import Log
import csv
from concurrent.futures import ThreadPoolExecutor


class App():
    def __init__(self):
        self.fcoin = Fcoin()
        self.fcoin.auth(config.api_key, config.api_secret)
        self.log = Log("")
        self.symbol = 'ftusdt'
        self.order_id = None
        self.dic_balance = defaultdict(lambda: None)
        self.time_order = time.time()
        self.oldprice = self.digits(self.get_ticker(),6)
        self.now_price = 0.0
        self.type = 0
        self.fee = 0.0
        self.count_flag = 0
        self.fall_rise = 0
        self.buy_price =0.0
        self.sell_price = 0.0
        self.executor = ThreadPoolExecutor(max_workers=4)

    def digits(self, num, digit):
        site = pow(10, digit)
        tmp = num * site
        tmp = math.floor(tmp) / site
        return tmp

    def get_ticker(self):
        ticker = self.fcoin.get_market_ticker(self.symbol)['data']['ticker']
        self.now_price = ticker[0]
        self.buy_price = ticker[2]
        self.sell_price = ticker[4]
        return self.now_price

    def get_must_sell_ticker(self):
        ticker = self.fcoin.get_market_ticker(self.symbol)['data']['ticker']
        self.now_price = ticker[0]
        self.buy_price = ticker[2]
        self.sell_price = ticker[4]
        return self.buy_price

    def get_must_buy_ticker(self):
        ticker = self.fcoin.get_market_ticker(self.symbol)['data']['ticker']
        self.now_price = ticker[0]
        self.buy_price = ticker[2]
        self.sell_price = ticker[4]
        return self.sell_price

    def get_blance(self):
        dic_blance = defaultdict(lambda: None)
        data = self.fcoin.get_balance()
        if data:
            for item in data['data']:
                dic_blance[item['currency']] = balance(float(item['available']), float(item['frozen']),float(item['balance']))
        return dic_blance

    def save_csv(self,array):
        with open("data/trade.csv","a+",newline='') as w:
            writer = csv.writer(w)
            writer.writerow(array)

    def reset_save_attrubute(self):
        self.now_price = 0.0
        self.type = 0
        self.fee = 0.0
        self.order_id = None

    def jump(self):
        self.dic_balance = self.get_blance()
        ft = self.dic_balance["ft"]
        usdt = self.dic_balance["usdt"]
        if usdt.available > 10:
            price = self.digits(self.get_must_buy_ticker(),6)
            amount = self.digits(usdt.available / price * 0.99, 2)
            if amount >= 5:
                data = self.fcoin.buy(self.symbol, price, amount,'market')
                if data:
                    self.fee = amount*0.001
                    self.order_id = data['data']
                    self.time_order = time.time()
                    self.type = 1
                    self.log.info('buy success price--[%s] amout--[%s] fee--[%s]' % (price,amount ,self.fee))

                    time.sleep(270)
                    
                    self.dic_balance = self.get_blance()
                    ft = self.dic_balance["ft"]
                    usdt = self.dic_balance["usdt"]

                    new_price = price
                    while new_price <= price:
                        new_price = self.digits(self.get_must_sell_ticker(),amount)
                        time.sleep(5)

                    if new_price > price:
                        data = self.fcoin.sell(self.symbol, price, amount,'market')
                        self.log.info('sell success price--[%s] amout--[%s] fee--[%s]' % (price,amount ,self.fee))

if __name__ == '__main__':
    run = App()
    thread = Thread(target=run.jump)
    thread.start()
    thread.join()
    print('done')
