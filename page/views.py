# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from page.models import Test
from page.models import Responses
from . import funs
import json
import requests
import time

'''
首页
'''
def index(request):
    return render(request, 'page/index.html')

'''
手动单条测试
'''
def test(request):
    save_action = request.POST.get('save_action', 0)
    project_id = request.POST['project_id']
    api_id = request.POST.get('api_id', 0)
    action_method = request.POST['action_method']
    api = request.POST['api']
    header_keys = request.POST.getlist('header_key[]')
    header_values = request.POST.getlist('header_value[]')
    header_descriptions = request.POST.getlist('header_description[]')
    body_keys = request.POST.getlist('body_key[]')
    body_values = request.POST.getlist('body_value[]')
    body_description = request.POST.getlist('body_description[]')
    cookie_keys = request.POST.getlist('cookie_key[]')
    cookie_values = request.POST.getlist('cookie_value[]')
    cookie_description = request.POST.getlist('cookie_description[]')

    headers = dict(zip(header_keys, header_values))
    bodies = dict(zip(body_keys, body_values))
    cookies = dict(zip(cookie_keys, cookie_values))

    headers_desc = dict(zip(header_keys, header_descriptions))
    bodies_desc = dict(zip(body_keys, body_description))
    cookies_desc = dict(zip(cookie_keys, cookie_description))

    headers_data = {}
    for h in headers:
        if len(h.strip()) :
            headers_data[h] = headers[h]

    bodies_data = {}
    for b in bodies :
        if len(b.strip()) :
            bodies_data[b] = bodies[b]

    cookies_data = {}
    for c in cookies :
        if len(c.strip()) :
            cookies_data[c] = cookies[c]

    if action_method == 'post' :
        res = requests.post(api, params=bodies_data, headers=headers_data, cookies=cookies_data)
    elif action_method == 'get' :
        res = requests.get(api, params=bodies_data, headers=headers_data, cookies=cookies_data)

    if save_action == '1' :
        add_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        test_tb = Test(project_id=project_id, api=api, action_method=action_method, headers = json.dumps(headers), bodies= json.dumps(bodies), cookies= json.dumps(cookies), headers_desc= json.dumps(headers_desc), bodies_desc=json.dumps(bodies_desc), cookies_desc=json.dumps(cookies_desc), add_time=add_time, update_time=update_time)
        test_tb.save()
        api_id = test_tb.id

        text_md5 = funs.md5_hash(res.text)
        responses_tb = Responses(api_id=api_id, text=res.text, text_md5=text_md5, status=res.status_code, response_time=res.elapsed.microseconds, add_time=add_time, update_time=update_time);
        responses_tb.save()

    return HttpResponse(res.text)

    '''
    status = res.status_code
    text = res.text
    microseconds = res.elapsed.microseconds
    '''

'''
测试列表展示
'''
def show(request):
    api_id = request.POST.get('api_id', 0)

    if api_id == 0 :
        # 获取全部
        test_list = Test.objects.all()
        json_list = serializers.serialize('json', test_list)
    else:
        # 获取一条数据
        test_list = Test.objects.filter(id=api_id)
        json_list = serializers.serialize('json', test_list)

    return HttpResponse(json_list, content_type="application/json")

'''
批量测试展示
'''
def project(request):
    project_id = request.POST.get('project_id', 0)

    project_list = Test.objects.filter(project_id=project_id)

    return render(request, 'page/project.html', {'project_list' : project_list})

'''
批量单挑测试
'''
def test_one(request):
    api_id = request.GET.get('api_id', 0)
    compare_response = request.GET['compare_response']
    compare_runtime = request.GET['compare_runtime']

    test_info = Test.objects.filter(id=api_id)
    response_info = Responses.objects.filter(api_id=api_id)

    for res_info in response_info:
        res_text = res_info.text
        res_text_md5 = res_info.text_md5
        res_response_time = res_info.response_time

    for p in test_info :
        action_method = p.action_method
        api = p.api
        bodies_json = p.bodies
        headers_json = p.headers
        cookies_json = p.cookies

    bodies = json.loads(bodies_json)
    headers = json.loads(headers_json)
    cookies = json.loads(cookies_json)

    headers_data = {}
    for h in headers:
        if len(h.strip()) :
            headers_data[h] = headers[h]

    bodies_data = {}
    for b in bodies :
        if len(b.strip()) :
            bodies_data[b] = bodies[b]

    cookies_data = {}
    for c in cookies :
        if len(c.strip()) :
            cookies_data[c] = cookies[c]

    if action_method == 'post' :
        res = requests.post(api, params=bodies_data, headers=headers_data, cookies=cookies_data)
    elif action_method == 'get' :
        res = requests.get(api, params=bodies_data, headers=headers_data, cookies=cookies_data)

    response_info_md5 = funs.md5_hash(res.text)

    code = 0
    msg = 'ok'
    if 'true' == compare_response :
        if res_text_md5 != response_info_md5 :
            '''返回值不同'''
            code = 1
            msg = '返回值不同'


    if 'true' == compare_runtime :
        if res_response_time < res.elapsed.microseconds :
            '''运行时超时'''
            code = 2
            msg = '运行超时'


    message_info = {'code':code, 'msg':msg}

    return HttpResponse(json.dumps(message_info), content_type="application/json")