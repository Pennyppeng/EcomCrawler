import time
import logging
from typing import List
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright
from parsers import parse_product_from_element
from utils import smooth_scroll
from storage import save_batch

logger = logging.getLogger(__name__)


def is_blocked_by_antibot(page) -> bool:
    markers = ("/punish?", "x5secdata", "captcha")
    for fr in page.frames:
        u = (fr.url or "").lower()
        if any(m in u for m in markers):
            return True
    body_text = (page.inner_text("body") or "").lower()
    return "验证码" in body_text or "captcha" in body_text


def dump_debug_artifacts(page, prefix: str = "debug"):
    ts = int(time.time())
    png = f"{prefix}_{ts}.png"
    html = f"{prefix}_{ts}.html"
    page.screenshot(path=png, full_page=True)
    with open(html, "w", encoding="utf-8") as f:
        f.write(page.content())
    logger.info("已导出调试文件: %s, %s", png, html)


def init_browser(profile_dir: str = "profile", headless: bool = False):
    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(user_data_dir=profile_dir, headless=headless)
    page = browser.new_page()
    return p, browser, page


def run_crawl(keyword: str, start_page: int = 1, end_page: int = 1, headless: bool = False):
    p = None
    try:
        p, browser, page = init_browser(headless=headless)
        # 直接进入搜索页，避免首页搜索框触发失败导致一直停留在首页。
        search_url = f"https://s.taobao.com/search?q={quote_plus(keyword)}"
        page.goto(search_url, timeout=60000)
        page.wait_for_timeout(3000)
        logger.info("已进入页面: %s", page.url)
        if is_blocked_by_antibot(page):
            logger.warning("检测到风控/验证码页面")
            if not headless:
                logger.info("请在浏览器中完成人机验证，程序将等待最多 120 秒")
                deadline = time.time() + 120
                while time.time() < deadline:
                    page.wait_for_timeout(2000)
                    if not is_blocked_by_antibot(page):
                        logger.info("已通过验证，继续抓取")
                        break
            if is_blocked_by_antibot(page):
                logger.warning("当前会话仍无法通过风控，停止抓取")
                dump_debug_artifacts(page, prefix="antibot")
                return

        results = []
        for pg in range(start_page, end_page + 1):
            logger.info(f"处理第 {pg} 页")
            # 等待结果加载
            page.wait_for_timeout(3000)
            smooth_scroll(page)

            if is_blocked_by_antibot(page):
                logger.warning("第 %s 页仍处于风控/验证码状态，停止翻页", pg)
                dump_debug_artifacts(page, prefix=f"antibot_page_{pg}")
                break

            # 优先使用链接选择器（更稳定），其次回退到旧选择器。
            product_elements = page.query_selector_all('a[href*="item.taobao.com/item.htm"]')
            if not product_elements:
                product_elements = page.query_selector_all(".item")
            if not product_elements:
                product_elements = page.query_selector_all(".J_MouserOnverReq")

            logger.info("当前页匹配到商品节点数: %s", len(product_elements))

            for el in product_elements:
                try:
                    # 链接节点缺少结构化字段时，给出兜底提取，保证至少有标题和链接。
                    href = el.get_attribute('href') or ''
                    if href and 'item.taobao.com' in href:
                        title_text = (el.inner_text() or '').strip()
                        if not title_text:
                            title_text = (el.get_attribute('title') or '').strip()
                        item = {
                            'title': title_text,
                            'price': 0.0,
                            'sales': 0,
                            'shop': '',
                            'product_link': href,
                        }
                    else:
                        item = parse_product_from_element(el)

                    if not item.get('title') and not item.get('product_link'):
                        continue
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
