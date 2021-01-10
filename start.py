# coding=utf-8
#早中打卡
from work import yiban

if __name__ == '__main__':
    yb = yiban('',  # 账号
               '',  # 密码
               '',# server酱url，没有不填
               ''# 假期模式需填写打卡地址 格式："内蒙古自治区","呼和浩特市","赛罕区"
               )
    yb.start()