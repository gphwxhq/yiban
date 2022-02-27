# yiban

**每个人有义务按时填报打卡记录，并对打卡记录负责，本脚本仅供学习使用**

* 自动提取打卡表单
* 批量完成早中打卡
* 随机生成体温
* 完成晚签到
* server酱推送结果

# 使用方法：  
1、下载所需库(requests,pycrypto)  
2、填写extracter.py内容，运行以获取打卡模板  
3、修改list.json中的表单，不要删去"[]"或"°"  
4、填写start.py或start_night.py中的内容  
5、运行start.py执行早中打卡，运行star_night.py执行晚签到

# 文件作用
ConfigHelper.py: 读写list.json  
Encryptions.py: 加密方法  
list.json: 提交表单文件  
Logger.py: 日志管理  
photo.jpg: 晚打卡示例照片  
start.py: 启动打卡  
start_night.py: 启动晚打卡  
extracter.py: 启动表单抽取  
Utils.py: 主要工作文件  
yiban.log: 日志文件

# 自定义
如需更换list.json文件名，请在ConfigHelper.py中修改  
日志存放位置可在logger.py中的LOG_PATH修改
默认打卡时间范围为一星期，可在Utils.py更改starttime和endtime修改，最长不超过一个月  

# 关于list.json
运行extracter.py会将打卡模板保存至该文件，提交的表单来自该文件  
采用json格式保存表单，可自定义该文件，除了体温均可写死，表单中如出现额外的'体温'两字，请修改switchForm函数的判断逻辑

# 经纬度获取方法
[高德api](https://lbs.amap.com/tools/picker)

# 服务器部署：
参考crontab命令
