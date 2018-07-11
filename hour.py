#!-*-coding:utf-8 -*-
import math
import time
import datetime
from fcoin3 import Fcoin
from collections import defaultdict
import config
from threading import Thread
from balance import balance
from log_back import Log
import csv

class App():
    def __init__(self):
        self.fcoin = Fcoin()
        self.fcoin.auth(config.api_key, config.api_secret)
        self.log = Log("")
        self.symbol = 'ftusdt'
        self.order_id = None
        self.dic_balance = defaultdict(lambda: None)
        self.now_price = 0.0
        self.type = 0
        self.fee = 0.0
        self.count_flag = 0
        self.fall_rise = 0
        self.buy_price =0.0
        self.sell_price = 0.0

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
    
    def server_time(self):
        now = datetime.datetime.fromtimestamp(int(self.fcoin.get_server_time()/1000))
        return now

    def dateDiffInSeconds(self, date1, date2):
        timedelta = date2 - date1
        return timedelta.days*24*3600 + timedelta.seconds
        
    def do_hour(self):
        self.dic_balance = self.get_blance()
        ft = self.dic_balance["ft"]
        usdt = self.dic_balance["usdt"]
        print('ft:%s usdt:%s' % (ft.available,usdt.available))

        if usdt.available > 10:
            price = self.digits(self.get_must_buy_ticker(),6)
            amount = self.digits(usdt.available / price * 0.98, 2)
            if amount >= 5:
                self.log.info('buy price--[%s] amout--[%s]' % (price,amount))
                data = self.fcoin.buy(self.symbol, price, amount, 'limit')
                if data:
                    self.order_id = data['data']
                    self.log.info('buy order success price--[%s] amout--[%s]' % (price,amount))

                    server_time = self.server_time()
                    start_time = server_time.replace(minute=58, second=50,microsecond=0)
                    sleep_seconds = self.dateDiffInSeconds(server_time, start_time)
                    if sleep_seconds > 1:
                        time.sleep(sleep_seconds)
                    
                    self.dic_balance = self.get_blance()
                    ft = self.dic_balance["ft"]
                    usdt = self.dic_balance["usdt"]
                    
                    new_price = price
                    while new_price <= price:
                        new_price = self.digits(self.get_must_sell_ticker(),6)
                        time.sleep(5)

                    if new_price > price:
                        self.log.info('sell price--[%s] amout--[%s]' % (price,amount))
                        data = self.fcoin.sell(self.symbol, new_price, amount,'limit')
                        self.log.info('sell order success price--[%s] amout--[%s]' % (new_price, amount))


    def loop(self):
        while True:
            try:
                server_time = self.server_time()
                start_time = server_time.replace(minute=50, second=0,microsecond=0)
                sleep_seconds = self.dateDiffInSeconds(server_time, start_time)
                if sleep_seconds > 1:
                    print("servertime: %s , starttime: %s , sleep: %s" % (server_time,start_time,sleep_seconds))
                    time.sleep(sleep_seconds)
                    self.do_hour()
                else:
                    time.sleep(60)

            except Exception as e:
                self.log.info(e)
                print(e)
            finally:
                self.reset_save_attrubute()

if __name__ == '__main__':
    run = App()
    run.loop()
    print('done')
