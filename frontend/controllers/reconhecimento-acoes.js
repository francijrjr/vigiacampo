import { api, usuarioAtual } from "../models/api.js";
import { estado } from "../models/estado.js";
import { montarMapaQuarteirao } from "../views/mapa-quarteirao.js";
import { camposTerritorio } from "../views/reconhecimento.js";

export function criarAcoesReconhecimento({ render, modal }) {
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
        ? `Editar quarteirão permanente QT ${atual?.quarteirao_numero || ""}`
        : "Novo quarteirão permanente · Reconhecimento Geográfico",
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
        `Excluir permanentemente o quarteirão QT ${item?.quarteirao_numero || valor} da localidade ${item?.localidade || ""}?`,
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
    "novo-territorio": executarSalvarTerritorio,
    "editar-territorio": executarSalvarTerritorio,
    "excluir-territorio": executarExcluirTerritorio,
    "limpar-filtros-territorio": executarLimparFiltrosTerritorio,
    "ir-modulos": executarIrModulos,
  };
}
