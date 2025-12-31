#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import argparse
from datetime import datetime, timedelta

def get_news_content(url, headers):
    """从单个新闻页面提取详细内容"""
    try:
        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 首先尝试从div id="content"中提取内容，这是详细新闻的主要容器
        content_div = soup.find("div", id="content")
        if content_div:
            # 获取标题
            title = soup.title.get_text(strip=True) if soup.title else "新闻"
            
            # 特殊处理联播快讯，将内容拆分为单独的新闻条目
            if "联播快讯" in title:
                news_items = []
                
                # 首先尝试使用HTML加粗标签来分割新闻条目
                structured_items = []  # 存储结构化的新闻条目 (标题, 内容)
                
                # 查找所有包含加粗标签的元素
                for p in content_div.find_all(["p", "div"]):
                    # 查找当前段落中的所有加粗标签
                    bold_tags = p.find_all(["strong", "b"])
                    
                    if bold_tags:
                        # 如果当前段落有加粗标签
                        for bold_tag in bold_tags:
                            try:
                                # 提取加粗文本作为新闻标题
                                news_title = bold_tag.get_text(strip=True)
                                if not news_title:
                                    continue
                                
                                # 提取标题后面的内容作为新闻正文
                                news_content = ""
                                paragraph_content = []
                                
                                # 先处理当前节点的所有后续兄弟节点
                                current_node = bold_tag.next_sibling
                                while current_node:
                                    try:
                                        if hasattr(current_node, "strip"):
                                            # 文本节点
                                            text = current_node.strip()
                                            if text:
                                                paragraph_content.append(text)
                                        elif hasattr(current_node, "get_text"):
                                            # 元素节点
                                            text = current_node.get_text(strip=True)
                                            if text:
                                                paragraph_content.append(text)
                                        
                                        # 安全获取下一个兄弟节点
                                        current_node = getattr(current_node, "next_sibling", None)
                                    except Exception as e:
                                        print(f"处理节点时出错: {e}")
                                        break
                                
                                # 将段落内容用换行符连接
                                if paragraph_content:
                                    news_content = "\n\n".join(paragraph_content)
                                
                                # 去除标题和内容中的重复部分
                                if news_title in news_content:
                                    news_content = news_content.replace(news_title, "", 1).strip()
                                
                                # 如果当前段落没有内容，查找下一个段落
                                if not news_content:
                                    next_p = p.find_next_sibling(["p", "div"])
                                    if next_p:
                                        next_content = next_p.get_text(strip=True)
                                        # 同样去除重复的标题
                                        if news_title in next_content:
                                            next_content = next_content.replace(news_title, "", 1).strip()
                                        news_content = next_content
                                
                                # 过滤掉无效标题
                                invalid_titles = ['央视网消息', '新闻联播', '(新闻联播)', '央视网消息（新闻联播）']
                                if any(invalid in news_title for invalid in invalid_titles):
                                    continue
                                
                                # 添加到结构化条目
                                structured_items.append((news_title, news_content))
                            except Exception as e:
                                print(f"处理加粗标签时出错: {e}")
                                continue
                
                # 如果使用加粗标签成功提取到新闻条目
                news_items = []
                has_structured_content = False  # 标记是否有结构化内容
                
                if structured_items and len(structured_items) > 1:
                    # 从结构化条目创建纯文本条目用于返回
                    news_items = [title + content for title, content in structured_items]
                    has_structured_content = True
                else:
                    # 使用传统的文本处理方法作为备选
                    # 首先提取所有段落内容
                    # 只处理最外层的p元素，避免父元素和子元素的文本都被提取导致重复
                    paragraphs = content_div.find_all("p")
                    text_content = []
                    
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 10:  # 跳过太短的文本
                            # 去除重复的标题行
                            if "央视网消息（新闻联播）" in text and text_content and "央视网消息（新闻联播）" in text_content[0]:
                                continue
                            text_content.append(text)
                    
                    if text_content:
                        # 组合内容，保持段落结构，段落之间空一行
                        content = "\n\n".join([p.strip() for p in text_content if p.strip()])
                        # 标准化换行符，保留段落之间的空行（将三个或更多换行符替换为两个）
                        content = re.sub(r"[\r\n]{3,}" , "\n\n", content)
                        # 去掉编辑信息和责任编辑信息
                        content = re.sub(r"编辑：.*?责任编辑：.*?", "", content)
                        content = re.sub(r"刘亮", "", content)
                        content = re.sub(r"编辑：.*?", "", content)
                        content = re.sub(r"责任编辑：.*?", "", content)
                        # 去掉重复内容
                        content = re.sub(r"(.+?)\n\1\n", "\1\n", content)
                        # 移除所有位置的"央视网消息（新闻联播）："
                        content = re.sub(r"央视网消息（新闻联播）：", "", content)
                        
                        # 使用更精确的文本模式匹配来分割新闻条目
                        # 基于常见的新闻条目开头模式：数字+条、日期、地点/机构等
                        # 使用正向前瞻确保只匹配完整的条目开头
                        # 保留换行符，只清理多余空格
                        content = re.sub(r"[ \t]+", " ", content).strip()  # 清理多余空格和制表符，保留换行符
                        
                        # 定义新闻条目开头的模式
                        # 使用非捕获组来定义开头模式，然后匹配到下一个开头模式之前的内容
                        entry_pattern = r"((?:[0-9]+条|今天|昨日|近日|[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|国家|上海|北京|广东|海南|福建|山东|江苏|浙江|河北|河南|湖北|湖南|四川|陕西|甘肃|青海|新疆|西藏|内蒙古|辽宁|吉林|黑龙江|天津|重庆|广西|宁夏|山西|安徽|江西|贵州|云南|香港|澳门|台湾|美国|英国|法国|德国|日本|韩国|俄罗斯|联合国|国际|黎巴嫩|以色列|伊朗)[^。！？]*[。！？]+(?:[^。！？]*[。！？]+)*?)(?=(?:[0-9]+条|今天|昨日|近日|[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|国家|上海|北京|广东|海南|福建|山东|江苏|浙江|河北|河南|湖北|湖南|四川|陕西|甘肃|青海|新疆|西藏|内蒙古|辽宁|吉林|黑龙江|天津|重庆|广西|宁夏|山西|安徽|江西|贵州|云南|香港|澳门|台湾|美国|英国|法国|德国|日本|韩国|俄罗斯|联合国|国际|黎巴嫩|以色列|伊朗)[^。！？]*[。！？]|$)"
                        
                        # 查找所有匹配的完整条目
                        news_items = re.findall(entry_pattern, content, re.DOTALL)
                
                # 清理空条目
                news_items = [item.strip() for item in news_items if item.strip()]
                
                # 去重处理
                seen_items = set()
                unique_news_items = []
                for item in news_items:
                    if item not in seen_items:
                        seen_items.add(item)
                        unique_news_items.append(item)
                news_items = unique_news_items
                
                # 重新组合内容，每条快讯之间用空行分隔
                content = "\n\n".join(news_items)
                
                # 去掉编辑信息和责任编辑信息
                content = re.sub(r"编辑：.*?责任编辑：.*?", "", content)
                content = re.sub(r"刘亮", "", content)
                content = re.sub(r"编辑：.*?", "", content)
                content = re.sub(r"责任编辑：.*?", "", content)
                # 去掉重复内容
                content = re.sub(r"(.+?)\n\1\n", "\1\n", content)
                # 去掉多余的空行
                content = re.sub(r"\n\n+", "\n\n", content).strip()
                
                # 对结构化内容中的编辑信息和多余文本进行清理
                if has_structured_content and structured_items:
                    cleaned_structured_items = []
                    seen_titles = set()
                    for item_title, item_content in structured_items:
                        # 清理标题
                        item_title = item_title.strip()
                        item_title = re.sub(r"央视网消息（新闻联播）：", "", item_title)
                        
                        # 清理内容
                        item_content = item_content.strip()
                        item_content = re.sub(r"编辑：.*?责任编辑：.*?", "", item_content)
                        item_content = re.sub(r"刘亮", "", item_content)
                        item_content = re.sub(r"编辑：.*?", "", item_content)
                        item_content = re.sub(r"责任编辑：.*?", "", item_content)
                        item_content = re.sub(r"央视网消息（新闻联播）：", "", item_content)
                        
                        # 只保留非空且不重复的条目
                        if item_title and item_content and item_title not in seen_titles:
                            seen_titles.add(item_title)
                            cleaned_structured_items.append((item_title, item_content))
                    structured_items = cleaned_structured_items
                    has_structured_content = len(structured_items) > 0
                
                # 返回结果时包含结构化内容
                return {
                    "title": title,
                    "url": url,
                    "content": content,
                    "structured_content": structured_items if has_structured_content else None
                }
            else:
                # 提取所有段落内容（非联播快讯的普通新闻）
                # 只处理最外层的p元素，避免父元素和子元素的文本都被提取导致重复
                paragraphs = content_div.find_all("p")
                text_content = []
                
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 10:  # 跳过太短的文本
                        # 去除重复的标题行
                        if "央视网消息（新闻联播）" in text and text_content and "央视网消息（新闻联播）" in text_content[0]:
                            continue
                        text_content.append(text)
                
                if text_content:
                    # 组合内容，保持段落结构，段落之间空一行
                    content = "\n\n".join([p.strip() for p in text_content if p.strip()])
                    # 标准化换行符，保留段落之间的空行（将三个或更多换行符替换为两个）
                    content = re.sub(r"[\r\n]{3,}" , "\n\n", content)
                    # 去掉编辑信息和责任编辑信息
                    content = re.sub(r"编辑：.*?责任编辑：.*?", "", content)
                    content = re.sub(r"刘亮", "", content)
                    content = re.sub(r"编辑：.*?", "", content)
                    content = re.sub(r"责任编辑：.*?", "", content)
                    # 去掉重复内容
                    content = re.sub(r"(.+?)\n\1\n", "\n", content)
                    # 去掉多余的空行
                    content = re.sub(r"\n\n+", "\n\n", content).strip()
                
                # 去掉多余的空行
                content = re.sub(r"\n\n+", "\n\n", content).strip()
                # 移除所有位置的"央视网消息（新闻联播）："
                content = re.sub(r"央视网消息（新闻联播）：", "", content)
                return {
                    "title": soup.title.get_text(strip=True) if soup.title else "新闻",
                    "url": url,
                    "content": content
                }
        
        # 如果没找到，尝试其他方法
        content = ""
        
        # 尝试查找常见的正文容器
        possible_containers = [
            soup.find("div", class_="cnt_bd"),
            soup.find("div", class_="content"),
            soup.find("article"),
            soup.find("div", class_="text_area"),
            soup.find("div", class_="article_body"),
            soup.find("div", class_="content_area"),
        ]
        
        for container in possible_containers:
            if container:
                # 只处理最外层的p元素，避免父元素和子元素的文本都被提取导致重复
                paragraphs = container.find_all("p")
                if paragraphs:
                    # 提取每个段落的文本并保持段落结构，段落之间空一行
                    paragraph_texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                    content = "\n\n".join(paragraph_texts)
                    break
        
        # 标准化换行符，保留段落之间的空行（将三个或更多换行符替换为两个）
        content = re.sub(r"[\r\n]{3,}" , "\n\n", content)
        # 移除所有位置的"央视网消息（新闻联播）："
        content = re.sub(r"央视网消息（新闻联播）：", "", content)
        
        return {
            "title": soup.title.get_text(strip=True) if soup.title else "新闻",
            "url": url,
            "content": content
        }
        
    except Exception as e:
        print(f"提取单个新闻内容时出错 ({url}): {e}")
        return None

