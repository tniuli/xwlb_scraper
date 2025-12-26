#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re

# 复制我们的get_news_content函数，用于测试
def get_news_content_for_test(html_content):
    """测试加粗标签处理逻辑"""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 模拟content_div
    content_div = soup.find("div", id="content")
    if content_div:
        # 模拟标题
        title = "国内联播快讯"
        
        # 特殊处理联播快讯，将内容拆分为单独的新闻条目
        if "联播快讯" in title:
            structured_items = []  # 存储结构化的新闻条目 (标题, 内容)
            
            # 首先尝试使用HTML加粗标签来分割新闻条目
            for p in content_div.find_all(["p", "div"]):
                # 查找当前段落中的所有加粗标签
                bold_tags = p.find_all(["strong", "b"])
                
                if bold_tags:
                    # 如果当前段落有加粗标签
                    for bold_tag in bold_tags:
                        # 提取加粗文本作为新闻标题
                        news_title = bold_tag.get_text(strip=True)
                        
                        # 提取标题后面的内容作为新闻正文
                        next_sibling = bold_tag.next_sibling
                        news_content = ""
                        
                        while next_sibling:
                            # 检查下一个兄弟节点是否是文本节点
                            if hasattr(next_sibling, "strip"):
                                news_content += next_sibling.strip()
                            elif hasattr(next_sibling, "get_text"):
                                news_content += next_sibling.get_text(strip=True)
                            # 安全地获取下一个兄弟节点
                            next_sibling = getattr(next_sibling, "next_sibling", None)
                        
                        # 组合标题和内容
                        if news_title:
                            if news_content:
                                structured_items.append((news_title, news_content))
                            else:
                                # 如果只有标题，查找下一个段落的内容
                                next_p = p.find_next_sibling(["p", "div"])
                                if next_p:
                                    next_content = next_p.get_text(strip=True)
                                    structured_items.append((news_title, next_content))
                                else:
                                    structured_items.append((news_title, ""))
            
            return structured_items
    return []

# 创建测试HTML内容
test_html = '''
<div id="content">
    <p><strong>我国新能源汽车产量突破3000万辆</strong> 工信部今天发布数据显示，今年前11个月，我国新能源汽车产量达到2998万辆，同比增长32.5%，预计全年产量将突破3000万辆大关。</p>
    <p><b>全国冬小麦播种基本完成</b> 农业农村部最新农情调度显示，全国冬小麦播种已经基本完成，播种面积保持稳定。各地正加强田间管理，确保明年夏粮丰收。</p>
    <div><strong>国际油价小幅下跌</strong> 受全球经济增长预期影响，国际油价今天小幅下跌，纽约轻质原油期货价格收于每桶72.5美元，跌幅0.8%。</div>
</div>
'''

# 测试加粗标签处理逻辑
print("测试加粗标签处理逻辑：")
result = get_news_content_for_test(test_html)

if result:
    print(f"成功提取到 {len(result)} 个结构化新闻条目：")
    for i, (title, content) in enumerate(result, 1):
        print(f"\n{i}. 标题：{title}")
        print(f"   内容：{content}")
else:
    print("未能提取到结构化新闻条目")

# 测试输出格式
print("\n\n测试Markdown输出格式：")
print("### 国内联播快讯")
for title, content in result:
    print(f"#### {title}")
    print(f"{content}\n")
