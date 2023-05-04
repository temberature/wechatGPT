# -*- coding: utf-8 -*-

import io
import random
import sys
import numpy as np
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
from paddleocr import PaddleOCR, draw_ocr
import cv2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
from readability import Document
import html2markdown
import html2text
# Change the standard output encoding to UTF-8
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8', errors='ignore')

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from state_manager import update_first_x_coords, update_prob, get_most_common_coords



def get_webpage_content(url):
    # Configure browser options
    chrome_options = Options()
    chrome_options.headless = True

    # Initialize the browser
    browser = webdriver.Chrome(options=chrome_options)

    # Open the webpage
    browser.get(url)

    # Wait for the webpage to fully render
    time.sleep(5)

    # Get the rendered HTML content
    rendered_html = browser.page_source

    # Close the WebDriver instance
    browser.quit()

    # Return the rendered HTML content
    return rendered_html

def get_markdown(url):
    webpage_content = get_webpage_content(url)

    if webpage_content:
        doc = Document(webpage_content)
        main_content = doc.summary()
        markdown_content = html2text.html2text(main_content)
        
        with open("output.md", "w", encoding='utf-8') as markdown_file:
            markdown_file.write(markdown_content)
        return markdown_content
            
def screenshot_webpage(url, save_path='screenshot.png'):
    # Configure browser options
    chrome_options = Options()
    chrome_options.headless = True

    # Initialize the browser
    browser = webdriver.Chrome(options=chrome_options)

    # Open the webpage
    browser.get(url)

    # Take a screenshot and save it to a file
    browser.save_screenshot(save_path)

    # Close the browser
    browser.quit()
    
def extract_links(text):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall(url_pattern, text)
    return urls

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
                new_distances.append(
                    1 + min((distances[i1], distances[i1 + 1], new_distances[-1])))
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
        temperature=0,  # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

# 定义一个函数，检查文本中是否包含关键词列表中的任何一个关键词


def contains_keyword(text, keywords):
    return any(keyword in text for keyword in keywords)

# 从 config.json 文件中加载 prob 变量
with open("state.json", "r") as f:
    config = json.load(f)
    prob = config["prob"]

# 使用 prob 变量进行其他操作
print("概率值为:", prob)
    
previous_content = None

