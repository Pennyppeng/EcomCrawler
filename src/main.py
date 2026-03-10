import argparse
import logging
from crawler import run_crawl


def parse_args():
    p = argparse.ArgumentParser(description="EcomCrawler - 淘宝商品抓取器")
    p.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    p.add_argument("--start", type=int, default=1, help="起始页，默认 1")
    p.add_argument("--end", type=int, default=1, help="结束页，默认 1")
    p.add_argument("--headless", action="store_true", help="是否无头模式")
    return p.parse_args()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = parse_args()
    run_crawl(keyword=args.keyword, start_page=args.start, end_page=args.end, headless=args.headless)


if __name__ == '__main__':
    main()
