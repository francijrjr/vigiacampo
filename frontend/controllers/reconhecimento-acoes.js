import { api, usuarioAtual } from "../models/api.js";
import { estado } from "../models/estado.js";
import { montarMapaQuarteirao } from "../views/mapa-quarteirao.js";
import { camposTerritorio, visualizacaoTerritorio } from "../views/reconhecimento.js";
import { camposBoletim } from "../views/boletim.js";
import { escapar } from "../views/formularios.js";

export function criarAcoesReconhecimento({ render, modal, dialog }) {
  const normalizar = (valor) => String(valor || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();

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

  async function executarAbrirBoletimTerritorio(valor) {
    const territorio = estado.territorioAtual.find((item) => item.id === Number(valor));
    if (!territorio) throw new Error("Quarteirão não encontrado. Atualize a lista e tente novamente.");
    const registros = await api("/registros/?skip=0&limit=100");
    const candidatos = registros.filter((registro) => {
      const zona = normalizar(registro.zona);
      return zona && [normalizar(territorio.localidade), normalizar(territorio.zona)].includes(zona);
    });
    document.querySelector("#dialog-title").textContent = `Boletim · QT ${territorio.quarteirao_numero}`;
    document.querySelector("#dialog-body").innerHTML = `<section class="boletim-territorio-escolha">
      <p>Escolha o registro diário que receberá o <strong>Boletim de Reconhecimento</strong> deste quarteirão.</p>
      ${candidatos.length ? `<div class="boletim-territorio-registros">${candidatos.map((registro) => `<button type="button" data-action="selecionar-registro-boletim:${territorio.id},${registro.id}"><span>${new Date(`${registro.data}T12:00:00`).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })}</span><strong>${escapar(registro.municipio)}</strong><small>${escapar(registro.zona || "Sem localidade")} · ${escapar(registro.atividade)}</small></button>`).join("")}</div>` : `<div class="boletim-territorio-vazio"><strong>Nenhum registro diário encontrado para ${escapar(territorio.localidade)}.</strong><span>Crie o registro diário primeiro e depois abra o boletim deste quarteirão.</span></div>`}
      <footer><button type="button" class="secondary" data-fechar-visualizacao>Fechar</button></footer>
    </section>`;
    dialog.showModal();
    document.querySelector("[data-fechar-visualizacao]").onclick = () => dialog.close();
  }

  async function executarSelecionarRegistroBoletim(valor) {
    const [territorioId, registroId] = valor.split(",").map(Number);
    const territorio = estado.territorioAtual.find((item) => item.id === territorioId);
    if (!territorio) throw new Error("Quarteirão não encontrado. Atualize a lista e tente novamente.");
    const registro = await api(`/registros/${registroId}`);
    let quarteirao = registro.quarteiroes.find((item) => String(item.numero) === String(territorio.quarteirao_numero));
    if (!quarteirao) {
      quarteirao = await api(`/registros/${registro.id}/quarteiroes`, {
        method: "POST",
        body: { numero: territorio.quarteirao_numero, sequencia: 1, lado: "1", logradouro: territorio.logradouros || null, geometria: territorio.geometria || null },
      });
    }
    const boletins = await api(`/registros/${registro.id}/boletins`);
    const existente = boletins.find((item) => item.quarteirao_id === quarteirao.id);
    if (existente) {
      dialog.close();
      location.hash = `boletim/${registro.id}/${existente.id}`;
      return;
    }
    dialog.close();
    modal(
      `Criar Boletim · QT ${territorio.quarteirao_numero}`,
      camposBoletim,
      {
        uf: "CE",
        distrito: territorio.distrito || "20ª CRES",
        municipio: territorio.municipio,
        localidade: territorio.localidade,
        sublocal: territorio.zona || "",
        categoria: territorio.categoria,
        quarteirao_numero: territorio.quarteirao_numero,
        responsavel: usuarioAtual().full_name,
        funcao_responsavel: "AGENTE",
        data: registro.data,
      },
      async (dados) => {
        const novo = await api(`/registros/${registro.id}/boletins`, { method: "POST", body: { ...dados, quarteirao_id: quarteirao.id } });
        location.hash = `boletim/${registro.id}/${novo.id}`;
      },
      "Criar boletim",
    );
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
    "abrir-boletim-territorio": executarAbrirBoletimTerritorio,
    "selecionar-registro-boletim": executarSelecionarRegistroBoletim,
    "novo-territorio": executarSalvarTerritorio,
    "editar-territorio": executarSalvarTerritorio,
    "excluir-territorio": executarExcluirTerritorio,
    "limpar-filtros-territorio": executarLimparFiltrosTerritorio,
    "ir-modulos": executarIrModulos,
  };
}
