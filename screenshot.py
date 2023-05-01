import pyautogui
import requests
import json
from collections import Counter
import re
import openai
import os
import time
import datetime
import platform
from wechat_utils import activate_wechat_and_send_message

# Your other code here

# # Call the function to activate WeChat and send a message
# message = "Hello, WeChat!"
# activate_wechat_and_send_message(message)

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        new_distances = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                new_distances.append(distances[i1])
            else:
                new_distances.append(1 + min((distances[i1], distances[i1 + 1], new_distances[-1])))
        distances = new_distances
    return distances[-1]

def similarity(s1, s2):
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    similarity = (max_len - distance) / max_len
    return similarity

string1 = "刘浩存 (应该是某次采访)"
string2 = "刘浩存 (应该是某次采访"

# similarity_score = similarity(string1, string2)
# print("The similarity score between the two strings is:", similarity_score)
# exit()


def remove_number_prefix(text):
    return re.sub(r"^\d+、\s*", "", text)

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

# 定义一个函数，检查文本中是否包含关键词列表中的任何一个关键词
def contains_keyword(text, keywords):
    return any(keyword in text for keyword in keywords)

def autoreply():
    # 将鼠标移动到指定坐标
    pyautogui.moveTo(200, 300)

    # # 在当前位置执行鼠标单击
    pyautogui.click()

    with open("config.json", "rb") as config_file:
        config = json.loads(config_file.read())

    openai.api_key  = config["open_ai_api_key"]

    time.sleep(1)
    # 截取屏幕截图
    screenshot = pyautogui.screenshot()

    file_path = "screenshot.png"
    # # 将屏幕截图保存为文件
    screenshot.save(file_path)


    url = "http://192.168.10.8:8089/api/tr-run/"

    # 替换此路径为您的截图文件路径
    screenshot_path = file_path

    with open(screenshot_path, "rb") as image_file:
        image_data = image_file.read()

    multipart_data = {
        "file": (screenshot_path, image_data, "image/png"),
        "compress": (None, "960"),
    }

    response = requests.post(url, files=multipart_data, verify=False)


    # print(response.text)

    text = response.text

    # 将 JSON 字符串解析为 Python 字典
    response_dict = json.loads(text)

    # 从字典中删除 img_detected 字段
    if "data" in response_dict and "img_detected" in response_dict["data"]:
        del response_dict["data"]["img_detected"]

    # 将修改后的字典转换回 JSON 字符串
    new_response_string = json.dumps(response_dict, ensure_ascii=False)

    # print(new_response_string)

    with open('result.json', 'w') as f:
        f.write(new_response_string)

    # 将 JSON 字符串解析为 Python 字典
    response_dict = json.loads(new_response_string)

    data = response_dict["data"]["raw_out"]


    # 提取x和y坐标
    x_coords = [item[0][point_idx][0] for item in data for point_idx in [0, 3]]


    # 初始化sorted_x
    sorted_x = []

    # 对x坐标进行处理
    for x in x_coords:
        merged = False
        for sorted_item in sorted_x:
            if abs(x - sorted_item[0]) <= 5:
                sorted_item[1] += 1
                merged = True
                break

        if not merged:
            sorted_x.append([x, 1])

    # 对sorted_x进行排序，按出现次数从多到少排序
    sorted_x = sorted(sorted_x, key=lambda x: x[1], reverse=True)

    # 输出结果
    # print("按出现次数从多到少排序的x坐标：")
    # for x, count in sorted_x:
    #     print(f"x坐标 {x} 出现了 {count} 次")


    # print("\n按出现次数从多到少排序的y坐标：")
    # for y, count in sorted_y:
    #     print(f"y坐标 {y} 出现了 {count} 次")

    # 提取前4个元素的x坐标值
    first_four_x_coords = [item[0] for item in sorted_x[:6]]

    # 找出前4个元素中的最大x坐标值，但不选择超过500的坐标值
    max_x_coord = max(x for x in first_four_x_coords if x <= 500)

    filtered_x_coords = [x for x in first_four_x_coords if x <= 500]
    filtered_x_coords.sort(reverse=True)

    if len(filtered_x_coords) >= 2:
        second_largest_x = filtered_x_coords[1]
    else:
        second_largest_x = None

    print("大x坐标值：", max_x_coord, "第二大x坐标值：", second_largest_x)

    group_name = ""
    merged_data = []
    data = sorted(data, key=lambda item: item[0][0][1])

    def merge(item, merged_data, max_x_coord, second_largest_x):
        ltpoint = item[0][0]
        isMsg = False
        isName = False
        if abs(ltpoint[0] - max_x_coord) <= 5:
            isMsg = True
        elif abs(ltpoint[0] - second_largest_x) <= 5:
            isName = True 
        # print(item)
        # print(isMsg, isName)
        if isMsg:
            type = "msg"
        elif isName:
            type = "name"
        else:
            type = "other"
        item.append(type)
        # if len(merged_data[index]) >= 4:
        #     merged_data[index][3] = type
        # else:
        #     merged_data[index].append(type)
        if isMsg or isName:
            # print(point)
            merged = False
            for index, merged_item in enumerate(merged_data):
                # print(item, merged_item)
                merged_lbpoint = merged_item[0][3]
                if abs(ltpoint[1] - merged_lbpoint[1]) <= 10 and item[3] == merged_item[3]:
                    print("<= 5",item, merged_item)
                    merged_data[index][0][0] = merged_item[0][0]
                    merged_data[index][0][1] = merged_item[0][1]
                    merged_data[index][0][2] = item[0][2]
                    merged_data[index][0][3] = item[0][3]
                    merged_data[index][1] = merged_item[1] + item[1]
                    merged_data[index][2] = (merged_item[2] + item[2]) / 2
                    merged_data[index][3] = merged_item[3]
                    merged = True
                    # exit()
                    break
                

            if not merged:
                merged_data.append(item)

    for item in data:
        item[1] = remove_number_prefix(item[1])
        ltpoint = item[0][0]
        lbpoint = item[0][3]
        if not group_name and abs(max_x_coord - ltpoint[0] - 46) <= 31:
            # print(item)
            group_name = item[1]
            print(group_name)

        merge(item, merged_data, max_x_coord, second_largest_x)

    print(merged_data)

    # 提取共有部分
    fixed_name = group_name.replace(' ', '').split('(')[0]


    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    file_name = f"{fixed_name}_{current_date}.json".replace('/', '_').replace('|', '_').replace('*s', '_')

    file_path = "history/" + file_name
    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 如果文件不存在，则创建文件
        with open(file_path, 'w') as f:
            f.write("[]")

    reverse_merged_data = sorted(merged_data, key=lambda item: item[0][0][1], reverse=True)
    with open(file_path, 'rb+') as f:
        old = json.loads(f.read())
        for item in reverse_merged_data:
            
            found = False
            for old_item in old:
                similarity_score = similarity(item[1], old_item[1])
                if similarity_score >= 0.6:
                    found = True
                    break
            
            if not found:
                requested = False
                if (contains_keyword(item[1], config["group_chat_keyword"]) and "@" not in item[1] and item[3] == "msg") or "@全" in item[1]:
                    history = ""
                    name = ""
                    if len(old) > 0:
                        last_item = old[-1]
                        old = old[:-1]
                        name = last_item[1]
                    history = '\n'.join((item[1] + ':' if len(item) >= 4 and item[3] == 'name' else item[1]) for item in old[-100:])
                    
                    prompt = f"历史消息：{history}。这个消息来自微信群{group_name}{name}，如果无法提供有效的回复，返回0，不然请用50字以内回答或建议: {item[1]}。\n"
                    print(prompt)
                    
                    message = "Hello, this is a test message!"
                    if any(name in group_name for name in config["group_name_white_list"]):
                        response = get_completion(prompt, "gpt-4") + "\n(人工智能生成，可能有错)"
                        print(response)
                        if (not "无法提供" in response) and (not "0" in response) and (not "不知道" in response) and (not "不清楚" in response) and (not "不了解" in response) and (not "不太" in response) and (not "不理解" in response):
                            activate_wechat_and_send_message(response)
                    else:
                        response = get_completion(prompt, "gpt-3.5-turbo") + "\n(人工智能生成，可能有错)"
                        print(response)
                        # activate_wechat_and_send_message(response)
                    requested = True
                    

                
                if requested:
                    time.sleep(20)
                    for item in merged_data:
                        old.append(item)    
                    # print(old)
                    # 从文件开头开始写入
                    f.seek(0)
                    f.write(json.dumps(old).encode('utf-8'))
                    f.truncate()  # 删除文件中任何剩余的内容
                    break

while True:
    autoreply()
    time.sleep(10)

exit()


for item in merged_data:
    if contains_keyword(item[1], config["group_chat_keyword"]):
        prompt = "这个消息来自微信群,请用50字以内回答: " + item[1]
        print(prompt)
        response = get_completion(prompt)
        print(response)
        message = "Hello, this is a test message!"
        activate_wechat_and_send_message(response)

# # 提取第一个x附近的y坐标
# nearby_y = [
#     item for item in data for point in item[0] if abs(point[0] - first_column_near) <= 5
# ]

# print("\n第一个x附近的y坐标：")
# for y in nearby_y:
#     print(f"y = {y}")


# # 设定y的阈值
# y_threshold = 5

# # 合并相近的y元素
# merged_data = []

# for y in nearby_y:
#     # 查找与当前y相近的元素
#     close_elements = [
#         element for element in nearby_y if abs(element - y) <= y_threshold
#     ]

#     # 如果找到相近元素且未被处理过，则合并
#     if close_elements and y not in merged_y:
#         merged_y.append(sum(close_elements) / len(close_elements))

# # 输出结果
# print("在第一个x附近，根据y合并相近的元素：")
# for y in merged_y:
#     print(f"y = {y}")
# 定义一个函数来删除文本中的数字前缀
