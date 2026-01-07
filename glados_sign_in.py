import requests,json,os
import datetime
import pandas as pd
import time
from dotenv import load_dotenv
load_dotenv()

# 请求超时时间（秒）
REQUEST_TIMEOUT = 15
# 最大重试次数
MAX_RETRIES = 3


# pushplus秘钥
sckey = os.environ.get("PUSHPLUS_TOKEN", "")

# glados账号cookie
cookies= os.environ.get("GLADOS_COOKIE", []).split("&")

# webhook编码
webhook_code = os.environ.get("WEBHOOK_CODE", "")

# 测试格式
# sckey = ""
# webhook_code = ""
# cookie_str = ""
# cookies = cookie_str.split("&")

if cookies[0] == "":
    print('未获取到COOKIE变量') 
    cookies = []
    exit(0)

def calculate_consecutive_days(dataframe):
    """
    计算连续签到天数
    """
    df = dataframe.copy()
    interval = df['checkin_date'] -df['checkin_date'].shift(1)
    if not pd.api.types.is_timedelta64_dtype(interval):
        interval = pd.to_timedelta(interval)
    
    interval_days = abs(interval.dt.days)
    
    df['interval_days'] = interval_days.fillna(1)
    df['Group'] = (df['interval_days'] != df['interval_days'].shift()).cumsum()
    
    consecutive_days =  len(df[df['Group'] == 1])
    
    
    return consecutive_days
        
    
    

