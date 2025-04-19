#!/usr/bin/env python3
"""
update_sku_ids.py  — замена <input name="product_id"> на <input name="sku_id">
по колонкам «Код артикула» ↔ «ID артикула» из CSV.
"""

import re
import argparse
import pandas as pd
from bs4 import BeautifulSoup


def build_mapping(csv_path: str) -> dict[str, str]:
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')

    # приводим ID артикула к целому без .0 и сразу к строке
    df['ID артикула'] = (
        pd.to_numeric(df['ID артикула'], errors='coerce')  # float → number
          .astype('Int64')                                 # сохраняем NaN, если есть
          .astype(str)                                     # Int64 → '10915'
    )

    return {
        str(code).strip(): sku_id.strip()
        for code, sku_id in zip(df['Код артикула'], df['ID артикула'])
        if pd.notna(code) and sku_id != '<NA>'
    }

def extract_tone(text: str | None) -> str | None:
    """Находит тон (например 1.0, 1.10, 10.02) в строке."""
    if not text:
        return None
    m = re.search(r'(\d+\.\d+)', text)
    return m.group(1) if m else None


def update_html(html_in: str, csv_path: str, html_out: str):
    mapping = build_mapping(csv_path)

    with open(html_in, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    for item in soup.select('div.item'):
        img = item.find('img')
        tone = extract_tone(img.get('alt')) or extract_tone(img.get('src'))
        if not tone or tone not in mapping:
            continue

        sku_id = mapping[tone]

        # ищем существующий input (product_id) и правим его
        inp = item.find('input', {'name': 'product_id'})
        if inp:
            inp['name'] = 'sku_id'
            inp['value'] = sku_id
        else:  # если вдруг поля нет — создадим
            form = item.find('form', class_='addtocart') or item
            form.insert(0, soup.new_tag('input', type='hidden',
                                         name='sku_id', value=sku_id))

    with open(html_out, 'w', encoding='utf-8') as f:
        f.write(str(soup))


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Меняет скрытые поля на sku_id + ID артикула.')
    p.add_argument('html_in',  help='Исходный HTML‑файл')
    p.add_argument('csv_path', help='CSV с колонками «Код артикула» и «ID артикула»')
    p.add_argument('-o', '--output', default='updated.html',
                   help='Куда записать результат (default: updated.html)')
    args = p.parse_args()
    update_html(args.html_in, args.csv_path, args.output)
    print(f'✓ Обновлённый HTML сохранён в «{args.output}».')
