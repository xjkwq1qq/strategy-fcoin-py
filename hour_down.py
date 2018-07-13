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
import schedule
import queue
import numpy as np
from numpy import mean, ptp, var, std, mean, median
from stategy.stategy_quick import stategy_quick
from data.candle_data import candle_data
from enum import Enum


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
        self.buy_price = 0.0
        # 正在卖出
        self.in_sell = False
        # 卖出价格
        self.sell_price = 0.0
        # 价格队列
        self.price_queue = []
        # 验证是否卖出价格
        self.check_sell_price = 0.0
        # 总共的增量
        self.total_increment = 0.0
        # 服务器时间
        self.diff_server_time = None

        stategy_quick.set_app(self)
        candle_data.set_app(self)

    def digits(self, num, digit):
        site = pow(10, digit)
        tmp = num * site
        tmp = math.floor(tmp) / site
        return tmp

    def get_ticker(self):
        if self.sell_price is None:
            self.get_market_ticker()
        return self.now_price

    def get_must_sell_ticker(self):
        if self.sell_price is None:
            self.get_market_ticker()
        return self.buy_price

    def get_must_buy_ticker(self):
        if self.sell_price is None:
            self.get_market_ticker()
        return self.sell_price

    def get_market_ticker(self):
        ticker = self.fcoin.get_market_ticker(self.symbol)['data']['ticker']
        self.now_price = ticker[0]
        self.buy_price = ticker[2]
        self.sell_price = ticker[4]

    # 获取当前用户持币信息
    def get_blance(self):
        if self.dic_blance is None:
            self.syn_blance()
        return self.dic_blance

    # 同步持币信息
    def syn_blance(self):
        dic_blance = defaultdict(lambda: None)
        data = self.fcoin.get_balance()
        if data:
            for item in data['data']:
                dic_blance[item['currency']] = balance(float(item['available']), float(item['frozen']),
                                                       float(item['balance']))
        self.dic_blance = dic_blance
        return dic_blance

    def save_csv(self, array):
        with open("data/trade.csv", "a+", newline='') as w:
            writer = csv.writer(w)
            writer.writerow(array)

    def reset_save_attrubute(self):
        self.now_price = 0.0
        self.type = 0
        self.fee = 0.0
        self.order_id = None

    # 获取当前服务器时间
    def get_server_time(self):
        if self.diff_server_time is None:
            self.synchronize_time()
        return datetime.datetime.fromtimestamp(
            int((int(datetime.datetime.now().timestamp() * 1000) + self.diff_server_time) / 1000))

    # 同步时间
    def synchronize_time(self):
        # self.server_time = datetime.datetime.fromtimestamp(int(self.fcoin.get_server_time() / 1000))
        self.diff_server_time = int(self.fcoin.get_server_time()) - int(datetime.datetime.now().timestamp() * 1000)
        # print(self.diff_server_time)

    def dateDiffInSeconds(self, date1, date2):
        timedelta = date2 - date1
        return timedelta.days * 24 * 3600 + timedelta.seconds

    def do_hour(self):
        self.dic_balance = self.get_blance()
        ft = self.dic_balance["ft"]
        usdt = self.dic_balance["usdt"]
        print('ft:%s usdt:%s' % (ft.available, usdt.available))

        if usdt.available > 50:
            # 买入ft
            price = self.digits(self.get_must_buy_ticker(), 6)
            amount = self.digits(usdt.available / price * 0.98, 2)
            if amount >= 5:
                self.log.info('buy price--[%s] amout--[%s]' % (price, amount))
                data = self.fcoin.buy(self.symbol, price, amount, 'limit')
                if data:
                    self.order_id = data['data']
                    self.log.info('buy order success price--[%s] amout--[%s]' % (price, amount))

                    server_time = self.get_server_time()
                    start_time = server_time.replace(minute=58, second=50, microsecond=0)
                    sleep_seconds = self.dateDiffInSeconds(server_time, start_time)
                    if sleep_seconds > 1:
                        time.sleep(sleep_seconds)

                    self.dic_balance = self.get_blance()
                    ft = self.dic_balance["ft"]
                    usdt = self.dic_balance["usdt"]

                    new_price = price
                    while new_price <= price:
                        new_price = self.digits(self.get_must_sell_ticker(), 6)
                        time.sleep(5)

                    if new_price > price:
                        self.log.info('sell price--[%s] amout--[%s]' % (price, amount))
                        data = self.fcoin.sell(self.symbol, new_price, amount, 'limit')
                        self.log.info('sell order success price--[%s] amout--[%s]' % (new_price, amount))
        else:

            self.sell_ft()

    # 查找到合理的卖点
    def get_sell_point(self):
        pass

    def get_sell_count(self):
        return config.sell_count

    # 卖出ft
    def sell_ft(self):
        # 卖出ft


        #       1）未持续上涨，直接卖出
        #       2）持续上涨，查找高点
        if self.get_server_time().minute < 5 and not self.in_sell:
            self.in_sell = True
            # 1、查看时间区间是在预期范围 01
            if self.get_ticker() > self.check_sell_price:
                # 2、查找合理点位卖出，
                data = self.fcoin.sell(self.symbol, self.get_sell_point(), self.get_sell_count(), 'limit')

                # 让订单卖出
                while (True):
                    # 获取订单状态
                    is_done = True
                    #
                    if is_done:
                        self.sell_done = True
                        break
                    else:
                        # 超过时间判断
                        # 超过时间重新下单
                        pass

        self.in_sell = False

    def get_buy_point(self):
        pass

    def get_sell_count(self):
        pass

    # 买入ft,直到买入成功为止
    def buy_ft(self):
        # 根据时间获取买入策略
        # 已经超过
        # 如果已经超过买入点，默认检测5分钟不够买，下降趋势情况下，超过根据涨跌获取买入点
        pass

    def get_price_queue(self):
        data = run.fcoin.get_candle("M1", run.symbol)
        self.price_queue = []
        for item in data['data']:
            self.price_queue.append(item['close'])

        trades_1 = '#'
        trades_2 = '#'
        trades_3 = '#'
        trades_5 = '#'
        trades_10 = '#'
        trades_20 = '#'
        trades_30 = '#'
        trades_60 = '#'
        # 1分钟
        new_price = self.price_queue[0]
        old_price = self.price_queue[1]
        trades_1 = self.digits((new_price - old_price) / old_price * 100, 6)
        # 2分钟
        new_price = self.price_queue[0]
        old_price = self.price_queue[2]
        trades_2 = self.digits((new_price - old_price) / old_price * 100, 6)
        # 3分钟
        new_price = self.price_queue[0]
        old_price = self.price_queue[3]
        trades_3 = self.digits((new_price - old_price) / old_price * 100, 6)
        # 5分钟
        new_price = self.price_queue[0]
        old_price = self.price_queue[5]
        trades_5 = self.digits((new_price - old_price) / old_price * 100, 6)
        # 10分钟
        new_price = self.price_queue[0]
        old_price = self.price_queue[10]
        trades_10 = self.digits((new_price - old_price) / old_price * 100, 6)
        # 20分钟
        new_price = self.price_queue[0]
        old_price = self.price_queue[20]
        trades_20 = self.digits((new_price - old_price) / old_price * 100, 6)
        # 30分钟
        new_price = self.price_queue[0]
        old_price = self.price_queue[30]
        trades_30 = self.digits((new_price - old_price) / old_price * 100, 6)
        # 60分钟
        new_price = self.price_queue[0]
        old_price = self.price_queue[60]
        trades_60 = self.digits((new_price - old_price) / old_price * 100, 6)

        print(
            '数据行情(百分比) 1m--[%s] 2m--[%s] 3m--[%s] 5m--[%s] 10m--[%s] 20m--[%s] 30m--[%s] 60m--[%s]' % (
                str(trades_1), str(trades_2), str(trades_3), str(trades_5), str(trades_10), str(trades_20),
                str(trades_30), str(trades_60)))

    def average(self, array):
        total = 0.0
        n = len(array)
        for num in array:
            total += num
        return 1.0 * total / n

    # 增长量计算
    def increment(self):
        data = self.fcoin.get_candle("H1", run.symbol)
        for item in data['data']:
            timeArray = time.localtime(item['id'])
            otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            # print("%s ----- %s" % (otherStyleTime, item))
        total_increment = 0;
        for index in range(self.get_server_time().hour):
            new_price = data['data'][index + 1]['close'];
            # print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data['data'][index+ 1]['id'])))
            old_price = data['data'][index + 1 + 24]['close'];
            total_increment += (new_price - old_price) / old_price
        self.total_increment = total_increment
        print(total_increment)
        pre_date_data = []
        max_data = []
        min_data = []
        cur_hour = self.get_server_time().hour
        for index in range(24 + cur_hour):
            cur_data = data['data'][index]
            pre_date_data.append(cur_data['close'])
            pre_date_data.append(cur_data['high'])
            pre_date_data.append(cur_data['low'])

            max_data.append(cur_data['high'])
            min_data.append(cur_data['low'])

            # print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data['data'][index + cur_hour]['id'])))

        # 变化系数计算
        cur_change_data = []
        pre_change_data = []
        for index in range(12):
            cur_data = data['data'][index]
            pre_data = data['data'][index + 24]
            cur_change_data.append(cur_data['close'])
            pre_change_data.append(pre_data['close'])

        change_price = np.average(np.array(cur_change_data)) / np.average(np.array(pre_change_data))
        print(change_price)

        np_data = np.array(pre_date_data)
        np_data_max = np.array(max_data)
        np_data_min = np.array(min_data)

        np_data_max.sort()
        max_avg_price = np.average(np_data_max[len(np_data_max) - 3:])
        np_data_min.sort()
        min_avg_price = np.average(np_data_min[0:3])
        # 极差
        # print(ptp(data))
        # print(var(data))
        # print(std(data))
        # print(mean(data) / std(data))
        # print(data.min())
        # print(median(data))
        # print(mean(data))
        # print(data)
        median_data = np.average(np_data)
        print(np_data)
        print(median_data)
        print(max_avg_price)
        print(min_avg_price)
        self.check_min_sell_price = (median_data - (median_data - min_avg_price) * 0.3) * change_price
        self.check_could_sell_price = (median_data + (max_avg_price - median_data) * 0.7) * change_price
        self.check_max_buy_price = (median_data + (max_avg_price - median_data) * 0.3) * change_price
        self.check_could_buy_price = (median_data - (median_data - min_avg_price) * 0.7) * change_price

        print(self.check_min_sell_price)
        print(self.check_could_sell_price)
        print(self.check_max_buy_price)
        print(self.check_could_buy_price)

    # 获取区间
    def get_interval(self):
        print(candle_data.get_candle_M1())

    # 计算区间
    def calculation_interval(self):
        candle_M1 = candle_data.get_candle_M1()
        candle_M1_data = candle_M1['data']
        for index in range(60):
            candle_M1_data[60 - 1 - index]

    # 改为定时任务
    def loop(self):

        stategy_quick.schedule()
        candle_data.schedule()
        # 开启卖出线程
        # schedule.every(2).seconds.do(self.get_interval)
        schedule.every(1).seconds.do(self.get_market_ticker)
        # schedule.every(10).seconds.do(self.sell_ft)
        # schedule.every(30).seconds.do(self.get_price_queue)
        # schedule.every(10).seconds.do(self.print_price_queue)
        while True:
            schedule.run_pending()
            time.sleep(1)
            # while True:
            #     try:
            #         server_time = self.server_time()
            #         start_time = server_time.replace(minute=48, second=0, microsecond=0)
            #         sleep_seconds = self.dateDiffInSeconds(server_time, start_time)
            #         if sleep_seconds > 1:
            #             print("servertime: %s , starttime: %s , sleep: %s" % (server_time, start_time, sleep_seconds))
            #             time.sleep(sleep_seconds)
            #             self.do_hour()
            #         else:
            #             time.sleep(60)
            #
            #     except Exception as e:
            #         self.log.info(e)
            #         print(e)
            #     finally:
            #         self.reset_save_attrubute()


class ChangeModel():
    # 开始节点
    start_price = None;
    # 结束节点
    end_price = None;
    # 上升最大斜率
    max_up_slope = None;

    # 下降最大斜率
    max_down_slope = None
    # 总的上升斜率
    total_up_slope = None
    # 总的下降斜率
    total_down_slope = None

    # 上升/下降/波动
    change_state = None


class ChangeState(Enum):
    up: 1  # 上涨
    down: 2  # 下降
    flux: 3  # 波动


app = App()
if __name__ == '__main__':
    run = App()
    run.increment()
    run.calculation_interval()
    # run.loop()
    # print(run.get_server_time())
    # print(run.fcoin.get_market_ticker(run.symbol)['data']['ticker'])
    # print(run.fcoin.get_server_time())
    # print(run.fcoin.get_trades(run.symbol))
    # data = run.fcoin.get_candle("M1", run.symbol, payload=json.dumps({'limit': 120}))
