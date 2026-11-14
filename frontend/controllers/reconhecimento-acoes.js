import { api, usuarioAtual } from "../models/api.js";
import { estado } from "../models/estado.js";
import { montarMapaQuarteirao } from "../views/mapa-quarteirao.js";
import { camposTerritorio, visualizacaoTerritorio } from "../views/reconhecimento.js";

export function criarAcoesReconhecimento({ render, modal, dialog }) {
  function abrirMapaConsulta(container, geometria) {
    if (!container || !geometria || !window.L) return;
    const mapa = window.L.map(container, { zoomControl: true, scrollWheelZoom: false, attributionControl: false });
    window.L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(mapa);
    const camada = window.L.geoJSON(geometria, { style: { color: "#176448", weight: 3, fillColor: "#91c9a7", fillOpacity: 0.34 } }).addTo(mapa);
    mapa.fitBounds(camada.getBounds(), { padding: [24, 24], maxZoom: 18 });
    const observer = new ResizeObserver(() => mapa.invalidateSize());
    observer.observe(container);
    dialog.addEventListener("close", () => { observer.disconnect(); mapa.remove(); }, { once: true });
  }

  async function executarVerTerritorio(valor) {
    const item = estado.territorioAtual.find((territorio) => territorio.id === Number(valor));
    if (!item) throw new Error("Quarteirão não encontrado. Atualize a lista e tente novamente.");
    document.querySelector("#dialog-title").textContent = "Consultar quarteirão";
    document.querySelector("#dialog-body").innerHTML = visualizacaoTerritorio(item);
    dialog.showModal();
    document.querySelector("[data-fechar-visualizacao]").onclick = () => dialog.close();
    abrirMapaConsulta(document.querySelector(".territorio-mapa-canvas"), item.geometria);
  }

  async function executarSalvarTerritorio(valor, nome) {
    const editando = nome === "editar-territorio" && valor;
    const atual = editando
      ? estado.territorioAtual.find((item) => item.id === Number(valor))
      : {
          municipio: usuarioAtual()?.municipio || "",
          distrito: "20ª CRES",
          categoria: "Urbana",
          lados: 4,
          residenciais: 0,
          comerciais: 0,
          terrenos_baldios: 0,
          pontos_estrategicos: 0,
          outros: 0,
        };
    return modal(
      editando
        ? `Editar quarteirão QT ${atual?.quarteirao_numero || ""}`
        : "Novo quarteirão · Reconhecimento Geográfico",
      camposTerritorio,
      atual,
      (dados) =>
        api(`/territorio/${editando ? valor : ""}`, {
          method: editando ? "PUT" : "POST",
          body: dados,
        }),
      editando ? "Salvar alterações" : "Cadastrar quarteirão",
      montarMapaQuarteirao,
    );
  }

  async function executarExcluirTerritorio(valor) {
    const item = estado.territorioAtual.find((i) => i.id === Number(valor));
    if (
      !confirm(
        `Excluir o quarteirão QT ${item?.quarteirao_numero || valor} da localidade ${item?.localidade || ""}?`,
      )
    )
      return;
    await api(`/territorio/${valor}`, { method: "DELETE" });
    await render();
  }

  async function executarLimparFiltrosTerritorio() {
    estado.filtrosTerritorio = {};
    await render();
  }

  async function executarIrModulos() {
    location.hash = "modulos";
  }

  return {
    "ver-territorio": executarVerTerritorio,
    "novo-territorio": executarSalvarTerritorio,
    "editar-territorio": executarSalvarTerritorio,
    "excluir-territorio": executarExcluirTerritorio,
    "limpar-filtros-territorio": executarLimparFiltrosTerritorio,
    "ir-modulos": executarIrModulos,
  };
}
