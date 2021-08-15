# coding=utf-8
from utils import yiban

if __name__ == '__main__':
    yb = yiban('',  # 账号
               '',  # 密码
               '',  # server酱url，没有不填
               )
    # lng = round(random.uniform(111.6987, 111.7011), 4)
    # lat = round(random.uniform(40.8140, 40.8159), 4)
    params = {
        'path': 'photo.jpg',#图片地址，应为jpg，校内签到留空
        'reason': ',',#原因，校内签到留空
        'lnglat': '',#经纬度
        'address': ''#地址
    }
    yb.start_night_attendance(params)