def autoreply():
    global prob
    global previous_content
    # 将鼠标移动到指定坐标
    pyautogui.moveTo(200, 300)

    # # 在当前位置执行鼠标单击
    pyautogui.click()

    with open("config.json", "rb") as config_file:
        config = json.loads(config_file.read())

    openai.api_key = config["open_ai_api_key"]

    time.sleep(1)
    # 截取屏幕截图
    screenshot = pyautogui.screenshot()

    file_path = "screenshot.png"
    # # 将屏幕截图保存为文件
    screenshot.save(file_path)

    # 替换此路径为您的截图文件路径
    screenshot_path = file_path

    with open(screenshot_path, "rb") as image_file:
        image_data = image_file.read()


    ocr = PaddleOCR(lang='ch', ocr_version='PP-OCRv3', show_log=False) # need to run only once to download and load model into memory

    result = ocr.ocr(screenshot_path)
    # print(result)
    response_dict = [[entry[0], entry[1][0], entry[1][1]] for entry in result[0]]
    image = cv2.imread(screenshot_path)
    # Draw boxes on the image
    for box in response_dict:
        coordinates = box[0]
        pts = np.array(coordinates, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], True, (0, 255, 0), 2)

    # Save the image with boxes
    output_image_path = "output_image.jpg"
    cv2.imwrite(output_image_path, image)

    # Display the image (optional)
    # cv2.imshow("Image with Boxes", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # exit()
    with open('result.json', 'w') as f:
        f.write(json.dumps(response_dict))

    # 将 JSON 字符串解析为 Python 字典
    # response_dict = json.loads(new_response_string)

    data = response_dict

    # 提取x和y坐标
    x_coords = [item[0][point_idx][0] for item in data if item[2] > 0.6 for point_idx in [0, 3]]

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

 
    first_x_coords = [item[0] for item in sorted_x if item[1] >= 8]
    first_x_coords.sort()
    # print(first_x_coords)
    
    most_common_coords = get_most_common_coords()
    print(most_common_coords)
    if len(most_common_coords) < 1:
        most_common_coords = first_x_coords
    max_x_coord = most_common_coords[3]
    second_largest_x = most_common_coords[2]

    print("大x坐标值：", max_x_coord, "第二大x坐标值：", second_largest_x)

    group_name = ""
    merged_data = []
    data = sorted(data, key=lambda item: item[0][0][1])

    def merge(item, merged_data, max_x_coord, second_largest_x):
        ltpoint = item[0][0]
        isMsg = False
        isName = False
        if ltpoint[0] - max_x_coord <= 10 and ltpoint[0] - max_x_coord > -5:
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

        if isMsg or isName:
            # print(point)
            merged = False
            for index, merged_item in enumerate(merged_data):
                # print(item, merged_item)
                merged_lbpoint = merged_item[0][3]
                if abs(ltpoint[1] - merged_lbpoint[1]) <= 10 and item[3] == merged_item[3]:
                    print("<= 5", item, merged_item)
                    merged_data[index][0][0] = merged_item[0][0]
                    merged_data[index][0][1][1] = merged_item[0][1][1]
                    merged_data[index][0][1][0] = max(merged_item[0][1][0], item[0][1][0])
                    merged_data[index][0][2][1] = item[0][2][1]
                    merged_data[index][0][2][0] = max(merged_item[0][2][0], item[0][2][0])
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
    fixed_name = group_name.replace(' ', '').split('(')[0].split('（')[0]

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # file_name = f"{fixed_name}".replace(
    #     '/', '_').replace('|', '_').replace('*', '_').replace('?', '_').replace('$', '_').replace('＆', '_').replace('》', '_').replace('◆', '_')

    # 移除所有非中文汉字和非英文字母
    fixed_name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', '', fixed_name)
    for group in config['group_name_white_list']:
        if group in fixed_name:
            fixed_name = group
            break

    file_name = f"{fixed_name}_{current_date}.json"

    print(file_name)

    file_path = "history/" + file_name
    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 如果文件不存在，则创建文件
        with open(file_path, 'w') as f:
            f.write("[]")

    reverse_merged_data = sorted(
        merged_data, key=lambda item: item[0][0][1], reverse=True)
    
    prob_changed = False
    with open(file_path, 'rb+') as f:
        old = json.loads(f.read())
        filtered_reverse_merged_data = []
        found = False
        for item in reverse_merged_data:
            if not prob_changed and item[1] != '':
                print("item", item)
                print("previous_content", previous_content)
                if previous_content == item[1]:
                    prob = min(prob * 1.1, 0.999)
                else:
                    prob = prob * 0.9
                    # Update the state with the new data
                    update_first_x_coords(first_x_coords)
                update_prob(prob)
                print("prob", prob)
                previous_content = item[1]
                prob_changed = True
                
            for old_item in old:
                similarity_score = similarity(item[1], old_item[1])
                if similarity_score >= 0.6:
                    found = True
                    break
            if not found:
                filtered_reverse_merged_data.append(item)
                
        filtered_merged_data = sorted(filtered_reverse_merged_data, key=lambda item: item[0][0][1])
        requested = False
        for index, item in enumerate(filtered_reverse_merged_data):

            if not requested and (contains_keyword(item[1], config["group_chat_keyword"]) and "@" not in item[1] and item[3] == "msg") or "@全" in item[1]:
                before = old + filtered_merged_data[:-index-1]
                history = ""
                name = ""
                if len(before) > 0:
                    last_item = before[-1]
                    before = before[:-1]
                    name = last_item[1]
                history = '\n'.join(
                    (item[1] + ':' if len(item) >= 4 and item[3] == 'name' else item[1]) for item in before[-100:])

                prompt = f"历史消息：{history}。这个消息来自微信群{group_name}{name}，假设你是微信群的成员，请采用非正式文风，用50字以内回答或建议: {item[1]}？\n"
                print(prompt)

                message = "Hello, this is a test message!"
                if any(name in group_name for name in config["group_name_white_list"]):
                    response = get_completion(
                        prompt, "gpt-4") + "\n(人工智能生成，可能有错)"
                    print(response)
                    # if (not "无法提供" in response) and (not "0" in response) and (not "不知道" in response) and (not "不清楚" in response) and (not "不了解" in response) and (not "不太" in response) and (not "不理解" in response):
                    # # # Send a text message
                    #     activate_wechat_and_send_message(message=response)
                else:
                    response = get_completion(
                        prompt, "gpt-3.5-turbo") + "\n(人工智能生成，可能有错)"
                    print(response)
                    # activate_wechat_and_send_message(response)
                requested = True
            
            url = ""
            if not requested:
                links = extract_links(item[1])
                print(links)
                if len(links) > 0:
                    url = links[0]
                
            if not requested and item[0][1][0] - item[0][0][0] < 200 and item[0][3][1] - item[0][0][1] > 30 and item[0][0][0] > 400 and item[0][0][0] < 500 and any(name in group_name for name in config["group_name_white_list"]):
                pyautogui.click(item[0][0][0] + 10, item[0][0][1] + 10)
                time.sleep(5)
                screenshot = pyautogui.screenshot()
                screenshot.save('example_screenshot.png')
                time.sleep(0.5)
                result = ocr.ocr('example_screenshot.png')
                print(result)
                response_dict = [[entry[0], entry[1][0], entry[1][1]] for entry in result[0]]

                for item in response_dict:
                    if item[0][0][0] > 150:
                        continue
                    links = extract_links(item[1].replace(' ', ''))
                    if len(links) > 0:
                        url = links[0]

            
            if url:
                markdown_content = get_markdown(url)
                # Extract the first and last 900 characters and concatenate them
                markdown_excerpt = markdown_content[:900] + markdown_content[-900:]
                # print(markdown_content)
                response = get_completion(markdown_excerpt + "总结一下上述内容：", "gpt-3.5-turbo") + "\n(人工智能生成)"
                print(response)
                if any(name in group_name for name in config["group_name_white_list"]):
                    # Send a screenshot
                    activate_wechat_and_send_message(message=response)
                requested = True
                        
                # time.sleep(20)
                # requested = True
        if requested:
            # time.sleep(20)
            for item in filtered_merged_data:
                old.append(item)
            # print(old)
            # 从文件开头开始写入
            f.seek(0)
            f.write(json.dumps(old).encode('utf-8'))
            f.truncate()  # 删除文件中任何剩余的内容


while True:
    print(prob)
    if random.random() > prob:
        autoreply()
    time.sleep(5)

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
