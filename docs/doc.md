# Documentation

## Args & Returns

### Args

由数个 JSONObject 构成的 JSONArray，每个 JSONObject 为一个探测站点的数据。

| Keys            | Type   | Description               |
| --------------- | ------ | ------------------------- |
| latitude        | double | 探测站点纬度                |
| longitude       | double | 探测站点经度                |
| node            | string | 主机-站点号字符串，如"81-12" |
| datetime        | string | 探测到雷击的日期时间字符串，如"2020-9-21 11:31:18" |
| microsecond     | uint32 | 单位 0.1 us                |
| signal_strength | double | 探测雷击的信号强度           |

### Returns

JSONObject

| Keys                | Type         | Description        |
| ------------------- | ------------ | ------------------ |
| datetime            | string       | 雷击发生的日期时间字符串，如"2020-9-21 11:31:18" |
| time                | uint32       | 单位 0.1 us         |
| latitude            | double       | 雷击发生纬度的计算结果 |
| longitude           | double       | 雷击发生经度的计算结果 |
| altitude            | double       | 雷击发生海拔的计算结果 |
| goodness            | double       | 计算结果的优度        |
| current             | double       | 雷击电流的计算结果     |
| raw                 | JSONArray    | 原始输入数据          |
| allDist             | double-array | 所有探测站点与雷击的距离，单位 km      |
| allDtime            | double-array | 所有探测时间与雷击的时差，单位 ms      |
| isInvolved          | uint32-array | 所有站点是否参与定位计算，是为1，否则为0 |
| involvedNodes       | string-array | 参与定位计算站点的主机-站点号字符串     |
| referNode           | string       | 参考站的主机-站点号字符串，如"81-12"   |
| involvedSigStrength | double-array | 参与计算站点的信号强度 |
| involvedCurrent     | double-array | 参与计算站点的电流强度 |

## Getting Started

### ltgpos.cpp

`ltgpos()`
- 声明：`char* ltgpos(char* str)`
- 描述：模块调用入口
- 参数：输入的数据JSON字符串
- 返回：输出的结果JSON字符串

### json_parser.cpp

`parseJsonStr()`
- 声明：`cJSON* parseJsonStr(const char* jstr, schdata_t* schdata)`
- 描述：解析输入的数据JSON字符串，选取定位计算所需的数据
- 参数：输入的数据JSON字符串，供解析填充的计算数据
- 返回：输入的数据JSON字符串中的源数据字段

`formatRetJsonStr()`
- 声明：`char* formatRetJsonStr(schdata_t* schdata, cJSON* jarr)`
- 描述：根据定位计算结果，构建输出的结果JSON字符串
- 参数：定位计算结果，输入的数据JSON字符串中的源数据字段
- 返回：输出的结果JSON字符串

### grid_search.cu

`grid_search()`
- 声明：`void grid_search(ssrinfo_t* ssrinfo, grdinfo_t* grdinfo, schdata_t* schdata)`
- 描述：通过网格搜索计算定位结果
- 参数：全局计算信息，定位计算数据
- 返回：定位计算结果

`calGirdGoodness2d_G()`
- 声明：`__global__ void calGirdGoodness2d_G(ssrinfo_t sinfo, grdinfo_t ginfo)`
- 描述：网格搜索的单格点计算优度
- 参数：格点计算信息
- 返回：格点计算结果

### comb_mapper.cpp

`comb_mapper()`
- 声明：`std::vector<long> comb_mapper(long involved)`
- 描述：对选取站点进行排列组合，生成多组不同的站点选取组合
- 参数：站点选取掩码
- 返回：多组站点选取掩码

### geodistance.cu

`getGeoDistance2d()`
- 声明：`double getGeoDistance2d(double lat1, double lon1, double lat2, double lon2)`
- 描述：计算两点距离（半正弦公式）
- 参数：站点经纬度
- 返回：距离（km）

### config.h

`kMaxGrdSize = 1024`：GTX 1080Ti 所支持的最大线程数
`kGoodThres = 20`：优度选取阈值
