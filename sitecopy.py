#!/usr/bin/env python
# coding: utf-8
# Author: Threezh1
# Blog 	: http://www.threezh1.com/
# Github: https://github.com/Threezh1

import requests, urllib, os, asyncio, functools, argparse, sys
from pathlib import Path
from bs4 import BeautifulSoup
from requests.packages import urllib3
from requests.adapters import HTTPAdapter

Welcome = """
 .▄▄ · ▪  ▄▄▄▄▄▄▄▄ . ▄▄·        ▄▄▄· ▄· ▄▌
 ▐█ ▀. ██ •██  ▀▄.▀·▐█ ▌▪▪     ▐█ ▄█▐█▪██▌
 ▄▀▀▀█▄▐█· ▐█.▪▐▀▀▪▄██ ▄▄ ▄█▀▄  ██▀·▐█▌▐█▪
 ▐█▄▪▐█▐█▌ ▐█▌·▐█▄▄▌▐███▌▐█▌.▐▌▐█▪·• ▐█▀·.
  ▀▀▀▀ ▀▀▀ ▀▀▀  ▀▀▀ ·▀▀▀  ▀█▄▀▪.▀     ▀ • """

Information = r"""
 Author: 	Threezh1
 Blog:		http://www.threezh1.com/
 Version:	1.0"""

Help = r"""
 Uage: README.md
 Stop Copy: Ctrl + C
"""

urllib3.disable_warnings()
header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36",}

def parse_args():
    parser = argparse.ArgumentParser(epilog='\tExample: \r\npython ' + sys.argv[0] + " -u http://www.baidu.com")
    parser.add_argument("-u", "--url", help="The address where you want to get the source code")
    parser.add_argument("-s", "--urls",help="Download multiple urls")
    parser.add_argument("-d", "--depth",help="Number of loops to get links")
    parser.add_argument("-t", "--threads",help="Number of threads for task execution")
    parser.add_argument("-e", "--entire",help="Download entire website", action="store_true")
    return parser.parse_args()

# Get the page source
def ExtractContent(url):
	try:
		raw = requests.get(url, headers = header, timeout=10, allow_redirects=True, verify=False)
		raw = raw.content
		if raw != "":
			return raw
	except Exception as e:
		print("[error] - " + url)
		#print(e)
		return None

def Md5Encrypt(text):
	import hashlib
	hl = hashlib.md5()
	hl.update(text.encode(encoding='utf-8'))
	return hl.hexdigest()

def GetUrlPart(url, part = ""):
	from urllib.parse import urlparse
	# http://www.example.com/a/b/index.php?id=1#h1
	# domain : www.example.com
	# scheme : http
	# path   : /a/b/index.php
	# id=1   : id=1
	# fragment : h1
	# completepath : /a/b/
	# completedomain : http://www.example.com
	# filename : index.php
	# filesuffix : php

	if url.startswith("http") == False:
		if part == "path":
			return url[:url.rfind("/") + 1]
		if part == "filename":
			temp = url[url.rfind("/") + 1:]
			if temp.find("?") != -1:
				temp = temp[:temp.find("?")]
			if temp.find("#") != -1:
				temp = temp[:temp.find("#")]
			return temp
	else:
		pass
	try:
		parsed = urlparse(url)
	except:
		return ""
	if part == "domain":
		return parsed.netloc
	elif part == "scheme":
		return parsed.scheme
	elif part == "path":
		return parsed.path
	elif part == "query":
		return parsed.query
	elif part == "fragment":
		return parsed.fragment
	elif part == "completepath":
		return parsed.path[:parsed.path.rfind("/") + 1]
	elif part == "completedomain":
		return (parsed.scheme + "://" + parsed.netloc)
	elif part == "filename": 
		return parsed.path[parsed.path.rfind("/") + 1:]
	elif part == "filesuffix": 
		temp = parsed.path[parsed.path.rfind("/") + 1:]
		if temp.find(".") == -1: return ""
		return temp[temp.find("."):]
	else:
		return parsed

