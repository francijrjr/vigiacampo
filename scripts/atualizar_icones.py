"""Atualiza apenas os SVGs usados pelo front a partir do Lucide oficial."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen
import json
import re

VERSAO = '0.468.0'
ICONES = ['layout-dashboard', 'clipboard-list', 'users', 'chart-no-axes-combined',
          'settings', 'house', 'send', 'file-pen-line', 'plus', 'arrow-right', 'arrow-left',
          'arrow-up-right', 'download', 'log-out', 'trash-2', 'pencil', 'copy', 'camera',
          'refresh-cw', 'x', 'clipboard-check', 'calendar-days', 'circle-check',
          'circle-dashed', 'map-pin', 'wifi', 'wifi-off', 'list-filter', 'key-round']
BASE = f'https://raw.githubusercontent.com/lucide-icons/lucide/{VERSAO}/'


def baixar(nome):
    with urlopen(BASE + f'icons/{nome}.svg', timeout=30) as resposta:
        svg = resposta.read().decode()
    return nome, re.search(r'<svg[^>]*>([\s\S]*?)</svg>', svg).group(1).strip()


if __name__ == '__main__':
    pasta = Path(__file__).resolve().parents[1] / 'frontend'
    with ThreadPoolExecutor(max_workers=6) as pool:
        icones = dict(pool.map(baixar, ICONES))
    with urlopen(BASE + 'LICENSE', timeout=30) as resposta:
        licenca = resposta.read().decode()
    (pasta / 'lucide-LICENSE.txt').write_text(licenca, encoding='utf-8')
    (pasta / 'icons.js').write_text(
        f'// Lucide {VERSAO} — https://lucide.dev — licença em lucide-LICENSE.txt\n'
        '// SVGs locais: funcionam sem CDN e sem etapa de compilação.\n'
        'const icones = ' + json.dumps(icones, ensure_ascii=False, indent=2) + ';\n\n'
        'export function icone(nome) {\n'
        '  if (!icones[nome]) throw new Error(`Ícone não encontrado: ${nome}`);\n'
        '  return `<svg class="lucide" data-icon="${nome}" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${icones[nome]}</svg>`;\n'
        '}\n', encoding='utf-8')
    print(f'{len(icones)} ícones Lucide {VERSAO} salvos localmente.')
