# coding=utf-8
import re, random
import requests, json, time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
from logger import logger


class yiban:
    def send(self, text, detail=""):
        # server酱发送模块
        if self.server_url == "":
            return
        data = {
            'text': text,
            'desp': detail
        }
        res = requests.post(self.server_url, data=data).json()
        if (res['errno'] != 0):
            logger.error("server酱报错：%s" % res['errmsg'])

    def encrypt_passwd(self, pwd):
        # 密码加密
        PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
            MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA6aTDM8BhCS8O0wlx2KzA
            Ajffez4G4A/QSnn1ZDuvLRbKBHm0vVBtBhD03QUnnHXvqigsOOwr4onUeNljegIC
            XC9h5exLFidQVB58MBjItMA81YVlZKBY9zth1neHeRTWlFTCx+WasvbS0HuYpF8+
            KPl7LJPjtI4XAAOLBntQGnPwCX2Ff/LgwqkZbOrHHkN444iLmViCXxNUDUMUR9bP
            A9/I5kwfyZ/mM5m8+IPhSXZ0f2uw1WLov1P4aeKkaaKCf5eL3n7/2vgq7kw2qSmR
            AGBZzW45PsjOEvygXFOy2n7AXL9nHogDiMdbe4aY2VT70sl0ccc4uvVOvVBMinOp
            d2rEpX0/8YE0dRXxukrM7i+r6lWy1lSKbP+0tQxQHNa/Cjg5W3uU+W9YmNUFc1w/
            7QT4SZrnRBEo++Xf9D3YNaOCFZXhy63IpY4eTQCJFQcXdnRbTXEdC3CtWNd7SV/h
            mfJYekb3GEV+10xLOvpe/+tCTeCDpFDJP6UuzLXBBADL2oV3D56hYlOlscjBokNU
            AYYlWgfwA91NjDsWW9mwapm/eLs4FNyH0JcMFTWH9dnl8B7PCUra/Lg/IVv6HkFE
            uCL7hVXGMbw2BZuCIC2VG1ZQ6QD64X8g5zL+HDsusQDbEJV2ZtojalTIjpxMksbR
            ZRsH+P3+NNOZOEwUdjJUAx8CAwEAAQ==
            -----END PUBLIC KEY-----'''
        cipher = PKCS1_v1_5.new(RSA.importKey(PUBLIC_KEY))
        cipher_text = base64.b64encode(cipher.encrypt(bytes(pwd, encoding="utf8")))
        return cipher_text.decode("utf-8")

    def login(self):
        # 登录
        data = {
            # 'app':1,
            # 'sig':'7643afdb3d9cce3f',
            'ct': 2,
            'password': self.encrypt_passwd(self.passwd),
            # FwGeug1brJxUETXbs5wIfBkQdw+IXwXpGsGy+2eHnhOLtxHQpfcvLIc0QOxa1EjQNivTS7vtVihGMd9y6x0QojPwf88M0gC+tG1PPgmoVBuiMtrAPBevs8trqnjVW896RuZaTeytC0jybncZTRAXy4OHCJVZkc2J1cx0SfdxjBYZNXrqXIAK1G1lGrZ1KJiMnH/hmcl8LNdzhU0iDrp+ZqZaivMsql2ljDy0BlP4aiBqF3obmjalMl9IAjZ7uPvdxAp2pD+vxN4DDXsFJnGBGwirPaI6ejbC73brMcO6UJ++WUtvRlhOYIyuKGScIOz+O4sOl+bIPCGPLQB5rT+SHbAJG+xBNoAJNHOfnfgrpj0lbuZVRQgIqEE2osX6JUZyhjW7iC0nGRT/bf/SNl5Z9PQl+eiVXLK1AknlHyu6e4TfRha/CVHrQi4TxfoARcYRsT9OTsRtEjh51v6gJYFX7Rfto32+/7oV6R43lFj7VTDBqJ03pm05d/G3skWvN7zVpYHCOSCBJvca9OHVvOD0onC70PskZ7v4wNgMa18Sc0X9kLvH9DzdJ73+lTBi18LhRXCVJtjOJ2nwcILqycYsyBmZgaL+8NE93QhspAbG0cRSxpePs4xtgizzeDAmYnt849xO1jgky8r9ABThkwuuzyGv18FnD+NYXFa/iSPI71M=
            'identify': random.sample('zyxwvutsrqponmlkjihgfedcba0123456789', 16),
            # '19b333ab697be0b9',
            # 'v' : '5.0',
            "mobile": self.account,
            # "sversion":29,
        }
        HEADERS = {"AppVersion": "5.0", "User-Agent": "yiban"}
        res = self.sess.post("https://m.yiban.cn/api/v4/passport/login", data=data, headers=HEADERS).json()
        if res is not None and str(res["response"]) == "100":
            self.access_token = res["data"]["access_token"]
            self.name = res["data"]["user"]["name"]
            logger.info("登录成功，用户：%s" % self.name)
            return True
        else:
            return False

    def auth(self):
        # 登录验证
        HEADERS = {"logintoken": self.access_token, "Host": "f.yiban.cn", "User-Agent": "yiban"}
        location = self.sess.get('http://f.yiban.cn/iapp/index?act=iapp7463', headers=HEADERS,
                                 allow_redirects=False)
        if "Location" in location.headers.keys():
            location = location.headers["Location"]
            verifyRequest = re.findall(r"verify_request=(.*?)&", location)[0]
        else:
            verifyRequest = ''
        self.sess.get("https://api.uyiban.com/base/c/auth/yiban?verifyRequest=%s&CSRF=%s" % (verifyRequest, self.csrf),
                      cookies=self.cookie, headers=self.headers)

    def switchForm(self, data):
        # 选择打卡表单
        with open('list.json', 'r', encoding='utf-8') as f:
            t = f.read()
            oform = json.loads(t)
        self.postForm = {}
        label = [item['props']['label'] for item in data]
        for form in oform:
            if label == list(oform[form].keys()):
                for item in data:
                    formValue = oform[form][item['props']['label']]
                    if '体温' in item['props']['label']:
                        temper = round(random.uniform(36.1, 36.6), 1)
                        if formValue == '°':
                            self.postForm[item['id']] = "%s°" % temper
                        else:
                            self.postForm[item['id']] = "%s" % temper
                    else:
                        self.postForm[item['id']] = formValue
                break
        if not self.postForm:
            return False
        return True

    def get_tasklist(self):
        # 获取任务列表
        cur = time.time()
        starttime = time.strftime("%Y-%m-%d", time.localtime(cur - 86400 * 7))  # 往前推7天
        # starttime 形式='2020-10-01'
        endtime = time.strftime("%Y-%m-%d", time.localtime(cur + 86400))  # 往后推一天，解决服务器时区问题
        url = 'https://api.uyiban.com/officeTask/client/index/uncompletedList?StartTime={}%2000%3A00&EndTime={}%2023%3A59&CSRF={}'.format(
            starttime, endtime, self.csrf)
        for i in range(self.max_try_time):
            res = self.sess.get(url, headers=self.headers, cookies=self.cookie).json()  # 获取任务列表
            if res['code'] != 0:
                logger.error(res['msg'])
                time.sleep(5)
                continue
            data = res['data']
            if len(data) == 0:
                if i == 0:
                    logger.info('没有任务')
                    self.send('%s没有任务' % self.name, "没有任务")
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
            if len(self.taskidlist) == 0:
                if i == 0:
                    logger.info('未到执行时间')
                    self.send('%s没有任务' % self.name, '未到执行时间')
                    logger.info("运行结束")
                    exit()
                else:
                    logger.info('复检结束，无遗漏任务')
                    return
            if (i > 0):
                logger.info("检测到遗漏任务，重新执行")
                self.finish += "检测到遗漏任务，重新执行\n\n"
            self.post_data()
        logger.error("已尝试至最大次数，可能打卡失败")
        self.finish += "已尝试至最大次数，可能打卡失败\n\n"

    def post_data(self):
        # 提交打卡
        self.finish += '结果：\n\n'
        for iter in range(len(self.taskidlist)):
            taskid = self.taskidlist[iter]
            title = self.titlelist[iter]
            param_url = 'https://api.uyiban.com/officeTask/client/index/detail?TaskId=%s&CSRF=%s' % (taskid, self.csrf)
            param = self.sess.get(param_url, headers=self.headers, cookies=self.cookie).json()  # 获取参数
            detail_url = 'https://api.uyiban.com/workFlow/c/my/form/%s?CSRF=%s' % (param['data']['WFId'], self.csrf)
            detail = self.sess.get(detail_url, headers=self.headers, cookies=self.cookie).json()
            if not self.switchForm(detail['data']['Form']):
                logger.error(title + '不在表单库中')
                self.send('%s打卡失败' % self.name, '%s不在表单库中' % title)
                continue
            url2 = 'https://api.uyiban.com/workFlow/c/my/apply/%s?CSRF=%s' % (param['data']['WFId'], self.csrf)
            data = {
                'data': json.dumps(self.postForm),
                'extend': '{"TaskId":"%s","title":"任务信息","content":[{"label":"任务名称","value":"%s"},{"label":"发布机构","value":"%s"},{"label":"发布人","value":"%s"}]}' % (
                taskid, title, param['data']['PubOrgName'], param['data']['PubPersonName'])
            }
            res = self.sess.post(url2, headers=self.headers, cookies=self.cookie, data=data).json()
            if res['msg'] == '':
                self.finish += '%s打卡成功\n\n' % title
                logger.info('%s打卡成功' % title)
            else:
                self.finish += '%s打卡失败,%s\n\n' % (title, res['msg'])
                logger.error('%s打卡失败,%s' % (title, res['msg']))
            time.sleep(5)

    def start(self):
        if not self.login():
            logger.error(self.account + ':' + '登录失败')
            self.send(self.account + ':' + '登录失败')
            logger.info("运行结束")
            exit()
        self.auth()
        self.get_tasklist()
        self.send('%s打卡结果' % self.name, self.finish)
        logger.info("运行结束")

    def start_night_attendance(self,params):
        if not self.login():
            logger.error(self.account + ':' + '登录失败')
            self.send(self.account + ':' + '登录失败')
            logger.info("运行结束")
            return
        self.auth()
        check_url = 'https://api.uyiban.com/nightAttendance/student/index/signPosition?CSRF=%s' % self.csrf
        post_url = 'https://api.uyiban.com/nightAttendance/student/index/signIn?CSRF=%s' % self.csrf
        res = self.sess.get(check_url, headers=self.headers, cookies=self.cookie).json()
        state = res['data']['State']
        if state != 0:
            if state == 3:
                self.send('%s晚检打卡完成' % self.name, '之前已完成晚点签到')
                logger.info("之前已完成晚点签到")
            else:
                logger.info('晚点签到:%s' % res['data']['Msg'])
                self.send('%s晚检打卡失败' % self.name, res['data']['Msg'])
            return
        if params['path']=='':
            data = {
                'Code': '',
                'SignInfo': '{"Reason":"","AttachmentFileName":"","LngLat":"%s","Address":"%s"}' % (params['lnglat'],params['address']),
                'OutState': 1
            }
        else:
            import os.path
            try:
                size = os.path.getsize(params['path'])
            except FileNotFoundError:
                logger.error('晚点签到失败，未找到照片')
                self.send('%s晚检签到失败' % self.name,'未找到照片')
                return
            upload = self.sess.get(
                'https://api.uyiban.com/nightAttendance/student/index/uploadUri?name=yiban_camera1.jpg&type=image%2Fjpeg&size=' + str(
                    size) + '&CSRF=' + self.csrf, headers=self.headers, cookies=self.cookie).json()
            upload_url = upload['data']['signedUrl']
            fileName = upload['data']['AttachmentFileName']
            headers = {
                'Host': 'oss.uyiban.cn',
                'content-type': 'image/jpeg',
                'connection': 'close',
                'referer': 'https://app.uyiban.com/nightattendance/student/',
                'user-agent': 'yiban',
                'origin': 'https://app.uyiban.com'
            }
            self.sess.put(upload_url, data=open(params['path'], 'rb').read(), headers=headers)
            # t = self.sess.get('https://api.uyiban.com/nightAttendance/student/index/downloadUri?AttachmentFileName=%s&CSRF=%s' % (fileName, self.csrf), headers=self.headers, cookies=self.cookie).json()
            # t3=self.sess.get(t['data'],headers=headers3)
            data = {
                'AttachmentFileName': '',
                'OutState': 2,
                'Code': '',
                'PhoneModel': '',
                'SignInfo': '{"Reason":"%s","AttachmentFileName":"%s","LngLat":"%s","Address":"%s"}' % (
                    params['reason'], fileName, params['lnglat'], params['address'])
            }
        res = self.sess.post(post_url, headers=self.headers, cookies=self.cookie, data=data).json()
        if res['code'] != 0:
            logger.error('晚点签到失败，错误：%s' % res['msg'])
            self.send('%s晚检签到失败' % self.name, res['msg'])
        else:
            self.send('%s晚检打卡成功' % self.name, '晚检签到成功')
            logger.info("晚检签到成功")

    def __init__(self, account, pswd, server_url=""):
        self.sess = requests.session()
        self.account = account
        self.passwd = pswd
        self.csrf = ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba0123456789', 32))
        self.cookie = {'csrf_token': self.csrf}
        self.headers = {
            'origin': 'https://app.uyiban.com',
            'referer': 'https://app.uyiban.com/',
            'Host': 'api.uyiban.com',
            'user-agent': 'yiban',
        }
        self.max_try_time = 3
        self.server_url = server_url
        self.finish = ""
