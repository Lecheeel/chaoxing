import json
import re
import time

from configs.api import ACTIVELIST, ANALYSIS, ANALYSIS2, CHAT_GROUP, PPTACTIVEINFO, PRESIGN
from utils.request import request, cookie_serialize
from utils.helper import delay

def traverse_course_activity(args):
    """
    遍历课程查找有效签到活动
    
    Args:
        args: 包含课程列表和用户凭证的字典
    
    Returns:
        dict/str: 签到活动信息或错误信息
    """
    print('正在查询有效签到活动，等待时间视网络情况而定...')
    courses = args.get('courses', [])
    cookies = {k: v for k, v in args.items() if k != 'courses'}
    
    # 特殊情况，只有一门课
    if len(courses) == 1:
        try:
            return get_activity(course=courses[0], **cookies)
        except Exception:
            print('未检测到有效签到活动！')
            return 'NoActivity'
    
    # 一次请求五个，全部reject或有一个成功则进行下一次请求
    for i in range(0, len(courses), 5):
        batch = courses[i:i+5]
        for course in batch:
            try:
                result = get_activity(course=course, **cookies)
                if result != 'Not Available':
                    return result
            except Exception:
                continue
    
    print('未检测到有效签到活动！')
    return 'NoActivity'

def get_activity(course, **cookies):
    """
    获取签到活动信息
    
    Args:
        course: 课程信息
        **cookies: 用户凭证
    
    Returns:
        dict/str: 签到活动信息或错误信息
    """
    url = f"{ACTIVELIST['URL']}?fid=0&courseId={course['courseId']}&classId={course['classId']}&_={int(time.time() * 1000)}"
    result = request(
        url,
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
        }
    )
    
    try:
        data = json.loads(result['data'])
        
        # 判断是否请求成功
        if data.get('data') is not None:
            active_list = data['data'].get('activeList', [])
            if active_list:
                other_id = int(active_list[0].get('otherId', -1))
                # 判断是否有效签到活动
                if 0 <= other_id <= 5 and active_list[0].get('status') == 1:
                    # 活动开始超过两小时则忽略
                    start_time = active_list[0].get('startTime', 0)
                    if (time.time() * 1000 - start_time) / 1000 < 7200:
                        print(f"检测到活动：{active_list[0].get('nameOne', '未知活动')}")
                        return {
                            'activeId': active_list[0].get('id'),
                            'name': active_list[0].get('nameOne'),
                            'courseId': course['courseId'],
                            'classId': course['classId'],
                            'otherId': other_id,
                        }
        else:
            print('请求似乎有些频繁，获取数据为空!')
            return 'Too Frequent'
    except Exception as e:
        print(f"解析活动数据出错: {e}")
    
    # 此课程最新活动并非有效签到
    raise Exception('Not Available')

def get_ppt_active_info(active_id, **cookies):
    """
    根据activeId请求获得签到信息
    
    Args:
        active_id: 活动ID
        **cookies: 用户凭证
    
    Returns:
        dict: 签到信息
    """
    url = f"{PPTACTIVEINFO['URL']}?activeId={active_id}"
    result = request(
        url,
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
        }
    )
    
    return json.loads(result['data']).get('data', {})

def pre_sign(args):
    """
    预签到请求
    
    Args:
        args: 包含活动ID、课程ID、班级ID和用户凭证的字典
    """
    active_id = args.get('activeId')
    class_id = args.get('classId')
    course_id = args.get('courseId')
    _uid = args.get('_uid')
    
    cookies = {k: v for k, v in args.items() if k not in ['activeId', 'classId', 'courseId']}
    
    # 预签到
    url = f"{PRESIGN['URL']}?courseId={course_id}&classId={class_id}&activePrimaryId={active_id}&general=1&sys=1&ls=1&appType=15&&tid=&uid={_uid}&ut=s"
    request(
        url,
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
        }
    )
    print('[预签]已请求')
    
    # analysis
    analysis_url = f"{ANALYSIS['URL']}?vs=1&DB_STRATEGY=RANDOM&aid={active_id}"
    analysis_result = request(
        analysis_url,
        {
            'headers': {
                'Cookie': cookie_serialize(cookies),
            },
        }
    )
    
    code_data = analysis_result['data']
    code_match = re.search(r"code=\'\+(\'.*?\')", code_data)
    if code_match:
        code = code_match.group(1).strip("'")
        
        # analysis2
        analysis2_url = f"{ANALYSIS2['URL']}?DB_STRATEGY=RANDOM&code={code}"
        analysis2_result = request(
            analysis2_url,
            {
                'headers': {
                    'Cookie': cookie_serialize(cookies),
                },
            }
        )
        print(f"analysis 请求结果：{analysis2_result['data']}")
    
    # 延迟500ms
    delay(0.5)

def speculate_type(text):
    """
    推测签到类型
    
    Args:
        text: 活动名称
    
    Returns:
        str: 签到类型
    """
    if '拍照' in text:
        return 'photo'
    elif '位置' in text:
        return 'location'
    elif '二维码' in text:
        return 'qr'
    # 普通、手势
    return 'general'

def get_sign_type(ppt_active_info):
    """
    解析签到类型
    
    Args:
        ppt_active_info: getPPTActiveInfo的返回对象
    
    Returns:
        str: 签到类型描述
    """
    other_id = ppt_active_info.get('otherId')
    if other_id == 0:
        if ppt_active_info.get('ifphoto') == 1:
            return '拍照签到'
        else:
            return '普通签到'
    elif other_id == 2:
        return '二维码签到'
    elif other_id == 3:
        return '手势签到'
    elif other_id == 4:
        return '位置签到'
    elif other_id == 5:
        return '签到码签到'
    else:
        return '未知'

def get_sign_result(result):
    """
    解析签到结果
    
    Args:
        result: 签到结果
    
    Returns:
        str: 具体的中文结果
    """
    if result == 'success':
        return '成功'
    elif result == 'fail':
        return '失败'
    elif result == 'fail-need-qrcode':
        return '请发送二维码'
    else:
        return result

def handle_activity_sign(params, activity, configs, name):
    """根据活动类型处理签到"""
    import sys
    from functions.general import handle_general_sign, handle_gesture_sign, handle_code_sign
    from functions.qrcode import handle_qrcode_sign
    from functions.location import handle_location_sign
    from functions.photo import handle_photo_sign
    
    # 预签到
    pre_sign({**activity, **params})
    
    # 根据签到类型调用相应的处理函数
    other_id = activity['otherId']
    
    if other_id == 2:
        # 二维码签到
        return handle_qrcode_sign(params, activity, configs, name), configs
    
    elif other_id == 4:
        # 位置签到
        return handle_location_sign(params, activity, configs, name)
    
    elif other_id == 3:
        # 手势签到
        return handle_gesture_sign(params, activity, name), configs
    
    elif other_id == 5:
        # 签到码签到
        return handle_code_sign(params, activity, name), configs
    
    elif other_id == 0:
        # 获取签到详情
        photo = get_ppt_active_info(activity['activeId'], **params)
        
        if photo.get('ifphoto') == 1:
            # 拍照签到
            return handle_photo_sign(params, activity, name), configs
        else:
            # 普通签到
            return handle_general_sign(params, activity, name), configs
    
    return "未知的签到类型", configs 