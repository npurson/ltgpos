from __future__ import unicode_literals

# -*- coding: utf-8 -*-
import os 
from itertools import chain
from pypinyin import lazy_pinyin
from tqdm import tqdm
import pandas as pd
import pymysql
import json
import sys
import pandas as pd
import django
import socket
from django.conf import settings
# settings.configure(DEBUG=True)
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.abspath(os.path.join(BASE_DIR, os.pardir)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebMysql.settings'
django.setup()
circulation_times = 200
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DataMangement.settings")
from DataManagement.models import *
'''
    DECIMAL = 0
    TINY = 1
    SHORT = 2
    LONG = 3
    FLOAT = 4
    DOUBLE = 5
    NULL = 6
    TIMESTAMP = 7
    LONGLONG = 8
    INT24 = 9
    DATE = 10
    TIME = 11
    DATETIME = 12
    YEAR = 13
    NEWDATE = 14
    VARCHAR = 15
    BIT = 16
    JSON = 245
    NEWDECIMAL = 246
    ENUM = 247
    SET = 248
    TINY_BLOB = 249
    MEDIUM_BLOB = 250
    LONG_BLOB = 251
    BLOB = 252
    VAR_STRING = 253
    STRING = 254
    GEOMETRY = 255
    CHAR = TINY
    INTERVAL = ENUM
    
    
    
cursor.description#返回游标活动状态 #(('VERSION()', 253, None, 24, 24, 31, False),)
包含7个元素的元组：
(name, type_code, display_size, internal_size, precision, scale, null_ok)
'''

def get_stations(file=r'./data/stationinfo.xlsx'):
    xlsx = pd.read_excel(file)
    columns = list(xlsx.columns)
    station_name_id = columns.index('stationname')
    weidu_id = columns.index('weidu')
    jingdu_id = columns.index('jingdu')
    station_dict = {}
    for idx, item in xlsx.iterrows():
        station_dict[item[station_name_id]] = (item[weidu_id], item[jingdu_id])
    return station_dict

def split_csv(fileName=None):
    data = pd.read_csv(fileName, error_bad_lines=False, names=['value'], index_col=False, header=None)
    # TODO:设计算法抽取数据
    return dataFrame


def query():
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        passwd='xuyifei',
        db='thunder'
    )
    
    cursor = conn.cursor()
    cursor.execute('show tables')
    tables = cursor.fetchall()
    # 先试着操作waveinfo_rs表
    cursor.execute("SELECT * FROM waveinfo_rs")
    cols = cursor.description
    # 根据表得到几个字段的index
    station = 3
    peaktime = 6
    slicefile = 12
    # 接下来获取waveinfo_rs表的全部数据
    data = cursor.fetchall()
    dataLength = len(data)
    data_batch = []
    # 开始连接
    s = socket.socket()
    # host = '192.168.1.123'
    host = '127.0.0.1'
    port = 8888
    s.connect((host, port))
    
    
    for i in tqdm(range(circulation_times)):
        # 初始化data_batch 为空，因此可以直接进入第一个if语句
        cur_names = lazy_pinyin(data[i][station])
        cur_name = chain(*cur_names)
        cur_name = ''.join(cur_name)
        fileName = data[i][slicefile]
        
        wave_data = split_csv()
        if not data_batch:
            data_batch.append({'stationname':cur_name, 'peaktime':data[i][peaktime]})
            continue
        # 如果第i个数据和第i-1个数据的相关性足够高，那就一起加入data_batch，日后一起发送
        elif cluster_data(data[i-1], data[i]):
            last_names = lazy_pinyin(data[i-1][station])
            last_name = chain(*last_names)
            last_name = ''.join(last_name)
            data_batch.append({'stationname':last_name, 'peaktime':data[i][peaktime]})
            continue
        # 如果第i个数据和第i-1个数据的相关性不够高，那就将当前data_batch所有的值拿出来进行发送操作，并且将第i
        # 个数据放在新的data_batch里面
        else:
            data_send = json.dumps(data_batch)
            data_send = str(len(data_send)).zfill(10) + data_send
            try:
                s.sendall(data_send.encode())
                info = s.recv(1024)
                # pass
                print(info)
            except:
                print("Send failed!!!!!")
                print("The data not sent is")
                print(data_batch)
            data_batch = [{'stationname':cur_name, 'peaktime':data[i][peaktime]}]
    s.close()
            
    print()

def cluster_data(data_1, data_2):
    return False

query()