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
        requests.post(self.server_url, data=data)

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

    def start(self):
        if not self.login():
            logger.info('登录失败')
            self.send('登录失败')
            exit()
        self.auth()
        cur=time.time()
        starttime=time.strftime("%Y-%m-%d", time.localtime(cur-604800))#往前推7天
        # starttime 形式='2020-10-01'
        endtime = time.strftime("%Y-%m-%d", time.localtime(cur+86400))#往后推一天，解决服务器时区问题
        url='https://api.uyiban.com/officeTask/client/index/uncompletedList?StartTime={}%2000%3A00&EndTime={}%2023%3A59&CSRF={}'.format(starttime,endtime,self.csrf)
        a = json.loads(self.sess.get(url,headers=self.headers,cookies=self.cookie).text)#获取任务列表
        if a['code'] != 0:
            logger.info(a['msg'])
            self.send(a['msg'])
            exit()
        data = a['data']
        if len(data) == 0:
            logger.info('没有任务')
            self.send('没有任务')
            exit()
        taskidlist=[]
        titlelist=[]
        for item in data:#筛选有效任务
            if cur>int(item['StartTime']):
                taskidlist.append(item['TaskId'])
                titlelist.append(item['Title'])
        if len(taskidlist)==0:
            logger.info('有任务但未到执行时间')
            self.send('有任务但未到执行时间')
            exit()
        finish='结果：\n'
        for iter in range(len(taskidlist)):
            taskid = taskidlist[iter]
            title = titlelist[iter]
            url = 'https://api.uyiban.com/officeTask/client/index/detail?TaskId=%s&CSRF=%s'%(taskid,self.csrf)
            b = json.loads(self.sess.get(url, headers=self.headers,cookies=self.cookie).text)#获取参数
            #表单数据：体温，本人是否有可疑症状，同住人是否有可疑症状
            temper = round(random.uniform(36, 36.6), 1) #生成区间位于36-36.6带有一位小数的体温
            morning_data = {
                'data': '{"ed9ff15f7155ed96682309ea8f865c94":"%s°","adbd34269e63dab3ceda0a9debb57733":"无以上症状","8525b81624577db90dd509b4301d1d21":"无以上症状"}'%temper,
                'extend': '{"TaskId":"%s","title":"任务信息","content":[{"label":"任务名称","value":"%s"},{"label":"发布机构","value":"学生工作处"}]}'%(taskid,title)
            }
            noon_data = {
                'data': '{"ed9ff15f7155ed96682309ea8f865c94":"%s°","adbd34269e63dab3ceda0a9debb57733":"无以上症状","9a9c2732741377699aa2158cb58e54f2":"无以上症状"}'%temper,
                'extend': '{"TaskId":"%s","title":"任务信息","content":[{"label":"任务名称","value":"%s"},{"label":"发布机构","value":"学生工作处"}]}'%(taskid,title)
            }
            url2 = 'https://api.uyiban.com/workFlow/c/my/apply/%s?CSRF=%s'%(b['data']['WFId'],self.csrf)
            if title[-4:-2] == "晨检":
                c = self.sess.post(url2, headers=self.headers,cookies=self.cookie, data=morning_data).text
            elif title[-4:-2] == "午检":
                c = self.sess.post(url2, headers=self.headers,cookies=self.cookie, data=noon_data).text
            else:
                logger.info(title+'晨检午检判断出错')
                self.send(title+'晨检午检判断出错')
                continue
            c = json.loads(c)
            if c['data'] != '':
                finish+=title+'打卡成功\n'
                logger.info(title + '打卡成功')
            else:
                finish += title + '打卡失败\n'
                logger.info(title + '打卡失败')
            time.sleep(5)
        # logger.info(finish)
        logger.info("运行结束")
        self.send('%s打卡结果'%self.name,finish)

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
        self.server_url=server_url
