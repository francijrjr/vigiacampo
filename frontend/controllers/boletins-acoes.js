import { baixar } from "../utils/download.js";
import { api, usuarioAtual } from "../models/api.js";
import { camposBoletim, camposImovelBoletim } from "../views/boletim.js";

import { estado } from "../models/estado.js";

export function criarAcoesBoletins({ render, modal }) {
  async function executarNovoBoletim() {
    const registro = estado.registroAberto;
    return modal(
      "Novo Boletim de Reconhecimento",
      camposBoletim,
      {
        municipio: registro.municipio,
        localidade: registro.zona || "",
        responsavel: usuarioAtual().full_name,
        funcao_responsavel: "AGENTE",
        data: registro.data,
        categoria: "Urbana",
      },
      async (dados) => {
        const novo = await api(`/registros/${registro.id}/boletins`, {
          method: "POST",
          body: dados,
        });
        location.hash = `boletim/${registro.id}/${novo.id}`;
      },
      "Criar boletim",
    );
  }

  async function executarEditarBoletim() {
    return modal(
      "Editar cabeçalho",
      camposBoletim,
      estado.boletimAberto,
      (dados) =>
        api(
          `/registros/${estado.boletimAberto.registro_id}/boletins/${estado.boletimAberto.id}`,
          { method: "PUT", body: dados },
        ),
    );
  }

  async function executarPdfBoletim() {
    return baixar(
      `/registros/${estado.boletimAberto.registro_id}/boletins/${estado.boletimAberto.id}/pdf`,
      `boletim-quarteirao-${estado.boletimAberto.quarteirao_numero}.pdf`,
    );
  }

  async function executarNovoImovelBoletim(valor) {
    const boletim = estado.boletimAberto;
    const anterior = boletim.imoveis.at(-1);
    const dados = valor
      ? boletim.imoveis.find((imovel) => imovel.id === Number(valor))
      : {
          logradouro: anterior?.logradouro || "",
          lado: anterior?.lado || "",
          tipo: "RESIDENCIAL",
        };
    return modal(
      valor ? "Editar imóvel do boletim" : "Adicionar imóvel ao boletim",
      camposImovelBoletim,
      dados,
      (payload) =>
        api(
          `/registros/${boletim.registro_id}/imoveis${valor ? "/" + valor : ""}`,
          {
            method: valor ? "PATCH" : "POST",
            body: { ...payload, quarteirao_id: boletim.quarteirao_id },
          },
        ),
    );
  }

  async function executarExcluirImovelBoletim(valor) {
    if (
      !confirm(
        "Excluir este imóvel e os dados da visita? O fechamento do boletim será atualizado.",
      )
    )
      return;
    await api(
      `/registros/${estado.boletimAberto.registro_id}/imoveis/${valor}`,
      { method: "DELETE" },
    );
    return render();
  }

  return {
    "novo-boletim": executarNovoBoletim,
    "editar-boletim": executarEditarBoletim,
    "pdf-boletim": executarPdfBoletim,
    "novo-imovel-boletim": executarNovoImovelBoletim,
    "editar-imovel-boletim": executarNovoImovelBoletim,
    "excluir-imovel-boletim": executarExcluirImovelBoletim,
  };
}
