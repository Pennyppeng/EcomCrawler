from pyquery import PyQuery as pq
from typing import Dict


def clean_text(s: str) -> str:
    if not s:
        return ""
    return "".join(s.split())


def parse_price(s: str) -> float:
    s = clean_text(s)
    if not s:
        return 0.0
    s = s.replace('¥', '').replace('￥', '').replace(',', '')
    try:
        return float(s)
    except Exception:
        # 尝试提取数字
        import re
        m = re.search(r"[0-9]+\.?[0-9]*", s)
        return float(m.group(0)) if m else 0.0


def parse_sales(s: str) -> int:
    s = clean_text(s)
    if not s:
        return 0
    if '万' in s:
        try:
            return int(float(s.replace('万', '')) * 10000)
        except Exception:
            return 0
    import re
    m = re.search(r"[0-9]+", s)
    return int(m.group(0)) if m else 0


def parse_product_from_element(el) -> Dict:
    # el is a Playwright element handle; get outer HTML and parse with PyQuery
    html = el.inner_html()
    d = pq(html)

    title = d('.title--ASSt27UY span').text() or d('.title a').text() or d('a').text()
    price = d('.price').text() or d('.pro-price').text()
    sales = d('.sales').text() or d('.deal-cnt').text()
    shop = d('.shop').text() or d('.shop-info').text()
    product_link = el.get_attribute('href') or d('a').attr('href')

    return {
        'title': clean_text(title),
        'price': parse_price(price),
        'sales': parse_sales(sales),
        'shop': clean_text(shop),
        'product_link': product_link,
    }
