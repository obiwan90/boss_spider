from playwright.sync_api import sync_playwright
import time
from config import Config
from datetime import datetime, timedelta

class BossSpider:
    def __init__(self):
        self.matched_jobs = []
        
        print("请输入搜索关键词（直接回车使用默认值：小程序开发）：")
        self.keyword = input().strip() or Config.DEFAULT_KEYWORD
        
        # 获取满足条件的关键词
        print("\n请输入满足条件的关键词，多个关键词用逗号分隔")
        print(f"直接回车使用默认值：{', '.join(Config.DEFAULT_ACCEPT_KEYWORDS)}")
        accept_input = input().strip()
        self.accept_keywords = [k.strip() for k in accept_input.split(',')] if accept_input else Config.DEFAULT_ACCEPT_KEYWORDS
        
        # 获取不满足条件的关键词
        print("\n请输入不满足条件的关键词，多个关键词用逗号分隔")
        print(f"直接回车使用默认值：{', '.join(Config.DEFAULT_REJECT_KEYWORDS)}")
        reject_input = input().strip()
        self.reject_keywords = [k.strip() for k in reject_input.split(',')] if reject_input else Config.DEFAULT_REJECT_KEYWORDS
        
        print("\n使用的满足条件关键词：", ', '.join(self.accept_keywords))
        print("使用的不满足条件关键词：", ', '.join(self.reject_keywords))
        
        print(f"\n请输入要采集的页数（直接回车采集 {Config.MAX_PAGES} 页）：")
        try:
            input_pages = input().strip()
            self.max_pages = int(input_pages) if input_pages else Config.MAX_PAGES
        except ValueError:
            print(f"输入有误，使用默认值：{Config.MAX_PAGES}页")
            self.max_pages = Config.MAX_PAGES

    def _is_within_days(self, update_time):
        """检查更新时间是否在指定天数内"""
        try:
            update_time = update_time.strip().lower()
            
            # 1. 直接符合条件的时间格式
            instant_patterns = [
                '刚刚活跃', '今天活跃', '今日活跃',
                '小时内活跃', '分钟前活跃'
            ]
            if any(x in update_time for x in instant_patterns):
                print(f"时间符合条件(即时): {update_time}")
                return True
            
            # 2. 处理"X日内活跃"
            if '日内活跃' in update_time:
                days = int(update_time.replace('日内活跃', ''))
                is_valid = days <= Config.DAYS_LIMIT
                print(f"时间{'' if is_valid else '不'}符合条件(X日内): {update_time}")
                return is_valid
            
            # 3. 处理"本周活跃"
            if '本周活跃' in update_time:
                print(f"时间符合条件(本周): {update_time}")
                return True
            
            # 4. 处理"X周内活跃"
            if '周内活跃' in update_time:
                weeks = int(update_time.replace('周内活跃', ''))
                is_valid = weeks * 7 <= Config.DAYS_LIMIT
                print(f"时间{'' if is_valid else '不'}符合条件(X周内): {update_time}")
                return is_valid
            
            # 5. 处理超期的时间格式
            expired_patterns = [
                '本月活跃', '月内活跃', '半年活跃', '年活跃',
                '月前活跃', '半年前活跃', '年前活跃'
            ]
            if any(x in update_time for x in expired_patterns):
                print(f"时间不符合条件(超期): {update_time}")
                return False
            
            # 6. 处理其他可能的时间格式
            if '活跃' in update_time:
                print(f"未识别的活跃时间格式: {update_time}")
                return False
            
            print(f"完全未识别的时间格式: {update_time}")
            return False
            
        except Exception as e:
            print(f"解析更新时间出错: {update_time}, {e}")
            return False

    def _check_job_conditions(self, detail_text, title, update_time):
        """检查职位是否满足条件"""
        # 1. 检查更新时间
        if not self._is_within_days(update_time):
            print(f"更新时间超过{Config.DAYS_LIMIT}天，跳过: {title}")
            return None
        
        # 2. 从job-detail-section获取工作信息
        try:
            detail_lower = detail_text.lower()
            
            # 检查是否包含不满足条件的关键词
            found_reject_keywords = []
            for keyword in self.reject_keywords:
                if keyword in detail_lower:
                    found_reject_keywords.append(keyword)
            
            if found_reject_keywords:
                print(f"发现不满足条件的关键词: {', '.join(found_reject_keywords)}")
                return None
            
            # 检查是否包含满足条件的关键词
            found_accept_keywords = []
            for keyword in self.accept_keywords:
                if keyword in detail_lower:
                    found_accept_keywords.append(keyword)
            
            if not found_accept_keywords:
                print(f"未找到任何满足条件的关键词")
                return None
            
            # 返回匹配到的关键词
            return found_accept_keywords
            
        except Exception as e:
            print(f"检查职位条件出错: {e}")
            return None

    def start(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # 访问搜索页面，添加工作类型参数
                encoded_keyword = self.keyword.replace(' ', '%20')
                search_url = f"{Config.BASE_URL}/web/geek/job?query={encoded_keyword}&city=100010000&jobType=1903"
                
                # 修改加载策略
                print("正在访问搜索页面...")
                try:
                    # 先尝试等待 domcontentloaded
                    page.goto(search_url, wait_until='domcontentloaded', timeout=20000)
                    # 然后等待职位列表出现
                    page.wait_for_selector('.job-list-box', timeout=20000)
                    print("页面加载成功")
                except Exception as e:
                    print(f"页面加载超时，尝试重新加载: {e}")
                    # 如果超时，重试一次
                    page.reload(wait_until='domcontentloaded', timeout=20000)
                    page.wait_for_selector('.job-list-box', timeout=20000)
                
                time.sleep(3)  # 等待页面稳定
                
                # 采集数据
                self._collect_jobs(page)
                
            except Exception as e:
                print(f"程序执行出错: {e}")
                # 保存错误截图
                try:
                    page.screenshot(path="error.png")
                    print("已保存错误截图: error.png")
                except:
                    pass
            finally:
                browser.close()

    def _collect_jobs(self, page):
        page_num = 1
        while True:
            try:
                print(f"正在采集第 {page_num} 页...")
                page.wait_for_selector('.job-list-box', timeout=10000)
                time.sleep(2)
                
                job_items = page.query_selector_all('.job-card-wrapper')
                print(f"找到 {len(job_items)} 个职位...")
                
                for job_item in job_items:
                    try:
                        # 获取基本信息
                        title_element = job_item.query_selector('.job-name') or job_item.query_selector('.job-title')
                        if not title_element:
                            print("未找到职位标题，跳过")
                            continue
                        title = title_element.inner_text().strip()
                        
                        link_element = (job_item.query_selector('a.job-card-left') or 
                                      job_item.query_selector('a[ka="job-item"]') or
                                      job_item.query_selector('a'))
                        if not link_element:
                            print(f"未找到职位链接，跳过: {title}")
                            continue
                        job_link = Config.BASE_URL + link_element.get_attribute('href')
                        
                        print(f"正在处理: {title}")
                        
                        # 使用新标签页打开详情页
                        new_page = page.context.new_page()
                        try:
                            new_page.goto(job_link, wait_until='domcontentloaded', timeout=20000)
                            new_page.wait_for_selector('.job-detail', timeout=20000)
                            time.sleep(1)
                            
                            # 获取更新时间
                            update_time = None
                            update_selectors = [
                                '.job-detail .time',
                                '.detail-content .time',
                                '.update-time',
                                'span[class*="time"]'
                            ]
                            
                            for selector in update_selectors:
                                element = new_page.query_selector(selector)
                                if element:
                                    update_time = element.inner_text().strip()
                                    if any(keyword in update_time for keyword in ['活跃', '发布', '更新']):
                                        print(f"找到更新时间: {update_time}")
                                        break
                            
                            if not update_time:
                                print(f"未找到更新时间，跳过: {title}")
                                continue
                            
                            # 获取职位详情信息
                            detail_section = new_page.query_selector('.job-detail-section')
                            if not detail_section:
                                print(f"未找到职位详情section，跳过: {title}")
                                continue
                            
                            detail_text = detail_section.inner_text()
                            
                            # 检查职位条件
                            matched_keywords = self._check_job_conditions(detail_text, title, update_time)
                            if matched_keywords:
                                print(f"职位符合条件: {title}")
                                # 记录匹配的职位信息
                                job_info = f"{title} | {', '.join(matched_keywords)} | {update_time} | {job_link}\n"
                                self.matched_jobs.append(job_info)
                                # 实时保存到文件
                                with open(Config.OUTPUT_FILE, 'a', encoding='utf-8') as f:
                                    f.write(job_info)
                        
                        except Exception as e:
                            print(f"处理详情页出错: {e}")
                        finally:
                            new_page.close()
                            time.sleep(1)
                    
                    except Exception as e:
                        print(f"处理位卡片出错: {e}")
                        continue
                
                if page_num >= self.max_pages:
                    print(f"已达到设定的最大页数: {self.max_pages}")
                    break
                
                # 翻页
                try:
                    current_url = page.url
                    if 'page=' not in current_url:
                        next_url = current_url + f'&page={page_num + 1}'
                    else:
                        next_url = current_url.replace(f'page={page_num}', f'page={page_num + 1}')
                    
                    # 确保 jobType 参数存在
                    if 'jobType=1903' not in next_url:
                        next_url += '&jobType=1903'
                    
                    print(f"正在跳转到第 {page_num + 1} 页...")
                    page.goto(next_url, wait_until='domcontentloaded', timeout=20000)
                    time.sleep(2)
                    
                    if page.url != current_url:
                        page_num += 1
                    else:
                        print("已经是最后一页")
                        break
                    
                except Exception as e:
                    print(f"翻页出错: {e}")
                    break
                
            except Exception as e:
                print(f"采集过程出错: {e}")
                break

        print(f"\n采集完成，共找到 {len(self.matched_jobs)} 个符合条件的职位")
        print(f"结果已保存到: {Config.OUTPUT_FILE}")