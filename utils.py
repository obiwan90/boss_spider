from datetime import datetime, timedelta
import re

def parse_date(date_str):
    """解析发布时间字符串"""
    if '分钟前' in date_str:
        minutes = int(re.search(r'\d+', date_str).group())
        return datetime.now() - timedelta(minutes=minutes)
    elif '小时前' in date_str:
        hours = int(re.search(r'\d+', date_str).group())
        return datetime.now() - timedelta(hours=hours)
    elif '天前' in date_str:
        days = int(re.search(r'\d+', date_str).group())
        return datetime.now() - timedelta(days=days)
    elif '昨天' in date_str:
        return datetime.now() - timedelta(days=1)
    else:
        return datetime.now()

def is_within_days(date_str, days):
    """判断给定的时间是否在指定天数内"""
    publish_date = parse_date(date_str)
    return (datetime.now() - publish_date).days < days 