def ProcessResourcePath(pages_url, source_url):
	""" Handle the relationship between relative paths and absolute paths, and give replacement results and save paths """
	
	source_download_url = ""
	processed_source_url = ""
	source_save_path = ""
	source_url_kind = 0
	
	relative_path = ""
	url_path = GetUrlPart(pages_url, "completepath")
	for i in range(url_path.count("/") - 1):
		relative_path += "../"
	# process others
	if_others = False
	if source_url.startswith("data:image") == False:
		# process absolute and special path
		if_abslote_url = False
		if source_url.startswith("http"):
			source_url_kind = 1
			source_download_url = source_url
			if_abslote_url = True
		elif source_url.startswith("//"):
			source_url_kind = 2
			source_download_url = GetUrlPart(pages_url, "scheme") + ":" + source_url
			if_abslote_url = True

		if_special_url = False
		if source_url.startswith("../"):
			source_url_kind = 3
			cleared_source_url = GetUrlPart(source_url, "filename")
			cleared_source_path = GetUrlPart(source_url, "path").replace("../", "")
			temp = url_path
			for i in range(source_url.count("../") + 1):
				temp = temp[:temp.rfind("/")]
			absolte_url_path = temp + "/"
			source_download_url = GetUrlPart(pages_url, "completedomain") + absolte_url_path + cleared_source_path + cleared_source_url
			temp = relative_path
			for i in range(source_url.count("../") + 1):
				temp = temp[:temp.rfind("/") + 1]
			processed_source_url = source_url
			if absolte_url_path.startswith("/"):absolte_url_path = absolte_url_path[1:]
			source_save_path = absolte_url_path + cleared_source_path + cleared_source_url
			if_special_url = True
		elif source_url.startswith("/") and source_url.startswith("//") == False and source_url.startswith("/./") == False:
			source_url_kind = 4
			source_download_url = GetUrlPart(pages_url, "completedomain") + source_url
			if relative_path == "":
				processed_source_url = GetUrlPart(source_url, "path")[1:] + GetUrlPart(source_url, "filename")
			else:
				processed_source_url = relative_path[:-1] + GetUrlPart(source_url, "path") + GetUrlPart(source_url, "filename")
			source_save_path = GetUrlPart(source_url, "path")[1:] + GetUrlPart(source_url, "filename")
			if_special_url = True
		elif source_url.startswith("/./"):
			source_url_kind = 5
			source_download_url =  GetUrlPart(pages_url, "completedomain") + "/" + source_url[3:]
			processed_source_url = relative_path + GetUrlPart(source_url, "path")[3:] + GetUrlPart(source_url, "filename")
			source_save_path = GetUrlPart(source_url, "path")[3:] + GetUrlPart(source_url, "filename")
			if_special_url = True

		# process relative path
		if if_abslote_url == True:
			temp_source_name = Md5Encrypt(source_url) + GetUrlPart(source_download_url, "filesuffix")
			processed_source_url = relative_path + "nopathsource/" + temp_source_name
			source_save_path = "nopathsource/" + temp_source_name
		elif if_special_url == True: pass
		elif source_url.startswith("./"):
			source_url_kind = 6
			cleared_source_url = GetUrlPart(source_url[2:], "path") + GetUrlPart(source_url, "filename")
		else:
			source_url_kind = 7
			cleared_source_url = GetUrlPart(source_url, "path") + GetUrlPart(source_url, "filename")

		if if_abslote_url == False and if_special_url == False:
			source_download_url = GetUrlPart(pages_url, "completedomain") + GetUrlPart(pages_url, "completepath") + cleared_source_url
			processed_source_url = cleared_source_url
			source_save_path = url_path[1:] + cleared_source_url
	else:
		source_url_kind = 0
	result = {
		"pages_url": pages_url,
		"source_url": source_url,
		"source_download_url": source_download_url,
		"processed_source_url": processed_source_url,
		"source_save_path": source_save_path,
		"source_url_kind": source_url_kind
	}
	return result

def IfBlackName(black_name_list, text, kind=1):
	# 1: equal
	# 2: exist
	# 3: startswith
	for temp in black_name_list:
		if kind == 1:
			if text == temp:
				return True
		if kind == 2:
			if text.find(temp) != -1:
				return True
		if kind == 3:
			if text.startswith(temp):
				return True
	return False

def ExtractLinks(url, lable_name, attribute_name):
	single_black_names = ["/", "#"]
	starts_black_names = ["#", "javascript:"]
	html_raw = ExtractContent(url)
	if html_raw == None: return []
	html = BeautifulSoup(html_raw.decode("utf-8", "ignore"), "html.parser")
	lables = html.findAll({lable_name})
	old_links = []
	for lable in lables:
		lable_attribute = lable.get(attribute_name)
		if lable_attribute == None or lable_attribute == "": continue
		lable_attribute = lable_attribute.strip()
		if IfBlackName(single_black_names, lable_attribute): continue 
		if IfBlackName(starts_black_names, lable_attribute, 3): continue
		if lable_attribute not in old_links:
			old_links.append(lable_attribute)
	return old_links

