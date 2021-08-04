# yiban
内大易班两检一点
<font color='red'> 由于代码结构太差，不方便维护，已停止更新 </font>

* 批量完成早中打卡
* 随机生成体温
* 完成晚签到（仅支持东区）
* 随机生成地址
* server酱推送结果

在python 3.6,3.8环境下测试成功  
感谢looyeagee大佬提供思路，参考项目：https://github.com/looyeagee/yiban_auto_submit
# 使用方法：  
1、下载所需库(requests,pycrypto)  
2、填写start.py和start_night.py中的内容 
3、运行start.py执行早中打卡，运行star_night.py执行晚签到

# 服务器部署：
参考crontab命令  
日志存放位置可在logger.py中的LOG_PATH修改
