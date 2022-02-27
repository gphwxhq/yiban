# coding=utf-8
import re, random
import requests, json, time

from ConfigHelper import *
from Encryptions import *
from Logger import logger
from requests.adapters import HTTPAdapter


class Yiban():
    def __send(self, text, detail=""):
        # server酱发送模块
        if self.__server_url == "":
            return
        data = {
            'title': text,
            'desp': detail
        }
        requests.post("https://sctapi.ftqq.com/SCT59032TwP7RJPevoSQrl0RCclKuAEM4.send",
                      data=data)


    def __login(self):
        # 登录
        data = {
            # 'app':1,
            # 'sig':'7643afdb3d9cce3f',
            'ct': 2,
            'password':encrypt_passwd(self.__passwd),
            # FwGeug1brJxUETXbs5wIfBkQdw+IXwXpGsGy+2eHnhOLtxHQpfcvLIc0QOxa1EjQNivTS7vtVihGMd9y6x0QojPwf88M0gC+tG1PPgmoVBuiMtrAPBevs8trqnjVW896RuZaTeytC0jybncZTRAXy4OHCJVZkc2J1cx0SfdxjBYZNXrqXIAK1G1lGrZ1KJiMnH/hmcl8LNdzhU0iDrp+ZqZaivMsql2ljDy0BlP4aiBqF3obmjalMl9IAjZ7uPvdxAp2pD+vxN4DDXsFJnGBGwirPaI6ejbC73brMcO6UJ++WUtvRlhOYIyuKGScIOz+O4sOl+bIPCGPLQB5rT+SHbAJG+xBNoAJNHOfnfgrpj0lbuZVRQgIqEE2osX6JUZyhjW7iC0nGRT/bf/SNl5Z9PQl+eiVXLK1AknlHyu6e4TfRha/CVHrQi4TxfoARcYRsT9OTsRtEjh51v6gJYFX7Rfto32+/7oV6R43lFj7VTDBqJ03pm05d/G3skWvN7zVpYHCOSCBJvca9OHVvOD0onC70PskZ7v4wNgMa18Sc0X9kLvH9DzdJ73+lTBi18LhRXCVJtjOJ2nwcILqycYsyBmZgaL+8NE93QhspAbG0cRSxpePs4xtgizzeDAmYnt849xO1jgky8r9ABThkwuuzyGv18FnD+NYXFa/iSPI71M=
            'identify': random.sample('zyxwvutsrqponmlkjihgfedcba0123456789', 16),
            # '19b333ab697be0b9',
            # 'v' : '5.0',
            "mobile": self.__account,
            # "sversion":29,
        }
        HEADERS = {"AppVersion": "5.0", "User-Agent": "yiban"}
        res = self.__sess.post("https://m.yiban.cn/api/v4/passport/login", data=data, headers=HEADERS).json()
        if res is not None and str(res["response"]) == "100":
            self.access_token = res["data"]["access_token"]
            self.name = res["data"]["user"]["name"]
            logger.info("登录成功，用户：%s" % self.name)
            return True
        else:
            return False

    def __auth(self):
        # 登录验证
        HEADERS = {"logintoken": self.access_token, "Host": "f.yiban.cn", "User-Agent": "yiban"}
        location = self.__sess.get('http://f.yiban.cn/iapp/index?act=iapp7463', headers=HEADERS,
                                   allow_redirects=False)
        if "Location" in location.headers.keys():
            location = location.headers["Location"]
            verifyRequest = re.findall(r"verify_request=(.*?)&", location)[0]
        else:
            verifyRequest = ''
        self.__sess.get("https://api.uyiban.com/base/c/auth/yiban?verifyRequest=%s&CSRF=%s" % (verifyRequest, self.__csrf),
                        cookies=self.__cookie, headers=self.__headers)


    # 选择打卡表单
    def __switchForm(self, data):
        #读取配置文件
        oform = configLoader()

        self.postForm = {}
        #提取服务器表项
        label = [item['props']['label'] for item in data if 'label' in item['props'].keys()]

        #生成提交表单
        for form in oform:
            #寻找与服务器匹配的本地表单
            if label == list(oform[form].keys()):
                #寻找本地表项
                for item in data:
                    #筛选无用表项
                    if not "label" in item['props']:
                        continue
                    #本地表项值
                    formValue = oform[form][item['props']['label']]
                    #填写体温表项
                    if '体温' in item['props']['label']:
                        temper = round(random.uniform(36.1, 36.6), 1)
                        if formValue == '°':
                            self.postForm[item['id']] = "%s°" % temper
                        else:
                            self.postForm[item['id']] = "%s" % temper
                    #其他根据本地表单填写
                    else:
                        self.postForm[item['id']] = formValue
                break
        #没有匹配的本地表单
        if not self.postForm:
            return False
        return True

    def __get_tasklist(self,dealType):
        # 获取任务列表
        cur = time.time()
        if self.__starttime== "" and self.__endtime== "":
            self.__starttime = time.strftime("%Y-%m-%d", time.localtime(cur - 86400 * 7))  # 往前推7天
            self.__endtime = time.strftime("%Y-%m-%d", time.localtime(cur + 86400))  # 往后推一天，解决服务器时区问题
        url = 'https://api.uyiban.com/officeTask/client/index/uncompletedList?StartTime={}%2000%3A00&EndTime={}%2023%3A59&CSRF={}'.format(
            self.__starttime, self.__endtime, self.__csrf)
        for i in range(self.__max_try_time):
            res = self.__sess.get(url, headers=self.__headers, cookies=self.__cookie).json()  # 获取任务列表
            if res['code'] != 0:
                logger.error(res['msg'])
                time.sleep(5)
                continue
            data = res['data']
            if len(data) == 0:
                if i == 0:
                    logger.info('没有任务')
                    self.__send('%s没有任务' % self.name, "没有任务")
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
                    self.__send('%s没有任务' % self.name, '未到执行时间')
                    logger.info("运行结束")
                    exit()
                else:
                    logger.info('复检结束，无遗漏任务')
                    return
            if (i > 0):
                logger.info("检测到遗漏任务，重新执行")
                self.__finish += "检测到遗漏任务，重新执行\n\n"
            if(dealType=="post"):
                self.__post_data()
            elif dealType=="extract":
                return
            else:
                logger.error('参数错误')
                exit()
        logger.error("已尝试至最大次数，可能打卡失败")
        self.__finish += "已尝试至最大次数，可能打卡失败\n\n"

    def __post_data(self):
        # 提交打卡
        self.__finish += '结果：\n\n'
        for iter in range(len(self.taskidlist)):
            taskid = self.taskidlist[iter]
            title = self.titlelist[iter]
            param_url = 'https://api.uyiban.com/officeTask/client/index/detail?TaskId=%s&CSRF=%s' % (taskid, self.__csrf)
            param = self.__sess.get(param_url, headers=self.__headers, cookies=self.__cookie).json()  # 获取参数
            detail_url = 'https://api.uyiban.com/workFlow/c/my/form/%s?CSRF=%s' % (param['data']['WFId'], self.__csrf)
            detail = self.__sess.get(detail_url, headers=self.__headers, cookies=self.__cookie).json()
            if not self.__switchForm(detail['data']['Form']):
                logger.error(title + '不在表单库中')
                self.__finish+= '%s不在表单库中\n\n' % title
                continue
            url2 = 'https://api.uyiban.com/workFlow/c/my/apply?CSRF=%s' %  self.__csrf
            data = {
                "WFId":param['data']['WFId'],
                'Data': json.dumps(self.postForm, ensure_ascii=False),
                'Extend': json.dumps({"TaskId":taskid,
                                      "title":"任务信息",
                                      "content":[
                                          {"label":"任务名称","value":title},
                                          {"label":"发布机构","value":param['data']['PubOrgName']},
                                          {"label":"发布人","value":param['data']['PubPersonName']}
                                      ]},
                                     ensure_ascii=False)
            }
            data = {'Str': aes_encrypt(json.dumps(data, ensure_ascii=False))}
            res = self.__sess.post(url2, headers=self.__headers, cookies=self.__cookie, data=data).json()
            if res['msg'] == '':
                self.__finish += '%s打卡成功\n\n' % title
                logger.info('%s打卡成功' % title)
            else:
                self.__finish += '%s打卡失败,%s\n\n' % (title, res['msg'])
                logger.error('%s打卡失败,%s' % (title, res['msg']))
            time.sleep(5)

    def start(self):
        if not self.__login():
            logger.error(self.__account + ':' + '登录失败')
            self.__send(self.__account + ':' + '登录失败')
            logger.info("运行结束")
            exit()
        self.__auth()
        self.__get_tasklist("post")
        self.__send('%s打卡结果' % self.name, self.__finish)
        logger.info("运行结束")

    def start_night_attendance(self,params):
        if not self.__login():
            logger.error(self.__account + ':' + '登录失败')
            self.__send(self.__account + ':' + '登录失败')
            logger.info("运行结束")
            return
        self.__auth()
        check_url = 'https://api.uyiban.com/nightAttendance/student/index/signPosition?CSRF=%s' % self.__csrf
        post_url = 'https://api.uyiban.com/nightAttendance/student/index/signIn?CSRF=%s' % self.__csrf
        res = self.__sess.get(check_url, headers=self.__headers, cookies=self.__cookie).json()
        state = res['data']['State']
        if state != 0:
            if state == 3:
                self.__send('%s晚检打卡完成' % self.name, '之前已完成晚点签到')
                logger.info("之前已完成晚点签到")
                logger.info("运行结束")
            else:
                logger.info('晚点签到:%s' % res['data']['Msg'])
                self.__send('%s晚检打卡失败' % self.name, res['data']['Msg'])
                logger.info("运行结束")
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
                self.__send('%s晚检签到失败' % self.name, '未找到照片')
                logger.info("运行结束")
                return
            upload = self.__sess.get(
                'https://api.uyiban.com/nightAttendance/student/index/uploadUri?name=yiban_camera1.jpg&type=image%2Fjpeg&size=' + str(
                    size) + '&CSRF=' + self.__csrf, headers=self.__headers, cookies=self.__cookie).json()
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
            self.__sess.put(upload_url, data=open(params['path'], 'rb').read(), headers=headers)
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
        res = self.__sess.post(post_url, headers=self.__headers, cookies=self.__cookie, data=data).json()
        if res['code'] != 0:
            logger.error('晚点签到失败，错误：%s' % res['msg'])
            self.__send('%s晚检签到失败' % self.name, res['msg'])
        else:
            self.__send('%s晚检打卡成功' % self.name, '晚检签到成功')
            logger.info("晚检签到成功")
        logger.info("运行结束")

    def doExtract(self):
        if not self.__login():
            logger.error(self.__account + ':' + '登录失败')
            self.__send(self.__account + ':' + '登录失败')
            logger.info("运行结束")
            exit()
        self.__auth()
        self.__get_tasklist("extract")

        # 读取配置文件
        oform = configLoader()
        addNum = 0

        for iter in range(len(self.taskidlist)):
            isExist=False
            hasDu=False

            taskid = self.taskidlist[iter]
            title = self.titlelist[iter]+'模板'

            param_url = 'https://api.uyiban.com/officeTask/client/index/detail?TaskId=%s&CSRF=%s' % (taskid, self.__csrf)
            param = self.__sess.get(param_url, headers=self.__headers, cookies=self.__cookie).json()  # 获取参数

            detail_url = 'https://api.uyiban.com/workFlow/c/my/form/%s?CSRF=%s' % (param['data']['WFId'], self.__csrf)
            detail = self.__sess.get(detail_url, headers=self.__headers, cookies=self.__cookie).json()['data']['Form']

            # 提取服务器表项
            labels =[]
            types=[]
            for item in detail:
                if 'label' in item['props'].keys():
                    if '体温' in item['props']['label']:
                        if '°' in ''.join(item['props']['options']):
                            hasDu=True
                    labels.append(item['props']['label'])
                    types.append(item['component'])

            # 查重
            for form in oform:
                # 寻找与服务器匹配的本地表单
                if labels == list(oform[form].keys()):
                    isExist=True
                    break
            if isExist:
                continue
            # 不存在
            addNum=addNum+1
            newDict={}
            for label,type in zip(labels,types):
                if '体温' in label and hasDu:
                    newDict[label]="°"
                elif type=="TreeSelect":
                    newDict[label]=[]
                else:
                    newDict[label]=""
            oform[title]=newDict
            logger.info("已添加： "+title)
        configWriter(oform)
        logger.info("添加模板%s个!"%addNum)
        logger.info("运行结束")




    def __init__(self, account, pswd, server_url=""):
        self.__sess = requests.session()
        self.__sess.mount('http://', HTTPAdapter(max_retries=3))
        self.__sess.mount('https://', HTTPAdapter(max_retries=3))

        self.__account = account
        self.__passwd = pswd
        self.__csrf = ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba0123456789', 32))
        self.__cookie = {'csrf_token': self.__csrf}
        self.__headers = {
            'origin': 'https://app.uyiban.com',
            'referer': 'https://app.uyiban.com/',
            'Host': 'api.uyiban.com',
            'user-agent': 'yiban',
        }
        self.__max_try_time = 3
        self.__server_url = server_url
        self.__finish = ""

        # starttime 形式='2020-10-01'
        self.__starttime= ""
        self.__endtime= ""