def SaveFile(file_content, file_path, utf8=False):
	processed_path = urllib.parse.unquote(file_path)
	try:
		path = Path(GetUrlPart(processed_path, "path"))
		path.mkdir(parents=True, exist_ok=True)
		if utf8 == False:
			with open(processed_path, "wb") as fobject:
				fobject.write(file_content)
		else:
			with open(processed_path, "w", encoding="utf-8") as fobject:
				fobject.write(file_content)
	except Exception as e:
		print("[error] - " + file_path)
		#print(e)

def ProcessLink(page_url, link, if_page_url = False):
	temp = ProcessResourcePath(page_url, link)
	processed_link = temp["source_download_url"]
	if GetUrlPart(page_url, "domain") != GetUrlPart(processed_link, "domain"): return None
	if if_page_url == True:
		processed_link = GetUrlPart(processed_link, "completedomain") + GetUrlPart(processed_link, "path")
	else:
		temp = ProcessResourcePath(page_url, link)
		processed_link = temp["processed_source_url"]
	url_filename = GetUrlPart(processed_link, "filename")
	url_suffix = GetUrlPart(processed_link, "filesuffix")
	if url_suffix == ".html":
		pass
	elif url_filename == "":
		processed_link += "index.html"
	else:
		processed_link += ".html"
	if if_page_url == False:
		if processed_link.startswith("/"):
			processed_link = processed_link[1:]
	return processed_link

def SaveSinglePage(page_url):
	domain = GetUrlPart(page_url, "domain")
	domain_path = domain.replace(".", "_")
	processed_page_url = ProcessLink("http://" + domain, page_url, True)
	page_save_path = "website/" + domain_path + "/" + GetUrlPart(processed_page_url, "path")
	if os.path.exists(page_save_path) == True: 
		print("[Info] - " + page_url + " Downloaded")
		return None
	print("[Processing] - " + page_url)	
	links_js = ExtractLinks(page_url, "script", "src")
	links_css = ExtractLinks(page_url, "link", "href")
	links_img = ExtractLinks(page_url, "img", "src")
	links_a = ExtractLinks(page_url, "a", "href")
	links_all = links_js + links_css + links_img
	page_raw = ExtractContent(page_url)
	if page_raw == None: return None
	page_raw = page_raw.decode("utf-8", "ignore")
	processed_links = []
	for link in links_all:
		link_info = ProcessResourcePath(page_url, link.strip())
		try:
			page_raw = page_raw.replace(link, link_info["processed_source_url"])
		except Exception as e:
			print(e)
			continue
		source_save_path = "website/" + domain_path + "/" + link_info["source_save_path"]
		source_save_path.replace("\\\\", "")
		if os.path.exists(source_save_path) == True: continue
		source_raw = ExtractContent(link_info["source_download_url"])
		#print(source_save_path)
		if source_raw == None: continue
		SaveFile(source_raw, source_save_path)
	links = []
	links_copy = []
	for link_a in links_a:
		processed_link = ProcessLink(page_url, link_a)
		if processed_link in links_copy: continue
		if processed_link == None: continue
		links_copy.append(processed_link)
		link_temp = {
			"link": link_a,
			"processed_link": processed_link
		}
		links.append(link_temp)

	for link in links:
		if link["link"] == '/': continue
		page_raw = page_raw.replace(link["link"], link["processed_link"])
	SaveFile(page_raw, page_save_path , True)

def CollectUrls(page_url):
	filename_black_names = [":", "?", "'", '"', "<", ">", "|"]
	black_suffix_str = ".tgz|.jar|.so|.docx|.py|.js|.css|.jpg|.jpeg|.png|.gif|.bmp|.pic|.tif|.txt|.doc|.hlp|.wps|.rtf|.pdf|.rar|.zip|.gz|.arj|.z|.wav|.aif|.au|.mp3|.ram|.wma|.mmf|.amr|.aac|.flac|.avi|.mpg|.mov|.swf|.int|.sys|.dll|.adt|.exe|.com|.c|.asm|.for|.lib|.lst|.msg|.obj|.pas|.wki|.bas|.map|.bak|.tmp|.dot|.bat|.cmd|.com"
	black_suffix = black_suffix_str.split("|")	
	links_a = ExtractLinks(page_url, "a", "href")
	result = []
	for link in links_a:
		link_info = ProcessResourcePath(page_url, link)
		processed_link = link_info["source_download_url"]
		if GetUrlPart(processed_link, "domain") != GetUrlPart(page_url, "domain"): continue
		if IfBlackName(filename_black_names, GetUrlPart(processed_link, "path"), 2): continue
		if IfBlackName(black_suffix, GetUrlPart(processed_link, "filesuffix")): continue
		processed_link = GetUrlPart(processed_link, "completedomain") + GetUrlPart(processed_link, "path")
		if processed_link not in result:
			result.append(processed_link)
	return result

