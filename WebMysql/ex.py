# -*- coding: utf-8 -*-
import os 
from pypinyin import lazy_pinyin
import pymysql
import json
import pandas as pd
from itertools import chain
import socket
import copy
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
    # TODO：将经纬度加入发送的数据中
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
    # TODO:设计算法抽取数据，转成list
    return dataFrame

def SendData(s, data_send, data_batch):
    try:
        s.sendall(data_send.encode())
        info = s.recv(1024)
        # pass
        print(info)
    except:
        print("Send failed!!!!!")
        print("The data not sent is")
        print(data_batch)
    return 


def query():
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        passwd='xuyifei',
        db='thunder'
    )
    cursor = conn.cursor()
    # cursor.execute('show tables')
    # tables = cursor.fetchall()
    # TODO：根据tables名字以及需求操作不同表
    # 操作waveinfo_rs表
    cursor.execute("SELECT * FROM waveinfo_rs")
    cols = cursor.description
    # 根据表得到几个字段的index
    # TODO: 根据数据库直接获得index，而不是手动指定
    station = 3
    peaktime = 6
    slicefile = 12

    data_batch = []
    # 开始连接
    s = socket.socket()
    host = '127.0.0.1'
    port = 8888
    s.connect((host, port))
    
    lastdata = None
    while(True):
        data = cursor.fetchone()
        # 到达文件尾，把手头数据发送
        if data is None:
            SendData(s, data_send, data_batch)
            break
        cur_names = lazy_pinyin(data[station])
        cur_name = chain(*cur_names)
        cur_name = ''.join(cur_name)
        fileName = data[slicefile]
        # wave_data = split_csv()
        if not data_batch:
            data_batch.append({'stationname':cur_name, 'peaktime':data[peaktime]})
        # 如果第i个数据和第i-1个数据的相关性足够高，那就一起加入data_batch，日后一起发送
        elif cluster_data(lastdata, data):
            last_names = lazy_pinyin(data[station])
            last_name = chain(*last_names)
            last_name = ''.join(last_name)
            data_batch.append({'stationname':last_name, 'peaktime':data[peaktime]})
        # 如果第i个数据和第i-1个数据的相关性不够高，那就将当前data_batch所有的值拿出来进行发送操作，并且将第i
        # 个数据放在新的data_batch里面
        else:
            data_send = json.dumps(data_batch)
            data_send = str(len(data_send)).zfill(10) + data_send
            SendData(s, data_send, data_batch)
            data_batch = [{'stationname':cur_name, 'peaktime':data[peaktime]}]
        last_data = copy.deepcopy(data)
    
    s.close()
    conn.close()

def cluster_data(data_1, data_2):
    return False

query()