def get_latest_xwlb_text(target_date=None):
    """抓取指定日期或最新一天的新闻联播文字版，包括每条新闻的详细内容"""
    base_url = "https://tv.cctv.com"
    list_url = f"{base_url}/lm/xwlb/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # 1. 获取新闻列表页
        print("正在请求新闻列表页...")
        response = requests.get(list_url, headers=headers)
        response.encoding = "utf-8"
        
        # 2. 解析页面，找到最新的新闻链接
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 查找所有包含日期的VIDE链接，这些是新闻视频链接
        all_links = soup.find_all("a", href=True)
        
        # 收集所有VIDE链接，去重
        vide_links = []
        seen = set()
        
        for link in all_links:
            href = link["href"]
            if "shtml" in href and "VIDE" in href:
                full_href = href if href.startswith("http") else f"{base_url}{href}"
                if full_href not in seen:
                    seen.add(full_href)
                    vide_links.append(full_href)
        
        if not vide_links:
            print("\n未找到最新新闻链接")
            return None
        
        print(f"找到 {len(vide_links)} 个VIDE链接")
        
        # 根据目标日期过滤链接（如果提供了目标日期）
        filtered_links = []
        if target_date:
            target_date_str = target_date.strftime("%Y/%m/%d")
            target_date_url = f"{base_url}/{target_date_str}/"
            
            # 1. 先尝试在当前列表页中查找指定日期的链接
            for link in vide_links:
                if target_date_str in link:
                    filtered_links.append(link)
            
            # 2. 如果当前列表页中没有找到，尝试多种方式获取历史新闻
            if not filtered_links:
                print(f"当前列表页中未找到{target_date.strftime('%Y年%m月%d日')}的新闻链接，尝试其他方式获取...")
                
                # 尝试1: 直接构建日期对应的完整新闻链接
                print("尝试直接构建日期对应的新闻链接...")
                target_date_num = target_date.strftime("%Y%m%d")
                
                # 基于观察到的URL格式模式，构建可能的完整新闻链接
                # 完整新闻通常以VIDE0开头
                possible_news_urls = [
                    # 尝试多种可能的完整新闻链接格式
                    f"{base_url}/{target_date_str}/VIDE0{target_date_num[-4:]}{target_date_num}*.shtml",
                    f"{base_url}/{target_date_str}/VIDE0{target_date_num}*.shtml",
                    f"{base_url}/{target_date_str}/VIDEA{target_date_num[-4:]}{target_date_num}*.shtml",
                    f"{base_url}/{target_date_str}/VIDEA{target_date_num}*.shtml"
                ]
                
                # 尝试2: 尝试不同的历史新闻列表页URL格式
                date_list_urls = [
                    # 正确的历史新闻URL格式，从xwlb_data.js文件中发现
                    f"{base_url}/lm/xwlb/day/{target_date_num}.shtml",
                    # 尝试其他可能的格式
                    f"{base_url}/lm/xwlb/data/index_{target_date_num}.shtml",
                    f"{base_url}/lm/xwlb/data/{target_date_num}.shtml",
                    f"{base_url}/lm/xwlb/{target_date_num}.shtml"
                ]
                
                # 先尝试历史新闻列表页
                for date_list_url in date_list_urls:
                    if filtered_links:  # 如果已经找到链接，停止尝试
                        break
                    
                    try:
                        print(f"  尝试访问历史新闻列表页: {date_list_url}")
                        date_response = requests.get(date_list_url, headers=headers)
                        
                        # 检查响应状态
                        if date_response.status_code != 200:
                            print(f"  页面访问失败 (状态码: {date_response.status_code})")
                            continue
                            
                        date_response.encoding = "utf-8"
                        date_soup = BeautifulSoup(date_response.text, "html.parser")
                        
                        # 从特定日期的列表页中提取VIDE链接
                        date_all_links = date_soup.find_all("a", href=True)
                        for link in date_all_links:
                            href = link["href"]
                            if "shtml" in href and "VIDE" in href:
                                full_href = href if href.startswith("http") else f"{base_url}{href}"
                                if full_href not in seen:
                                    seen.add(full_href)
                                    if target_date_str in full_href:
                                        filtered_links.append(full_href)
                        
                        if filtered_links:
                            print(f"  从{date_list_url}找到 {len(filtered_links)} 个{target_date.strftime('%Y年%m月%d日')}的VIDE链接")
                            break
                            
                    except Exception as e:
                        print(f"  访问{date_list_url}时出错: {e}")
                        continue
                
                # 如果还是没找到，直接检查日期目录下的内容
                if not filtered_links:
                    print("尝试检查日期目录下的内容...")
                    # 尝试访问日期目录页
                    date_dir_url = f"{base_url}/{target_date_str}/"
                    try:
                        response = requests.get(date_dir_url, headers=headers)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, "html.parser")
                            all_links = soup.find_all("a", href=True)
                            for link in all_links:
                                href = link["href"]
                                if "shtml" in href and "VIDE" in href:
                                    full_href = href if href.startswith("http") else f"{base_url}{href}"
                                    if full_href not in seen:
                                        seen.add(full_href)
                                        if target_date_str in full_href:
                                            filtered_links.append(full_href)
                    except Exception as e:
                        print(f"访问日期目录时出错: {e}")
            
            # 如果还是没找到，尝试直接构建单个新闻链接（不依赖列表页）
            if not filtered_links:
                print(f"尝试直接构建{target_date.strftime('%Y年%m月%d日')}的单个新闻链接...")
                
                # 根据观察到的URL格式，构建可能的新闻链接目录并尝试获取内容
                # 注意：由于URL中包含随机字符，无法直接构建完整链接
                # 但我们可以尝试从日期目录获取所有链接
                date_news_dir = f"{base_url}/{target_date_str}/"
                try:
                    # 直接请求日期目录，查看是否有可用的新闻链接
                    dir_response = requests.get(date_news_dir, headers=headers)
                    if dir_response.status_code == 200:
                        dir_soup = BeautifulSoup(dir_response.text, "html.parser")
                        
                        # 查找所有链接，筛选出包含VIDE的新闻链接
                        all_news_links = dir_soup.find_all("a", href=True)
                        for link in all_news_links:
                            href = link["href"]
                            if "shtml" in href and "VIDE" in href:
                                full_href = href if href.startswith("http") else f"{base_url}{href}"
                                if full_href not in seen:
                                    seen.add(full_href)
                                    filtered_links.append(full_href)
                except Exception as e:
                    print(f"访问日期新闻目录时出错: {e}")
            
            if not filtered_links:
                print(f"未找到{target_date.strftime('%Y年%m月%d日')}的新闻链接")
                print(f"提示：")
                print(f"1. 当前列表页只包含{vide_links[0][20:30]}左右的最新新闻")
                print(f"2. CCTV网站可能不提供通过直接URL访问历史新闻的功能")
                print(f"3. 网站可能有防爬机制，限制自动化访问历史新闻")
                print(f"4. 您可以尝试：")
                print(f"   - 手动访问CCTV新闻联播页面寻找历史新闻")
                print(f"   - 使用当前日期或最近日期的新闻")
                print(f"   - 检查网络连接或尝试使用不同的网络环境")
                return None
            
            print(f"找到 {len(filtered_links)} 个{target_date.strftime('%Y年%m月%d日')}的VIDE链接")
            vide_links = filtered_links
        
        # 获取最新的新闻联播完整视频链接
        latest_news_url = None
        for link in vide_links:
            if "VIDE0" in link:  # 完整新闻通常以VIDE0开头
                latest_news_url = link
                break
        
        # 如果没找到VIDE0开头的，就用第一个
        if not latest_news_url:
            latest_news_url = vide_links[0]
        
        print(f"使用完整新闻链接: {latest_news_url}")
        
        # 3. 请求新闻详情页，获取新闻大纲和单个新闻链接
        print("正在请求新闻详情页...")
        news_response = requests.get(latest_news_url, headers=headers)
        news_response.encoding = "utf-8"
        news_soup = BeautifulSoup(news_response.text, "html.parser")
        
        # 提取完整新闻标题
        title = news_soup.title.get_text(strip=True) if news_soup.title else "新闻联播"
        
        # 4. 从列表页获取所有单个新闻链接（除了完整新闻）
        print("\n提取单个新闻链接...")
        news_item_links = []
        
        for link in vide_links:
            if link != latest_news_url:  # 排除完整新闻链接
                news_item_links.append(link)
        
        print(f"找到 {len(news_item_links)} 个单个新闻链接")
        
        # 5. 从单个新闻链接中提取大纲和详细内容
        print("\n提取新闻大纲和详细内容...")
        
        # 先获取所有单个新闻的内容，然后组合大纲
        detailed_news = []
        outline_items = []
        
        for i, news_url in enumerate(news_item_links[:20]):  # 最多处理20条新闻
            print(f"  正在抓取第 {i+1}/{len(news_item_links)} 条: {news_url}")
            news_content = get_news_content(news_url, headers)
            
            if news_content and news_content["content"]:
                detailed_news.append(news_content)
                
                # 提取大纲标题（从标题中提取）
                news_title = news_content["title"]
                # 清理标题，去除[视频]前缀和其他多余内容
                news_title = re.sub(r"^\[视频\]", "", news_title).strip()
                outline_items.append(news_title)
        
        # 6. 生成大纲内容
        outline_content = ""
        if outline_items:
            outline_content = "\n".join([f"- {title}" for i, title in enumerate(outline_items)])
        
        # 7. 组合最终内容
        print("\n组合最终内容...")
        
        # 先添加标题（使用Markdown一级标题）
        # 清理标题，确保它是用户要求的格式：YYYY年MM月DD日新闻联播文字版｜
        date_str = ""
        # 优先使用用户提供的日期
        if target_date:
            date_str = target_date.strftime("%Y年%m月%d日")
        else:
            # 尝试从URL中提取日期信息（URL格式更一致）
            date_match = re.search(r'(\d{4})/(\d{2})/(\d{2})', latest_news_url)
            if date_match:
                # 格式化为YYYY年MM月DD日格式
                date_str = f"{date_match.group(1)}年{date_match.group(2)}月{date_match.group(3)}日"
            else:
                # 如果URL中没有找到日期，尝试从标题中提取
                date_match = re.search(r'(\d{4})(\d{2})(\d{2})', title)
                if date_match:
                    date_str = f"{date_match.group(1)}年{date_match.group(2)}月{date_match.group(3)}日"
        # 在开头添加图片
        final_content = f"![](https://files.mdnice.com/user/158914/f297f420-0530-4a26-8d81-0644824ee6e0.jpg)\n\n"
        # 生成用户要求的标题格式
        clean_main_title = f"{date_str}新闻联播文字版｜｜｜｜" if date_str else "新闻联播文字版｜｜｜｜"
        final_content += f"{clean_main_title}\n\n"
        # 添加大纲（使用Markdown五级标题）
        if outline_content:
            final_content += "# 新闻大纲\n"
            final_content += outline_content
            final_content += "\n\n"
        
        # 再添加每个新闻的详细内容（使用Markdown五级标题）
        if detailed_news:
            final_content += "# 详细新闻\n\n"
            
            for i, news in enumerate(detailed_news):
                # 清理标题，去除[视频]前缀
                clean_title = re.sub(r"^\[视频\]", "", news['title']).strip()
                
                # 使用Markdown六级标题
                final_content += f"## {clean_title}\n"
                
                # 特殊处理联播快讯
                if "联播快讯" in clean_title:
                    # 优先使用结构化内容
                    if news.get("structured_content"):
                        for title_part, content_part in news["structured_content"]:
                            title_part = title_part.strip()
                            content_part = content_part.strip()
                            
                            if not title_part and not content_part:
                                continue
                                
                            # 确保标题不为空
                            if not title_part:
                                title_part = "新闻快讯"
                            
                            # 使用Markdown七级标题
                            final_content += f"### {title_part}\n"
                            
                            # 输出内容部分
                            if content_part:
                                final_content += f"{content_part}\n\n"
                    else:
                        # 没有结构化内容时，使用传统的分割方法
                        news_items = news['content'].split("\n\n")
                        
                        for item in news_items:
                            item = item.strip()
                            if not item:
                                continue
                                
                            # 提取新闻标题（更加智能的方式）
                            title_part = ""
                            
                            # 尝试查找合适的标题
                            if len(item) > 50:
                                # 情况1：查找第一个标点符号（。、：）前的内容作为标题
                                for punc in ["。", "、", "：", "，"]:
                                    if punc in item[:100]:
                                        title_part = item.split(punc, 1)[0].strip() + punc
                                        break
                            
                            # 如果没有找到合适的标点符号
                            if not title_part:
                                # 情况2：查找日期前的内容
                                date_match = re.search(r"(今天|昨日|近日|[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)", item)
                                if date_match:
                                    title_part = item[:date_match.start()].strip()
                                    if title_part:
                                        # 确保标题以标点符号结尾
                                        if not title_part.endswith(("。", "、", "：", "，")):
                                            title_part += "："
                                else:
                                    # 情况3：使用前70个字符作为标题
                                    title_part = item[:70].strip()
                                    if len(item) > 70:
                                        title_part += "..."
                            
                            # 确保标题不为空
                            if not title_part:
                                title_part = "新闻快讯"
                            
                            # 使用Markdown三级标题
                            final_content += f"# {title_part}\n"
                            
                            # 只输出item中除标题外的内容部分
                            if title_part in item:
                                # 去掉标题部分，只保留正文
                                content_part = item.replace(title_part, "", 1).strip()
                                if content_part:
                                    final_content += f"{content_part}\n\n"
                            else:
                                # 如果标题不在item中，输出完整内容
                                final_content += f"{item}\n\n"
                else:
                    # 普通新闻，直接添加内容
                    final_content += f"{news['content']}\n\n"
        
        # 如果没有获取到详细内容，尝试直接从页面提取大纲
        if not detailed_news and not outline_content:
            print("\n尝试从完整新闻页面提取大纲...")
            
            # 查找页面中的所有div，寻找包含新闻大纲的内容
            all_divs = news_soup.find_all("div")
            
            for div in all_divs:
                text = div.get_text(strip=True)
                if text and len(text) > 500:  # 寻找较长的文本内容
                    # 检查是否包含新闻条目格式
                    if re.search(r"1\..*?2\..*?3\.", text, re.DOTALL):
                        outline_content = text
                        break
            
            if outline_content:
                # 清理大纲内容
                outline_content = re.sub(r"\s+" , " ", outline_content).strip()
                final_content += "【新闻大纲】\n"
                final_content += outline_content
        
        print(f"\n成功提取到完整新闻内容，总长度: {len(final_content)}字符")
        
        print(f"\n标题: {title}")
        if outline_content:
            print(f"\n新闻大纲预览:\n{outline_content[:500]}...")
        
        return {
            "title": title,
            "url": latest_news_url,
            "content": final_content,
            "outline": outline_content,
            "detailed_news": detailed_news
        }
        
    except Exception as e:
        print(f"抓取过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_news_outline(content):
    """从新闻内容中提取标题大纲"""
    outline = []
    
    # 匹配主要新闻条目，确保只匹配完整的序号，如"1."而不是"664.1"中的"664."
    # 使用正向肯定前瞻，确保序号后是空格或中文字符
    main_items = re.findall(r"(\d+)\.(?![0-9])(.*?)(?=\d+\.(?![0-9])|$)", content, re.DOTALL)
    
    for num, title in main_items:
        # 清理标题，只保留核心内容
        title = title.strip()
        if title and len(title) > 5:
            # 如果标题包含小标题（如国内联播快讯），提取小标题
            if "联播快讯" in title:
                # 提取快讯标题
                outline.append(f"{num}. {title.split('：')[0]}：")
                # 提取快讯中的小条目
                sub_items = re.findall(r"(\([0-9]+\))(.*?)(?=\([0-9]+\)|$)", title, re.DOTALL)
                for sub_num, sub_title in sub_items:
                    sub_title = sub_title.strip()
                    if sub_title and len(sub_title) > 2:
                        outline.append(f"  {sub_num} {sub_title.split('；')[0]}")
            else:
                # 普通新闻条目，只提取核心标题
                outline.append(f"{num}. {title.split('；')[0]}")
    
    return outline

def save_to_file(data, filename=None):
    """将抓取的内容保存到文件，按照用户要求的Markdown格式，文件名包含新闻日期"""
    if not data:
        return
    
    # 直接使用get_latest_xwlb_text函数生成的Markdown格式内容
    content = data['content']
    
    # 从内容中提取日期（格式：YYYY年MM月DD日）
    content = data['content']
    date_match = re.search(r'(\d{4}年\d{2}月\d{2}日)', content)
    
    if date_match:
        date_str = date_match.group(1)
        filename = f"{date_str}新闻联播文字版.txt"
    else:
        # 如果没有从内容中提取到日期，使用默认文件名
        filename = "新闻联播文字版.txt"
    
    # 1. 写入文件
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\n新闻内容已保存到文件: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取指定日期的新闻联播文字版")
    parser.add_argument("--date", help="指定日期（格式：YYYYMMDD），默认抓取最新日期", type=str)
    args = parser.parse_args()
    
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y%m%d")
        except ValueError:
            print("日期格式错误，请使用YYYY-MM-DD格式")
            exit(1)
    
    print("开始抓取新闻联播文字版..." + (f"（日期：{target_date.strftime('%Y年%m月%d日')}）" if target_date else "（最新日期）"))
    xwlb_data = get_latest_xwlb_text(target_date)
    if xwlb_data:
        save_to_file(xwlb_data)
        print("\n抓取完成！")
    else:
        print("\n抓取失败！")