import json
import re
import time

from configs.api import ACTIVELIST, ANALYSIS, ANALYSIS2, CHAT_GROUP, PPTACTIVEINFO, PRESIGN
from utils.request import request_manager
from utils.debug import is_debug_mode, debug_print
from functions.general import handle_general_sign, handle_code_sign
from functions.gesture import handle_gesture_sign
from functions.qrcode import handle_qrcode_sign
from functions.location import handle_location_sign
from functions.photo import handle_photo_sign

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
    
    # 设置临时cookies
    if cookies:
        request_manager.set_cookies(cookies)
    
    if is_debug_mode():
        debug_print(f"正在检查课程 {course.get('courseName', '未知课程')} 的签到活动", "blue")
        
    result = request_manager.request(
        url,
        {
            'headers': {
                'Referer': 'https://mooc1-1.chaoxing.com/visit/interaction',
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
                        if is_debug_mode():
                            debug_print(f"活动详情: ID={active_list[0].get('id')}, 类型={other_id}, 状态={active_list[0].get('status')}", "green")
                        return {
                            'activeId': active_list[0].get('id'),
                            'name': active_list[0].get('nameOne'),
                            'courseId': course['courseId'],
                            'classId': course['classId'],
                            'otherId': other_id,
                        }
        else:
            print('请求似乎有些频繁，获取数据为空!')
            if is_debug_mode():
                debug_print("获取活动列表失败，返回数据为空", "red")
            return 'Too Frequent'
    except Exception as e:
        print(f"解析活动数据出错: {e}")
        if is_debug_mode():
            debug_print(f"解析活动数据出错: {e}", "red")
    
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
    
    # 设置临时cookies
    if cookies:
        request_manager.set_cookies(cookies)
        
    result = request_manager.request(
        url,
        {
            'scenario': 'activity',
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
    
    if is_debug_mode():
        debug_print(f"开始执行预签到: activeId={active_id}, courseId={course_id}, classId={class_id}", "blue")
    
    # 从args提取认证信息并设置
    auth_info = {k: v for k, v in args.items() if k not in ['activeId', 'classId', 'courseId']}
    request_manager.set_cookies(auth_info)
    
    # 预签到
    url = f"{PRESIGN['URL']}?courseId={course_id}&classId={class_id}&activePrimaryId={active_id}&general=1&sys=1&ls=1&appType=15&&tid=&uid={_uid}&ut=s"
    result = request_manager.request(
        url,
        {
            'headers': {
                'Referer': 'https://mobilelearn.chaoxing.com/',
            },
        }
    )
    print('[预签]已请求')
    
    if is_debug_mode():
        debug_print(f"预签到响应状态: {result['statusCode']}", "green")
    
    # analysis
    analysis_url = f"{ANALYSIS['URL']}?vs=1&DB_STRATEGY=RANDOM&aid={active_id}"
    analysis_result = request_manager.request(
        analysis_url,
        {
            'headers': {
                'Referer': 'https://mobilelearn.chaoxing.com/',
            },
        }
    )
    
    if is_debug_mode():
        debug_print(f"Analysis请求状态: {analysis_result['statusCode']}", "green")
    
    code_data = analysis_result['data']
    code_match = re.search(r"code=\'\+(\'.*?\')", code_data)
    if code_match:
        code = code_match.group(1).strip("'")
        
        # analysis2
        analysis2_url = f"{ANALYSIS2['URL']}?DB_STRATEGY=RANDOM&code={code}"
        analysis2_result = request_manager.request(
            analysis2_url,
            {
                'headers': {
                    'Referer': 'https://mobilelearn.chaoxing.com/',
                },
            }
        )
        print(f"analysis 请求结果：{analysis2_result['data']}")
        
        if is_debug_mode():
            debug_print(f"Analysis2请求状态: {analysis2_result['statusCode']}", "green")
    

def handle_activity_sign(params, activity, configs, name, location_preset_item=None, location_address_info=None, location_random_offset=True):
    """
    根据活动类型处理签到
    
    Args:
        params: 用户参数
        activity: 活动信息
        configs: 配置信息
        name: 用户名
        location_preset_item: 位置签到的预设位置索引，None表示自动选择
        location_address_info: 位置签到的自定义位置信息
        location_random_offset: 位置签到时是否随机偏移坐标，默认为True
    
    Returns:
        tuple: (签到结果, 更新后的配置)
    """
    import sys
    
    # 预签到
    pre_sign({**activity, **params})
    
    # 根据签到类型调用相应的处理函数
    other_id = activity['otherId']
    
    if is_debug_mode():
        debug_print(f"处理签到活动: 类型ID={other_id}, 活动ID={activity['activeId']}, 用户={name}", "blue")
    
    if other_id == 2:
        # 二维码签到
        return handle_qrcode_sign(params, activity, configs, name), configs
    
    elif other_id == 4:
        # 位置签到
        return handle_location_sign(params, activity, configs, name, location_preset_item, location_address_info, location_random_offset)
    
    elif other_id == 3:
        # 手势签到
        return handle_gesture_sign(params, activity, name), configs
    
    elif other_id == 5:
        # 签到码签到
        return handle_code_sign(params, activity, name), configs
    
    elif other_id == 0:
        # 获取签到详情
        photo = get_ppt_active_info(activity['activeId'], **params)
        
        if is_debug_mode():
            debug_print(f"获取签到详情: ifphoto={photo.get('ifphoto')}", "green")
        
        if photo.get('ifphoto') == 1:
            # 拍照签到
            return handle_photo_sign(params, activity, name), configs
        else:
            # 普通签到
            return handle_general_sign(params, activity, name), configs
    
    return "未知的签到类型", configs 