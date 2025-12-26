#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

url = 'https://tv.cctv.com/lm/xwlb/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

print('=== Page Structure Analysis ===')
print(f'Title: {soup.title.get_text() if soup.title else "No title"}')

# Check the main content area
main_content = soup.find('div', class_='w1200')
if main_content:
    print('\nMain content area found, examining its children:')
    for i, child in enumerate(main_content.find_all(recursive=False)):
        print(f'Child {i+1}: {child.name} {child.get("class", [])} {child.get("id", "")}')
        if child.name in ['div', 'ul']:
            # Check if it contains links
            links = child.find_all('a', href=True)
            if links:
                print(f'  Contains {len(links)} links, first 5:')
                for link in links[:5]:
                    print(f'    {link.get_text(strip=True)} -> {link["href"]}')
else:
    print('No main content area found')

# Check all divs with class containing 'list'
print('\n=== All divs with "list" in class ===')
list_divs = soup.find_all('div', class_=lambda x: x and 'list' in x)
for i, div in enumerate(list_divs):
    print(f'Div {i+1}: {div["class"]}')
    links = div.find_all('a', href=True)
    if links:
        print(f'  Contains {len(links)} links, first 3:')
        for link in links[:3]:
            print(f'    {link.get_text(strip=True)} -> {link["href"]}')

# Check for the latest news link specifically
print('\n=== Latest news link analysis ===')
latest_links = soup.find_all('a', href=lambda x: x and 'shtml' in x and 'VIDE' in x)
if latest_links:
    print(f'Found {len(latest_links)} VIDE links, first 5:')
    for link in latest_links[:5]:
        print(f'  {link.get_text(strip=True)} -> {link["href"]}')
