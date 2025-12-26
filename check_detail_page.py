#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

# Use one of the detailed news links from the analysis
detail_url = 'https://tv.cctv.com/2025/12/26/VIDEzxiSOOmMPjQCSNhEqqKc251226.shtml'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(detail_url, headers=headers)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

print('=== Detailed News Page Analysis ===')
print(f'Title: {soup.title.get_text() if soup.title else "No title"}')

# Look for the content area
print('\n=== Looking for content containers ===')

# Try common content container classes
common_containers = [
    soup.find('div', class_='cnt_bd'),
    soup.find('div', class_='content'),
    soup.find('div', id='content'),
    soup.find('article'),
    soup.find('div', class_='text_area'),
    soup.find('div', class_='article_body'),
    soup.find('div', class_='content_area'),
    soup.find('div', class_='main_text')
]

for i, container in enumerate(common_containers):
    if container:
        print(f'Container {i+1}: {container.name} {container.get("class", [])} {container.get("id", "")}')
        
        # Extract text content
        paragraphs = container.find_all(['p', 'div'])
        text_content = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 10:  # Skip short texts
                text_content.append(text)
        
        if text_content:
            print(f'  Contains {len(text_content)} paragraphs, first 5:')
            for para in text_content[:5]:
                print(f'    {para[:100]}...')
            print(f'  Total text length: {sum(len(t) for t in text_content)} characters')

# Check all divs with significant content
print('\n=== All divs with significant content ===')
all_divs = soup.find_all('div')
divs_with_content = []

for div in all_divs:
    text = div.get_text(strip=True)
    if text and len(text) > 50:
        divs_with_content.append((len(text), div))

# Sort by content length, descending
divs_with_content.sort(reverse=True)

for i, (length, div) in enumerate(divs_with_content[:5]):
    print(f'Div {i+1}: {div.name} {div.get("class", [])} {div.get("id", "")}, content length: {length}')
    text = div.get_text(strip=True)
    print(f'  First 150 characters: {text[:150]}...')
