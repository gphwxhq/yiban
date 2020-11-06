# coding=utf-8
import re,random
import requests, json, time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
from urllib import parse
from requests.exceptions import SSLError
from logger import logger

class yiban:
    def send(self, text,detail=""):
        #server酱发送模块
        if self.server_url=="":
            return
        data = {
            'text': text,
            'desp': detail
        }
        res=json.loads(requests.post(self.server_url, data=data).text)
        if(res['errno']!=0):
            logger.error("server酱报错：%s"%res['errmsg'])

    def encrypt_passwd(self, pwd):
        #密码加密
        PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
            MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAxbzZk3gEsbSe7A95iCIk
            59Kvhs1fHKE6zRUfOUyTaKd6Rzgh9TB/jAK2ZN7rHzZExMM9kw6lVwmlV0VabSmO
            YL9OOHDCiEjOlsfinlZpMZ4VHg8gkFoOeO4GvaBs7+YjG51Am6DKuJWMG9l1pAge
            96Uhx8xWuDQweIkjWFADcGLpDJJtjTcrh4fy8toE0/0zJMmg8S4RM/ub0q59+VhM
            zBYAfPmCr6YnEZf0QervDcjItr5pTNlkLK9E09HdKI4ynHy7D9lgLTeVmrITdq++
            mCbgsF/z5Rgzpa/tCgIQTFD+EPPB4oXlaOg6yFceu0XUQEaU0DvAlJ7Zn+VwPkkq
            JEoGudklNePHcK+eLRLHcjd9MPgU6NP31dEi/QSCA7lbcU91F3gyoBpSsp5m7bf5
            //OBadjWJDvl2KML7NMQZUr7YXqUQW9AvoNFrH4edn8d5jY5WAxWsCPQlOqNdybM
            vKF2jhjIE1fTWOzK+AvvFyNhxer5bWGU4S5LTr7QNXnvbngXCdkQfrcSn/ydQXP0
            vXfjf3NhpluFXqWe5qUFKXvjY6+PdrE/lvTmX4DdvUIu9NDa2JU9mhwAPPR1yjjp
            4IhgYOTQL69ZQcvy0Ssa6S25Xi3xx2XXbdx8svYcQfHDBF1daK9vca+YRX/DzXxl
            1S4uGt+FUWSwuFdZ122ZCZ0CAwEAAQ==
            -----END PUBLIC KEY-----
            '''
        cipher = PKCS1_v1_5.new(RSA.importKey(PUBLIC_KEY))
        cipher_text = base64.b64encode(cipher.encrypt(bytes(pwd, encoding="utf8")))
        return parse.quote(cipher_text.decode("utf-8"))

    def login(self):
        params = {
            "account": self.account,
            "ct": 2,
            "identify": 0,
            "v": "4.7.12",
            "passwd": self.encrypt_passwd(self.passwd)
        }
        HEADERS = {"Origin": "https://c.uyiban.com", "User-Agent": "yiban"}
        try:
            data = self.sess.get("https://mobile.yiban.cn/api/v2/passport/login", params=params, headers=HEADERS).text
        except SSLError:
            #解决 (Caused by SSLError(SSLError(1, '[SSL: DH_KEY_TOO_SMALL] dh key too small (_ssl.c:897)'),))
            requests.packages.urllib3.disable_warnings()
            requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
            try:
                requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += 'HIGH:!DH:!aNULL'
            except AttributeError:
                # no pyopenssl support used / needed / available
                pass
            data = self.sess.get("https://mobile.yiban.cn/api/v2/passport/login", params=params, headers=HEADERS,
                              verify=False).text
        data=json.loads(data)
        if data is not None and str(data["response"]) == "100":
            self.access_token = data["data"]["access_token"]
            self.name = data["data"]["user"]["name"]
            logger.info("登录成功，用户：%s"%self.name)
            return True
        else:
            return False

    def auth(self):
        #登录验证
        HEADERS = {"Origin": "https://c.uyiban.com", "User-Agent": "yiban"}
        location = self.sess.get('http://f.yiban.cn/iapp/index?act=iapp7463&v=%s' % self.access_token, headers=HEADERS,
                                 allow_redirects=False).headers["Location"]
        verifyRequest = re.findall(r"verify_request=(.*?)&", location)[0]
        # logger.info(verifyRequest)
        self.sess.get("https://api.uyiban.com/base/c/auth/yiban?verifyRequest=%s&CSRF=%s" % (verifyRequest, self.csrf),
                      cookies=self.cookie, headers=self.headers)

    def get_tasklist(self):
        cur = time.time()
        starttime = time.strftime("%Y-%m-%d", time.localtime(cur - 604800))  # 往前推7天
        # starttime 形式='2020-10-01'
        endtime = time.strftime("%Y-%m-%d", time.localtime(cur + 86400))  # 往后推一天，解决服务器时区问题
        url = 'https://api.uyiban.com/officeTask/client/index/uncompletedList?StartTime={}%2000%3A00&EndTime={}%2023%3A59&CSRF={}'.format(
            starttime, endtime, self.csrf)
        for i in range(self.max_try_time):
            a = json.loads(self.sess.get(url, headers=self.headers, cookies=self.cookie).text)  # 获取任务列表
            if a['code'] != 0:
                logger.error(a['msg'])
                self.send(a['msg'])
                logger.info("运行结束")
                exit()
            data = a['data']
            if len(data) == 0:
                if i==0:
                    logger.info('没有任务')
                    self.send('没有任务')
                    logger.info("运行结束")
                    exit()
                else:
                    logger.info('复检结束，无遗漏任务')
                    return
            self.taskidlist = []
            self.titlelist = []
            for item in data:  # 筛选有效任务
                if cur > int(item['StartTime']):
                    self.taskidlist.append(item['TaskId'])
                    self.titlelist.append(item['Title'])
            if len(self.taskidlist)==0:
                if i==0:
                    logger.info('有任务但未到执行时间')
                    self.send('有任务但未到执行时间')
                    logger.info("运行结束")
                    exit()
                else:
                    logger.info('复检结束，无遗漏任务')
                    return
            if(i>0):
                logger.info("检测到遗漏任务，重新执行")
                self.finish += "检测到遗漏任务，重新执行\n"
            self.post_data()
        logger.error("已尝试至最大次数，可能打卡失败")
        self.finish += "已尝试至最大次数，可能打卡失败\n"


    def post_data(self):
        self.finish+= '结果：\n'
        for iter in range(len(self.taskidlist)):
            taskid = self.taskidlist[iter]
            title = self.titlelist[iter]
            url = 'https://api.uyiban.com/officeTask/client/index/detail?TaskId=%s&CSRF=%s' % (taskid, self.csrf)
            b = json.loads(self.sess.get(url, headers=self.headers, cookies=self.cookie).text)  # 获取参数
            # 表单数据：体温，本人是否有可疑症状，同住人是否有可疑症状
            temper = round(random.uniform(36, 36.6), 1)  # 生成区间位于36-36.6带有一位小数的体温
            morning_data = {
                'data': '{"ed9ff15f7155ed96682309ea8f865c94":"%s°","adbd34269e63dab3ceda0a9debb57733":"无以上症状","8525b81624577db90dd509b4301d1d21":"无以上症状"}' % temper,
                'extend': '{"TaskId":"%s","title":"任务信息","content":[{"label":"任务名称","value":"%s"},{"label":"发布机构","value":"学生工作处"}]}' % (
                taskid, title)
            }
            noon_data = {
                'data': '{"ed9ff15f7155ed96682309ea8f865c94":"%s°","adbd34269e63dab3ceda0a9debb57733":"无以上症状","9a9c2732741377699aa2158cb58e54f2":"无以上症状"}' % temper,
                'extend': '{"TaskId":"%s","title":"任务信息","content":[{"label":"任务名称","value":"%s"},{"label":"发布机构","value":"学生工作处"}]}' % (
                taskid, title)
            }
            url2 = 'https://api.uyiban.com/workFlow/c/my/apply/%s?CSRF=%s' % (b['data']['WFId'], self.csrf)
            if title[-4:-2] == "晨检":
                c = self.sess.post(url2, headers=self.headers, cookies=self.cookie, data=morning_data).text
            elif title[-4:-2] == "午检":
                c = self.sess.post(url2, headers=self.headers, cookies=self.cookie, data=noon_data).text
            else:
                logger.error(title + '晨检午检判断出错')
                self.send(title + '晨检午检判断出错')
                continue
            c = json.loads(c)
            if c['data'] != '':
                self.finish += '%s打卡成功,' % title
                logger.info('%s打卡成功' % title)
            else:
                self.finish += '%s打卡失败,'% title
                logger.error('%s打卡失败' % title)
            time.sleep(5)

    def start(self):
        if not self.login():
            logger.error('登录失败')
            self.send('登录失败')
            logger.info("运行结束")
            exit()
        self.auth()
        self.get_tasklist()
        self.send('%s打卡结果'%self.name,self.finish)
        logger.info("运行结束")


    def start_night_attendance(self):
        if not self.login():
            logger.error('登录失败')
            self.send('登录失败')
            logger.info("运行结束")
            exit()
        self.auth()
        check_url='https://api.uyiban.com/nightAttendance/student/index/signPosition?CSRF=%s'%self.csrf
        post_url = 'https://api.uyiban.com/nightAttendance/student/index/signIn?CSRF=%s' % self.csrf
        for i in range(self.max_try_time):
            res=json.loads(self.sess.get(check_url, headers=self.headers, cookies=self.cookie).text)
            if res['data']['State']==3:
                if i==0:
                    self.send('之前已完成晚点签到')
                    logger.info("之前已完成晚点签到")
                else:
                    self.send('晚检签到成功')
                    logger.info("晚检签到成功")
                logger.info("运行结束")
                exit()
            add1 = round(random.uniform(111.6987, 111.7011), 4)
            add2=round(random.uniform(40.8140, 40.8159), 4)
            data={
                'Code':'',
                'SignInfo':'{"Reason":"","AttachmentFileName":"","LngLat":"%s,%s","Address":"内蒙古自治区 呼和浩特市 赛罕区 金宇巷 109号 靠近内蒙古大学(东校区) "}'% (add1, add2),
                'OutState':1
            }
            res = json.loads(self.sess.post(post_url, headers=self.headers, cookies=self.cookie,data=data).text)
            if res['code']!=0:
                logger.error('晚点签到失败，错误：%s'%res['msg'])
                self.send('晚点签到失败，错误：%s'%res['msg'])
                logger.info("运行结束")
                exit()
            time.sleep(5)
        logger.error('晚点签到:已尝试至最大次数，可能签到失败')
        self.send('晚点签到:已尝试至最大次数，可能签到失败')
        logger.info("运行结束")

    def __init__(self,account,pswd,server_url=""):
        self.sess = requests.session()
        self.account = account
        self.passwd = pswd
        self.csrf = 'a6c72b556f582b4cc1a557cf80ca7cc7'
        self.cookie={'csrf_token':self.csrf}
        self.headers = {
            'origin': 'https://app.uyiban.com',
            'referer': 'https://app.uyiban.com/',
            'Host': 'api.uyiban.com',
            'user-agent': 'yiban',
        }
        self.max_try_time=3
        self.server_url=server_url
        self.finish=""
