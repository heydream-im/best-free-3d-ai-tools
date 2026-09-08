"""Build concise localized catalogs from shared traffic and screenshot records.

README_zh.md is the complete Chinese editorial source. README.md mirrors English.
Update data/locales.json
when product descriptions change, then run python3 scripts/build-readmes.py.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
locales = json.loads((ROOT / 'data/locales.json').read_text())
products = json.loads((ROOT / 'data/traffic.json').read_text())['products']
screenshots = {p['id']: p for p in json.loads((ROOT / 'data/screenshots.json').read_text())}
languages = [('en', 'English'), ('zh', '简体中文'), ('tw', '繁體中文'),
             ('ja', '日本語'), ('ko', '한국어'), ('de', 'Deutsch'),
             ('fr', 'Français'), ('es', 'Español'), ('pt', 'Português'),
             ('it', 'Italiano'), ('ru', 'Русский'), ('ar', 'العربية'),
             ('id', 'Bahasa Indonesia'), ('th', 'ไทย'), ('vi', 'Tiếng Việt')]
nav = ' · '.join(f'[{name}](README_{code}.md)' for code, name in languages)
start, end = '<!-- LANGUAGES:START -->', '<!-- LANGUAGES:END -->'
main = ROOT / 'README_zh.md'
source = main.read_text()
header = (f'{start}\n\n> 本项目来自 [Hey Dream AI](https://heydream.im/) 团队。\n\n'
          f'{nav}\n\n'
          '中文为完整指南，其他语言为包含全部 17 款产品的精简版，涵盖截图、用途、流量口径与使用边界。\n\n'
          f'{end}')
if start in source:
    before, rest = source.split(start, 1)
    _, after = rest.split(end, 1)
    source = before + header + after
else:
    title, rest = source.split('\n', 1)
    source = title + '\n\n' + header + '\n' + rest
main.write_text(source)

for code, loc in locales.items():
    assert len(loc['descs']) == len(products), f'Description count: {code}'
    traffic, tools, workflow, free, sources, display, rank, product, visits, official, full = loc['labels']
    parts = [f"# {loc['title']}", f"> {loc['team']}", nav, loc['intro'],
             f'[{full}](README_zh.md)', f'## {traffic}', loc['note'],
             f'| {display} | {rank} | {product} | {visits} |\n| --- | --- | --- | ---: |']
    for p in products:
        name = 'Tencent Hunyuan3D' if p['id'] == 'hunyuan3d' else p['name']
        url = p.get('product_url') or screenshots[p['id']]['requested_url']
        value = p['reported_value']
        if p.get('source_url'):
            value = f"[{value}]({p['source_url']})"
        parts[-1] += f"\n| {p.get('display_position') or '—'} | {p['rank'] or '—'} | [{name}]({url}) | {value} |"
    parts += [f'## {tools}']
    for i, (p, description) in enumerate(zip(products, loc['descs']), 1):
        name = 'Tencent Hunyuan3D' if p['id'] == 'hunyuan3d' else p['name']
        url = p.get('product_url') or screenshots[p['id']]['requested_url']
        shot = screenshots[p['id']]['file']
        parts += [f'### {i}. {name}', f'[![{name}]({shot})]({url})', description,
                  f'[{official}]({url})']
    parts += [f'## {workflow}', loc['flow'], f'## {free}', loc['limits'],
              f'## {sources}',
              '[data/traffic.json](data/traffic.json) · [data/screenshots.json](data/screenshots.json)',
              f'[{full}](README_zh.md#sources)',
              '[data/locales.json](data/locales.json) · [scripts/build-readmes.py](scripts/build-readmes.py)']
    content = '\n\n'.join(parts) + '\n'
    (ROOT / f'README_{code}.md').write_text(content)
    if code == 'en':
        (ROOT / 'README.md').write_text(content)
print(f'Built {len(languages)} language editions with {len(products)} products each.')
