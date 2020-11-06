# coding=utf-8
#晚签到
from work import yiban

if __name__ == '__main__':
    yb = yiban('',#账号
               '',#密码
               '')#server酱url，没有不填
    yb.start_night_attendance()