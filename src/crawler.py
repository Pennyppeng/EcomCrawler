import time
import logging
from typing import List
from playwright.sync_api import sync_playwright
from parsers import parse_product_from_element
from utils import smooth_scroll
from storage import save_batch

logger = logging.getLogger(__name__)


def init_browser(profile_dir: str = "profile", headless: bool = False):
    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(user_data_dir=profile_dir, headless=headless)
    page = browser.pages[0] if browser.pages else browser.new_page()
    return p, browser, page


def run_crawl(keyword: str, start_page: int = 1, end_page: int = 1, headless: bool = False):
    p = None
    try:
        p, browser, page = init_browser(headless=headless)
        page.goto("https://www.taobao.com", timeout=30000)

        # 输入关键词并搜索 - 选择器可能需根据页面调整
        search_box = page.query_selector('input[name="q"]') or page.query_selector('input#q')
        if not search_box:
            logger.warning("未找到搜索输入框，请检查 selector")
        else:
            search_box.fill(keyword)
            search_box.press('Enter')

        results = []
        for pg in range(start_page, end_page + 1):
            logger.info(f"处理第 {pg} 页")
            # 等待结果加载
            page.wait_for_timeout(3000)
            smooth_scroll(page)

            # 商品容器选择器需要以实际页面为准
            product_elements = page.query_selector_all(".item")
            if not product_elements:
                # 备用选择器
                product_elements = page.query_selector_all(".J_MouserOnverReq")

            for el in product_elements:
                try:
                    item = parse_product_from_element(el)
                    results.append(item)
                except Exception as e:
                    logger.exception("解析商品失败: %s", e)

            # 批量保存以免内存过高
            if results:
                save_batch(results, f"output_page_{pg}.xlsx")
                results = []

            # 翻页：尝试点击下一页
            # 注意：建议使用 Chrome DevTools 的 Copy XPath 来获得稳定的 xpath
            try:
                next_btn = page.query_selector('a.next') or page.query_selector('a[aria-label="下一页"]')
                if next_btn:
                    next_btn.click()
                    page.wait_for_timeout(3000)
                else:
                    logger.info("未找到下一页按钮，结束翻页")
                    break
            except Exception:
                logger.exception("点击下一页失败，结束")
                break

    finally:
        try:
            if p:
                p.stop()
        except Exception:
            pass
