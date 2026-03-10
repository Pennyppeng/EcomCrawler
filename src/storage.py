import pandas as pd
from typing import List, Dict


def save_batch(items: List[Dict], file_path: str = 'output.xlsx'):
    if not items:
        return
    df = pd.DataFrame(items)
    # 如果文件已经存在，可以选择追加逻辑；此处覆盖写入
    df.to_excel(file_path, index=False)
