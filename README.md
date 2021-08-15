# yiban

**每个人有义务按时填报打卡记录，并对打卡记录负责，本脚本仅供学习使用**

* 批量完成早中打卡
* 随机生成体温
* 完成晚签到
* server酱推送结果

# 使用方法：  
1、下载所需库(requests,pycrypto)  
2、填写start.py,start_night.py中的内容，按需修改list.json中的表单
3、运行start.py执行早中打卡，运行star_night.py执行晚签到

# list.json
采用json格式保存表单，除了体温均可写死，体温如不加'°'则留空，加'°'则填'°'，表单中如出现额外的'体温'两字，请修改switchForm函数的判断逻辑

# 经纬度获取方法
[高德api](https://lbs.amap.com/tools/picker)

# 服务器部署：
参考crontab命令  
日志存放位置可在logger.py中的LOG_PATH修改
