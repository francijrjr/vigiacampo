import { buscarLocalizacao } from "../utils/geolocalizacao.js";
export function montarMapaQuarteirao(form, dados) {
  const painel = document.createElement("section");
  painel.className = "quarteirao-mapa";
  painel.innerHTML = `<div class="mapa-intro"><h3>Desenhe o quarteirão</h3><p>Toque nos cantos da quadra e conclua o contorno. Arraste os pontos para ajustar.</p></div>
    <div class="mapa-controles"><button type="button" class="secondary" data-localizar>Minha localização</button><button type="button" class="secondary" data-desfazer>Desfazer ponto</button><button type="button" class="secondary" data-limpar>Limpar desenho</button><button type="button" class="primary" data-concluir>Concluir contorno</button></div>
    <p class="mapa-estado" role="status"></p><div class="mapa-canvas" aria-label="Mapa para desenhar o quarteirão" tabindex="0"></div><p class="mapa-desenho" role="status"></p><p class="mapa-rede" role="status"></p>`;
  form.querySelector(".form-error").before(painel);

  const status = painel.querySelector(".mapa-estado");
  const desenho = painel.querySelector(".mapa-desenho");
  const localizar = painel.querySelector("[data-localizar]");
  const concluir = painel.querySelector("[data-concluir]");
  const numero = form.elements.numero;
  if (!window.L) {
    status.textContent = "Não foi possível carregar o mapa. Reabra o formulário com conexão à internet.";
    painel.querySelectorAll("button").forEach((b) => { b.disabled = true; });
    return { ler: () => ({ geometria: dados.geometria || null }), destruir() {} };
  }
  const L = window.L;
  let pontos = dados.geometria?.coordinates[0].slice(0, -1).map(([lng, lat]) => [lat, lng]) || [];
  let fechado = pontos.length > 0, ativo = true, marcador, precisao, cancelarBusca;
  let acompanharCentro = !pontos.length;
  const mapa = L.map(painel.querySelector(".mapa-canvas"), { doubleClickZoom: false, worldCopyJump: true }).setView([-14.2, -51.9], 4);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>',
  }).on("tileerror", () => {
    painel.querySelector(".mapa-rede").textContent = "Não foi possível carregar parte do mapa. Verifique sua conexão antes de desenhar.";
  }).addTo(mapa);
  const camadas = L.layerGroup().addTo(mapa);
  // Uma leitura tardia não deve tirar o usuário do local escolhido manualmente.
  const interromperCentro = () => { acompanharCentro = false; };
  mapa.on("dragstart", interromperCentro);
  const canvas = painel.querySelector(".mapa-canvas");
  canvas.addEventListener("pointerdown", interromperCentro);
  canvas.addEventListener("wheel", interromperCentro);
  canvas.addEventListener("keydown", interromperCentro);
  const icone = L.divIcon({ className: "mapa-vertice", iconSize: [20, 20], iconAnchor: [10, 10] });
  function atualizar() {
    form.querySelector(".form-error").textContent = "";
    camadas.clearLayers();
    const linha = fechado ? L.polygon(pontos, { color: "#318ab0", weight: 4, fillColor: "#60afd0", fillOpacity: 0.45, interactive: false })
      : L.polyline(pontos, { color: "#318ab0", weight: 3, dashArray: "6 6", interactive: false });
    linha.addTo(camadas);
    if (fechado) {
      const rotulo = document.createElement("span");
      rotulo.textContent = `QT ${numero.value || "—"}`;
      linha.bindTooltip(rotulo, { permanent: true, direction: "center", className: "mapa-rotulo" });
    }
    pontos.forEach((ponto, indice) => {
      const vertice = L.marker(ponto, { icon: icone, draggable: true, title: `Canto ${indice + 1}`, autoPan: true }).addTo(camadas);
      vertice.on("dragend", () => {
        const p = vertice.getLatLng().wrap();
        pontos[indice] = [p.lat, p.lng];
        atualizar();
      });
    });
    concluir.disabled = fechado || pontos.length < 3;
    painel.querySelector("[data-desfazer]").disabled = !pontos.length;
    painel.querySelector("[data-limpar]").disabled = !pontos.length;
    desenho.textContent = fechado ? `Contorno concluído · ${pontos.length} cantos. Arraste os pontos para ajustar.`
      : pontos.length ? `${pontos.length} cantos marcados. Adicione pelo menos 3 e conclua o contorno.` : "Nenhum contorno desenhado. O desenho é opcional.";
  }
  mapa.on("click", ({ latlng }) => {
    acompanharCentro = false;
    if (fechado) return;
    if (pontos.length >= 300) { desenho.textContent = "Limite de 300 pontos atingido. Conclua o contorno."; return; }
    const p = latlng.wrap();
    pontos.push([p.lat, p.lng]); atualizar();
  });
  concluir.onclick = () => { fechado = true; atualizar(); };
  painel.querySelector("[data-desfazer]").onclick = () => { pontos.pop(); fechado = false; atualizar(); };
  painel.querySelector("[data-limpar]").onclick = () => { pontos = []; fechado = false; atualizar(); };
  numero.addEventListener("input", atualizar);
  function localizarUsuario(centralizar = true) {
    cancelarBusca?.();
    if (!window.isSecureContext || !navigator.geolocation) {
      status.textContent = "Localização indisponível. Acesse por HTTPS ou navegue pelo mapa manualmente."; return;
    }
    acompanharCentro = Boolean(centralizar);
    localizar.textContent = "Buscar novamente";
    status.textContent = "Buscando sua localização… Permita o acesso quando o navegador solicitar.";
    // Remove estimativas antigas enquanto uma nova busca está em andamento.
    if (marcador) { mapa.removeLayer(marcador); marcador = null; }
    if (precisao) { mapa.removeLayer(precisao); precisao = null; }
    function mostrar({ coords }, buscando) {
      if (!ativo) return;
      const centro = [coords.latitude, coords.longitude];
      const impreciso = coords.accuracy > 50;
      const cor = impreciso ? "#b57719" : "#2376c5";
      if (marcador) mapa.removeLayer(marcador);
      if (precisao) mapa.removeLayer(precisao);
      precisao = L.circle(centro, { radius: coords.accuracy, color: cor, weight: 1, fillOpacity: 0.09, interactive: false }).addTo(mapa);
      marcador = null;
      if (!impreciso) marcador = L.circleMarker(centro, { radius: 7, color: "white", weight: 3, fillColor: cor, fillOpacity: 1, interactive: false }).addTo(mapa);
      if (acompanharCentro) {
        if (impreciso) mapa.fitBounds(precisao.getBounds(), { padding: [25, 25], maxZoom: 16, animate: false });
        else mapa.setView(centro, 18, { animate: false });
      }
      status.dataset.precisao = impreciso ? "baixa" : "boa";
      status.textContent = impreciso
        ? `${buscando ? "Aguardando uma leitura mais precisa…" : "Não foi possível obter precisão de rua. Confira as permissões de localização do dispositivo ou ajuste o mapa manualmente."}`
        : `Localização estimada pelo dispositivo · precisão aproximada de ${Math.round(coords.accuracy)} m. Confira o local antes de desenhar.`;
    }
    cancelarBusca = buscarLocalizacao({
      atualizar: (posicao) => mostrar(posicao, true),
      concluir: (posicao) => { localizar.textContent = "Minha localização"; mostrar(posicao, false); },
      falhar: (erro) => {
        if (!ativo) return;
        localizar.textContent = "Minha localização";
        status.dataset.precisao = "baixa";
        status.textContent = ({ 1: "Permissão de localização negada. Habilite-a no navegador ou navegue manualmente.", 2: "Localização indisponível. Tente novamente ou navegue manualmente.", 3: "Não foi possível obter uma localização recente. Tente novamente ou navegue manualmente." })[erro.code] || "Não foi possível localizar você. Navegue pelo mapa manualmente.";
      },
    });
  }
  localizar.onclick = () => localizarUsuario("forcar");
  atualizar();
  if (pontos.length) mapa.fitBounds(pontos, { padding: [35, 35], maxZoom: 19 });
  localizarUsuario(!pontos.length);
  const observer = new ResizeObserver(() => mapa.invalidateSize());
  observer.observe(painel.querySelector(".mapa-canvas"));
  return {
    ler() {
      if (pontos.length && !fechado) throw new Error("Conclua o contorno ou limpe o desenho antes de salvar.");
      const coordenadas = pontos.map(([lat, lng]) => [lng, lat]);
      return { geometria: fechado ? { type: "Polygon", coordinates: [[...coordenadas, coordenadas[0]]] } : null };
    },
    destruir() {
      ativo = false;
      cancelarBusca?.();
      observer.disconnect();
      numero.removeEventListener("input", atualizar);
      canvas.removeEventListener("pointerdown", interromperCentro);
      canvas.removeEventListener("wheel", interromperCentro);
      canvas.removeEventListener("keydown", interromperCentro);
      mapa.remove();
    },
  };
}
