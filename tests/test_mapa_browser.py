"""Fluxo do mapa em banco descartável e GPS simulado, sem consumir tiles públicos."""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def servidor_mapa(tmp_path_factory):
    pasta = tmp_path_factory.mktemp('mapa')
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        porta = s.getsockname()[1]
    url = f'http://127.0.0.1:{porta}'
    env = {**os.environ, 'DATABASE_URL': f'sqlite:///{pasta / "mapa.db"}',
           'SEED_DEMO': 'true', 'AUTO_CREATE_TABLES': 'true', 'UPLOAD_DIR': str(pasta / 'uploads')}
    processo = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--port', str(porta)],
                                cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                if httpx.get(url, timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(.1)
        else:
            pytest.fail('Servidor de teste não iniciou')
        yield url
    finally:
        processo.terminate()
        processo.wait(timeout=10)


@pytest.mark.parametrize('mobile', [False, True])
def test_desenhar_salvar_reabrir_e_limpar(servidor_mapa, mobile):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        contexto = browser.new_context(viewport={'width': 390 if mobile else 1440, 'height': 844 if mobile else 1100},
                                       is_mobile=mobile, has_touch=mobile, permissions=['geolocation'],
                                       geolocation={'latitude': -3.73, 'longitude': -38.53, 'accuracy': 8})
        contexto.route('https://tile.openstreetmap.org/**', lambda rota: rota.fulfill(
            content_type='image/svg+xml', body='<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#edf1ee"/><path d="M0 128H256M128 0V256" stroke="white" stroke-width="15"/></svg>'))
        sessao = contexto.request.post(servidor_mapa+'/api/v1/auth/login', data={'username': 'agente', 'password': 'agente123'}).json()
        registro = contexto.request.post(servidor_mapa+'/api/v1/registros/',
            headers={'Authorization': 'Bearer '+sessao['access_token']},
            data={'municipio': 'Fortaleza', 'codigo_area': '01', 'ciclo': '01', 'data': '2026-10-04', 'atividade': 'LI'}).json()
        page = contexto.new_page()
        erros = []
        page.on('pageerror', lambda e: erros.append(str(e)))
        page.goto(servidor_mapa)
        page.evaluate('(s) => sessionStorage.setItem("alberio.sessao", JSON.stringify(s))', sessao)
        page.goto(servidor_mapa+f"/#registro/{registro['id']}")
        page.reload()
        page.locator('[data-action="novo-quarteirao"]').click()
        page.get_by_label('Número do quarteirão').fill('01')
        page.locator('.mapa-estado').filter(has_text='precisão aproximada de 8 m').wait_for()
        canvas = page.locator('.mapa-canvas')
        for x, y in [(80, 80), (210, 80), (210, 210), (80, 210)]:
            canvas.click(position={'x': x, 'y': y})
        page.get_by_role('button', name='Salvar', exact=True).click()
        page.locator('.form-error').filter(has_text='Conclua o contorno').wait_for()
        page.get_by_role('button', name='Desfazer ponto').click()
        canvas.click(position={'x': 80, 'y': 210})
        page.get_by_role('button', name='Concluir contorno').click()
        page.locator('.mapa-rotulo').filter(has_text='QT 01').wait_for()
        destino = RAIZ/'tmp'/'screenshots'
        destino.mkdir(parents=True, exist_ok=True)
        page.locator('#dialog').screenshot(path=str(destino/f'mapa-{ "mobile" if mobile else "desktop"}.png'))
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.get_by_role('button', name='Salvar', exact=True).click()
        page.locator('#dialog').wait_for(state='hidden')
        page.get_by_text('Quarteirão 01', exact=True).wait_for()
        page.locator('[data-action^="editar-quarteirao:"]').click()
        page.locator('.mapa-desenho').filter(has_text='Contorno concluído · 4 cantos').wait_for()
        assert page.locator('.mapa-vertice').count() == 4
        if not mobile:
            endpoint = servidor_mapa+f"/api/v1/registros/{registro['id']}/quarteiroes"
            headers = {'Authorization': 'Bearer '+sessao['access_token']}
            antes = contexto.request.get(endpoint, headers=headers).json()[0]['geometria']
            vertice = page.locator('.mapa-vertice').first
            vertice.scroll_into_view_if_needed()
            caixa = vertice.bounding_box()
            page.mouse.move(caixa['x']+10, caixa['y']+10)
            page.mouse.down()
            page.mouse.move(caixa['x']+30, caixa['y']+25, steps=8)
            page.mouse.up()
            page.get_by_role('button', name='Salvar', exact=True).click()
            page.locator('#dialog').wait_for(state='hidden')
            depois = contexto.request.get(endpoint, headers=headers).json()[0]['geometria']
            assert antes != depois
            page.locator('[data-action^="editar-quarteirao:"]').click()
        page.get_by_role('button', name='Limpar desenho').click()
        page.get_by_role('button', name='Salvar', exact=True).click()
        page.locator('#dialog').wait_for(state='hidden')
        page.locator('[data-action^="editar-quarteirao:"]').click()
        page.locator('.mapa-desenho').filter(has_text='Nenhum contorno').wait_for()
        page.get_by_role('button', name='Cancelar', exact=True).click()
        # Permissão negada e callback tardio após fechar não quebram o modal.
        page.evaluate('() => { navigator.geolocation.watchPosition = (_, erro) => { setTimeout(() => erro({code: 1}), 100); return 999; }; }')
        page.locator('[data-action="novo-quarteirao"]').click()
        page.locator('.mapa-estado').filter(has_text='Permissão de localização negada').wait_for()
        page.get_by_role('button', name='Cancelar', exact=True).click()
        page.locator('[data-action="novo-quarteirao"]').click()
        page.get_by_role('button', name='Cancelar', exact=True).click()
        page.wait_for_timeout(150)
        assert erros == []
        browser.close()


def test_localizacao_refinada_sem_mover_desenho(servidor_mapa):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page()
        page.route('https://tile.openstreetmap.org/**', lambda rota: rota.abort())
        page.goto(servidor_mapa)
        page.evaluate('''async () => {
            const { criarInterface } = await import('/static/views/interface.js');
            const { camposQuarteirao } = await import('/static/views/formularios.js');
            const { montarMapaQuarteirao } = await import('/static/views/mapa-quarteirao.js');
            const criar = L.map;
            L.map = (...args) => (window.mapaTeste = criar(...args));
            window.buscas = []; window.cancelados = [];
            navigator.geolocation.watchPosition = (sucesso, erro) => buscas.push({sucesso, erro}) - 1;
            navigator.geolocation.clearWatch = (id) => cancelados.push(id);
            const interfaceMapa = criarInterface(() => {});
            window.abrirMapa = (dados = {}) => interfaceMapa.modal('Mapa teste', camposQuarteirao, dados, () => {}, 'Salvar', montarMapaQuarteirao);
            window.enviarPosicao = (id, accuracy, latitude, longitude, timestamp = Date.now()) => buscas[id].sucesso({coords: {accuracy, latitude, longitude}, timestamp});
            abrirMapa();
        }''')
        page.evaluate('enviarPosicao(0, 5000, -23.55, -46.63)')
        assert page.locator('.mapa-estado').get_attribute('data-precisao') == 'baixa'
        assert page.evaluate('mapaTeste.getZoom()') < 16
        page.evaluate('enviarPosicao(0, 8, -3.73, -38.53)')
        page.locator('.mapa-estado').filter(has_text='precisão aproximada de 8 m').wait_for()
        assert page.evaluate('mapaTeste.getZoom()') == 18
        assert page.evaluate('mapaTeste.getCenter().lat') == pytest.approx(-3.73)
        assert page.evaluate('cancelados') == [0]
        # Depois de uma interação manual, uma posição melhor não desloca o desenho.
        page.get_by_role('button', name='Minha localização', exact=True).click()
        page.evaluate('enviarPosicao(1, 3000, -3.73, -38.53)')
        page.locator('.mapa-canvas').dispatch_event('pointerdown')
        centro = page.evaluate('[mapaTeste.getCenter().lat, mapaTeste.getCenter().lng, mapaTeste.getZoom()]')
        page.evaluate('enviarPosicao(1, 8, -4.0, -39.0)')
        assert page.evaluate('[mapaTeste.getCenter().lat, mapaTeste.getCenter().lng, mapaTeste.getZoom()]') == centro
        page.get_by_role('button', name='Cancelar', exact=True).click()
        page.locator('#dialog').wait_for(state='hidden')
        page.evaluate('abrirMapa({geometria: {type: "Polygon", coordinates: [[[-38.53, -3.73], [-38.529, -3.73], [-38.529, -3.731], [-38.53, -3.73]]]}})')
        centro = page.evaluate('[mapaTeste.getCenter().lat, mapaTeste.getCenter().lng]')
        page.evaluate('enviarPosicao(2, 8, -23.55, -46.63)')
        assert page.evaluate('[mapaTeste.getCenter().lat, mapaTeste.getCenter().lng]') == centro
        browser.close()
