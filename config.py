class Config:
    # 网站URL
    BASE_URL = "https://www.zhipin.com"
    
    # 默认配置
    DEFAULT_KEYWORD = "小程序开发"
    DEFAULT_CITY = "全国"
    DEFAULT_START_PAGE = 1  # 默认起始页
    MAX_PAGES = 5  # 默认采集5页
    
    # 默认关键词
    DEFAULT_ACCEPT_KEYWORDS = ['远程办公', '远程工作', '居家办公', '在家办公', '可远程', 
                             '支持远程', '可在家', '可居家', '兼职', 'remote', '弹性办公']
    DEFAULT_REJECT_KEYWORDS = ['不接受远程', '不支持远程', '不接受在家', '不支持居家',
                             '不接受居家', '不支持在家', '必须坐班', '不接受兼职',
                             '不支持远程办公', '不接受远程办公', '必须到岗', '必须到办公室']
    
    # 数据保存路径
    OUTPUT_FILE = "matched_jobs.txt"
    
    # 时间限制（一周内）
    DAYS_LIMIT = 7
    
    # 请求头
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    } 