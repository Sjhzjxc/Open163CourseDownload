# -*- coding: utf-8 -*-
# @Time    : 18/10/14 18:49
# @Author  : Sjhzjxc
# @Email   : sjhzjxc@gmail.com
# @File    : main.py
# @Software: PyCharm
import getopt
import json
import os
import sys
from contextlib import closing

import lxml
import requests
from bs4 import BeautifulSoup

dir = "Vedio/"
get_down_url = "http://c.open.163.com/mob/%s/getMoviesForIpad.do"


class ProgressBar(object):
    """
    下载进度
    """

    def __init__(self, title, count=0.0, run_status=None, fin_status=None, total=100.0, unit='', sep='/',
                 chunk_size=1.0):
        super(ProgressBar, self).__init__()
        self.info = "[%s] %s %.2f %s %s %.2f %s"
        self.title = title
        self.total = total
        self.count = count
        self.chunk_size = chunk_size
        self.status = run_status or ""
        self.fin_status = fin_status or " " * len(self.statue)
        self.unit = unit
        self.seq = sep

    def __get_info(self):
        # 【名称】状态 进度 单位 分割线 总数 单位
        _info = self.info % (
            self.title, self.status, self.count / self.chunk_size, self.unit, self.seq, self.total / self.chunk_size,
            self.unit)
        return _info

    def refresh(self, count=1, status=None):
        self.count += count
        # if status is not None:
        self.status = status or self.status
        end_str = "\r"
        if self.count >= self.total:
            end_str = '\n'
            self.status = status or self.fin_status
        print(self.__get_info(), end=end_str)


def cleanIllegalChar(s):
    return s.replace('/', '').replace(r':', '').replace(r'*', '').replace(r'?', '') \
        .replace(r'"', '').replace(r'>', '').replace(r'<', '').replace(r'|', '')


def download_video(index, dir, title, url):
    with closing(requests.get(url, stream=True)) as response:
        chunk_size = 1024
        content_size = int(response.headers['content-length'])
        title_clean = cleanIllegalChar(title)
        video_file = "%s/%d_%s.mp4" % (dir, index, title_clean)
        if os.path.exists(video_file) and os.path.getsize(video_file) == content_size:
            print('跳过' + title)
        else:
            progress = ProgressBar(title, total=content_size, unit="KB", chunk_size=chunk_size,
                                   run_status="正在下载", fin_status="下载完成")
            with open(video_file, "wb") as file:
                for data in response.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    progress.refresh(count=len(data))


def usage():
    print("main.py -u <course url> -p <download location>")


def main(argv):
    global dir
    course_url = ""
    try:
        opts, args = getopt.getopt(argv, "hu:p:", ["help", "url=", "path="])
    except getopt.GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif o in ("-u", "--url"):
            course_url = a
        elif o in ("-p", "--path"):
            dir = a
        else:
            assert False, "unhandled option"

    if course_url == "":
        print("please enter course url!")
        sys.exit(2)
    try:
        if not os.path.exists(dir):
            os.mkdir(dir)
        resp = requests.get(course_url)
        if resp.status_code != 200:
            print("error, get %s %d" % (course_url, resp.status_code))
        else:
            soup = BeautifulSoup(resp.text.encode('utf8'), 'html.parser')
            dir = dir + soup.title.string
            if not os.path.exists(dir):
                os.mkdir(dir)
            plid = soup.find(class_='downbtn j-movie-download').attrs['data-plid']
            url = get_down_url % plid
            resp = requests.get(url)
            if resp.status_code != 200:
                print("error, get %s %d" % (url, resp.status_code))
            # print(resp.text)
            body = json.loads(resp.text)
            if "data" in body:
                data = body["data"]
                if "videoList" in data:
                    videoList = data["videoList"]
                    for index, video in enumerate(videoList):
                        title = ""
                        if "title" in video:
                            title = video["title"]
                            print(title)
                        if "mp4ShareUrl" in video:
                            video_url = video["mp4ShareUrl"]
                            print(video_url)
                            if video_url == "":
                                print(video)
                            else:
                                download_video(index + 1, dir, title, video_url)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main(sys.argv[1:])
