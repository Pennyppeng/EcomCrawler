import time


def smooth_scroll(page, step: int = 1000, pause: float = 0.5, max_scrolls: int = 20):
    """逐步向下滚动页面，等待懒加载内容加载。"""
    for _ in range(max_scrolls):
        page.evaluate(f"window.scrollBy(0, {step})")
        page.wait_for_timeout(int(pause * 1000))


def ensure_url(base: str, href: str) -> str:
    if not href:
        return ''
    if href.startswith('http'):
        return href
    if href.startswith('//'):
        return 'https:' + href
    return base.rstrip('/') + '/' + href.lstrip('/')
