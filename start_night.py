# coding=utf-8
from Utils import Yiban
import random

if __name__ == '__main__':
    yb = Yiban('',  # 账号
               '',  # 密码
               '',  # server酱url，没有不填
               )
    lng = round(random.uniform(0, 0), 4)
    lat = round(random.uniform(0, 0), 4)
    params = {
        'path': '',#图片地址，校内签到留空
        'reason': '',#原因，校内签到留空
        'lnglat': '%s,%s'%(lng,lat),#经纬度
        'address': ''#地址
    }
    yb.start_night_attendance(params)