def start():   
    # 推送内容
    title = "GLaDOS"
    success, fail = 0, 0        # 成功账号数量 失败账号数量
    sendContent = ""


    url= "https://glados.space/api/user/checkin"
    url2= "https://glados.space/api/user/status"
    referer = 'https://glados.space/console/checkin'
    origin = "https://glados.space"
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    payload={
        'token': 'glados.one'
    }
    for cookie in cookies:
        # 签到请求，带重试机制
        checkin = None
        for attempt in range(MAX_RETRIES):
            try:
                print(f"尝试签到 (第 {attempt + 1}/{MAX_RETRIES} 次)...")
                checkin = requests.post(url, headers={
                'cookie': cookie,
                'referer': referer,
                'origin': origin,
                'user-agent': useragent,
                'content-type': 'application/json;charset=UTF-8'
                }, data=json.dumps(payload), timeout=REQUEST_TIMEOUT)
                print(f"签到请求成功，状态码: {checkin.status_code}")
                break  # 请求成功，跳出重试循环
            except requests.exceptions.Timeout:
                print(f"签到请求超时 (第 {attempt + 1} 次)")
                if attempt < MAX_RETRIES - 1:
                    print(f"等待 3 秒后重试...")
                    time.sleep(3)
            except requests.exceptions.RequestException as e:
                print(f"签到请求异常: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"等待 3 秒后重试...")
                    time.sleep(3)
        
        if checkin is None:
            message_content = "签到请求失败，所有重试均超时"
            fail += 1
            sendContent += f"签到状态: {message_content}\n\n"
            continue

        if checkin.status_code == 502:
            message_content = "签到请求失败，服务器返回502 Bad Gateway"
            fail += 1
            sendContent += f"签到状态: {message_content}\n\n"
            continue

        # 获取用户状态，也添加超时
        try:
            state_response = requests.get(url2, headers={
                'cookie': cookie,
                'referer': referer,
                'origin': origin,
                'user-agent': useragent
            }, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            print(f"获取用户状态请求失败: {e}")
            message_content = f"获取用户状态失败: {e}"
            fail += 1
            sendContent += f"签到状态: {message_content}\n\n"
            continue

        state = state_response.json()
        
        # 检查返回状态：code=0 表示成功，其他值表示失败
        if state_response.status_code != 200 or state.get('code', -1) != 0:
            error_msg = state.get('message', '未知错误')
            error_code = state.get('code', '未知')
            message_content = f"获取用户状态失败 [code={error_code}]: {error_msg}"
            print(f"⚠️ Cookie 可能无效或已过期: {message_content}")
            print(f"   请重新获取 Cookie 并更新 .env 文件")
            fail += 1
            sendContent += f"签到状态: {message_content}\n\n"
            continue
    #--------------------------------------------------------------------------------------------------------#  
        leftdays = str(state['data']['leftDays']).split('.')[0]
        email = state['data']['email']
        vip_days = state['data']['vip']
        
        if checkin.status_code == 200:
            checkin_result = checkin.json()
            message_status = checkin_result['message']
            
            # 本次执行获取的点数
            points = checkin_result['points']
            
            
            # 获取签到记录
            df_checkin = pd.DataFrame(checkin_result['list'])
            df_checkin['change'] = df_checkin['change'].astype('float')
            df_checkin['checkin_date'] = df_checkin['time'].apply( lambda x: datetime.datetime.fromtimestamp(x/1000).date())
            df_checkin['checkin_time'] = df_checkin['time'].apply( lambda x: datetime.datetime.fromtimestamp(x/1000).strftime('%Y-%m-%d %H:%M:%S'))
            
            # df_checkin = df_checkin.sort_values('checkin_date', ascending=False)
            
            
            # 过滤出积分增加和签到记录，排除积分扣除记录
            valid_checkin = df_checkin[df_checkin['change'] >= 0]
            deduct_record = df_checkin[df_checkin['change'] < 0]
            
            # 本日积分变动
            change = df_checkin['change'][0]
            
            # 当前剩余积分
            balance = int(float(df_checkin['balance'][0]))
            
            # 执行签到的时间
            checkin_time = df_checkin['checkin_time'][0]
            
            # 最近签到日期
            checkin_date = df_checkin['checkin_date'][0]
            
            # 计算连续天数
            consecutive_days = calculate_consecutive_days(valid_checkin)
            
            
            
            # # 本日签到获取点数
            # change = int(float(checkin_result['list'][0]['change']))
            
            # # 账号当前剩余活动点数
            # balance =  int(float(checkin_result['list'][0]['balance']))
            
            # # 执行签到的时间
            # checkin_timestamp = checkin_result['list'][0]['time'] /1000
            # checkin_time = datetime.datetime.fromtimestamp(checkin_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            # # 预计签到的日期
            # checkin_date = checkin_result['list'][0]['business'].split(':')[-1]
            
            # # 计算连续签到天数
            # consecutive_days = calculate_consecutive_days(checkin_result['list'])
            
            print(email+'----'+message_status+'----剩余('+leftdays+')天')

            if "Points" in message_status:
                success += 1
                message_content = "签到成功"

            elif "Please Try Tomorrow" in message_status:
                message_content = "今日已签到"

            else:
                fail += 1
                message_content = "签到失败，请检查..."

            if leftdays is not None:
                message_days = f"{leftdays} 天"

            else:
                message_days = "无法获取剩余天数信息"

        else:
            message_content = "签到请求url失败, 请检查...cookie"
            message_days = "获取信息失败"


        # 推送内容
        sendContent += f"{'-'*30}\n\
            成功：{success}\n\
            失败：{fail}\n\
            账号: {email}\n\
            状态码：{checkin.status_code}\n\
            签到状态: {message_content}\n\
            签到消息：{message_status}\n\
            本次执行获取积分：{points}\n\
            本日积分变动: {change}\n\
            剩余天数: {leftdays}\n\
            剩余VIP天数: {vip_days}\n\
            当前积分: {balance}\n\
            签到时间: {checkin_time}\n\
            最近签到日期: {checkin_date}\n\
            连续签到天数: {consecutive_days}\n"
        
        if cookie == cookies[-1]:
            sendContent += '-' * 30

    #--------------------------------------------------------------------------------------------------------#   
    print("sendContent:" + "\n", sendContent)

    if sckey != "":
        title += f': 成功{success},失败{fail}'
        
        url = 'http://www.pushplus.plus/send'
        data = {
            "token":sckey,
            "title":title,
            "content":sendContent,
            "channel":"webhook",
            "webhook": webhook_code,  # 设置自己的webhook编码
        }
        
        body=json.dumps(data).encode(encoding='utf-8')
        headers = {'Content-Type':'application/json'}
        requests.post(url,data=body,headers=headers)

def main_handler(event, context):
  return start()

if __name__ == '__main__':
    start()