async def coroutine_execution(function, param1):
	"""
	通过run_in_executor方法来新建一个线程来执行耗时函数。
	注意：functools.partial调用的参数应与目标函数一致
	"""
	loop = asyncio.get_event_loop()
	result = await loop.run_in_executor(None,functools.partial(function, page_url=param1)) 
	# result为目标函数返回的值
	return result

def coroutine_init(function, parameters, threads):
	"""
	处理线程
	coroutine_execution()调用协程函数，可自行修改参数个数内容等。 
	"""
	times = int(len(parameters) / threads) + 1
	if len(parameters) == threads or int(len(parameters) % threads) == 0: times -= 1
	result = []
	for num in range(times):
		tasks = []
		Minimum = threads * num
		Maximum = threads * (num + 1)
		if num == times - 1 and len(parameters) % threads != 0:
			Minimum = (times - 1) * threads
			Maximum = len(parameters)
		if len(parameters) <= threads:
			Minimum = 0
			Maximum = len(parameters)
		for i in range(Minimum, Maximum):
			# 此处的parameters[i]就是取目标参数的单个值，可自行调整
			future = asyncio.ensure_future(coroutine_execution(function, param1=parameters[i]))
			tasks.append(future)
		loop = asyncio.get_event_loop()
		loop.run_until_complete(asyncio.wait(tasks))
		for task in tasks:
			result.append(task.result())
		#print("[*] The {}th thread ends".format(str(num + 1)))
	return result

def ExtractUrls(main_url, depth = 200, threads = 30):
	print("[Info] - Collecting URLs for the entire website, it takes a little time...")
	print("Main url: {url} \nDepth: {depth}\nThreads:{threads}".format(url=main_url,depth=depth,threads=threads))
	domain = GetUrlPart(main_url, "domain")
	domain_path = domain.replace(".", "_")
	urls = CollectUrls(main_url)
	if main_url not in urls: urls.append(main_url)
	collected_urls = []
	urls_count = 0
	for i in range(0, depth):
		print("- " + str(i + 1) + "th loop traversal in progress")
		copy_urls = urls[:]
		if len(copy_urls) == len(collected_urls): break
		not_extracted_urls = []
		for url in copy_urls:
			if url not in collected_urls: 
				not_extracted_urls.append(url)
		results = coroutine_init(CollectUrls, parameters=not_extracted_urls, threads=threads)
		collected_urls.extend(not_extracted_urls)
		for result in results:
			for temp_url in result:
				if temp_url not in urls:
					urls.append(temp_url.strip())
		print("- Collected a total of {0} URL links in this cycle".format(len(urls) - urls_count))
		urls_count = len(urls)
	print("[Info] - Urls collection completed")
	print("[Info] - Collected a total of {0} URLs".format(str(urls_count)))
	print("\n[Info] - Getting source and resources for each page...")
	results = coroutine_init(SaveSinglePage, parameters=urls, threads=threads)

if __name__ == "__main__":

	print(Welcome)
	print(Information)
	print(Help)

	args = parse_args()
	if args.urls == None:
		if args.url == None:
			print("Please enter a url. \n Example: python -u 'http://www.threezh1.com/'")
			exit()
		if args.entire == True:
			depth = 200
			threads = 30
			if args.depth != None: depth = int(args.depth)
			if args.threads != None: threads = int(args.threads)
			ExtractUrls(args.url, depth, threads)
		elif args.entire == False:
			SaveSinglePage(args.url)
		print("\n[Info] - All resources have been downloaded")
	else:
		with open(args.urls, "r", encoding="utf-8") as fobject:
			urls = fobject.read().split("\n")
		for url in urls:
			if args.entire == True:
				depth = 200
				threads = 30
				if args.depth != None: depth = int(args.depth)
				if args.threads != None: threads = int(args.threads)
				ExtractUrls(url, depth, threads)
			elif args.entire == False:
				SaveSinglePage(url)