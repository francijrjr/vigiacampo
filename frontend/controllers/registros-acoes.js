import { baixar } from "../utils/download.js";
import { api, ErroConexao, usuarioAtual } from "../models/api.js";

import { camposQuarteirao, camposRegistro } from "../views/formularios.js";
import { estado } from "../models/estado.js";
import { hoje } from "../utils/datas.js";
import { fila, guardarFila } from "../models/rascunhos.js";

export function criarAcoesRegistros({ render, modal }) {
  function novoRegistro() {
    modal(
      "Novo registro diário",
      camposRegistro,
      { municipio: usuarioAtual().municipio, data: hoje(), atividade: "LI" },
      async (dados) => {
        dados.client_id = crypto.randomUUID();
        if (!navigator.onLine) {
          guardarFila([...fila(), dados]);
          return;
        }
        try {
          const registro = await api("/registros/", {
            method: "POST",
            body: dados,
          });
          location.hash = `registro/${registro.id}`;
        } catch (erro) {
          if (erro instanceof ErroConexao) {
            guardarFila([...fila(), dados]);
          } else throw erro;
        }
      },
      "Criar registro",
    );
  }
  async function executarNovoRegistro() {
    return novoRegistro();
  }

  async function executarEditarRegistro() {
    const registro = estado.registroAberto;
    return modal("Editar registro", camposRegistro, registro, (dados) =>
      api(`/registros/${registro.id}`, { method: "PATCH", body: dados }),
    );
  }

  async function executarEnviarRegistro() {
    const registro = estado.registroAberto;

    if (
      !confirm(
        "Enviar este registro? Depois do envio, somente o supervisor poderá alterá-lo.",
      )
    )
      return;
    await api(`/registros/${registro.id}`, {
      method: "PATCH",
      body: { status: "SYNCED", concluido: true },
    });

    await render();
  }

  async function executarDuplicar() {
    const registro = estado.registroAberto;

    const novo = await api(`/registros/${registro.id}/duplicar`, {
      method: "POST",
    });
    location.hash = `registro/${novo.id}`;
    return;
  }

  async function executarPdf() {
    const registro = estado.registroAberto;
    return baixar(
      `/relatorios/registro/${registro.id}/pdf`,
      `registro-${registro.id}.pdf`,
    );
  }

  async function executarExcluirRegistro() {
    const registro = estado.registroAberto;

    if (
      !confirm(
        "Excluir este registro e todas as visitas? Esta ação não pode ser desfeita.",
      )
    )
      return;
    await api(`/registros/${registro.id}`, { method: "DELETE" });
    location.hash = "registros";
    return;
  }

  async function executarNovoQuarteirao(valor, nome) {
    const registro = estado.registroAberto;
    return modal(
      nome === "novo-quarteirao" ? "Adicionar quarteirão" : "Editar quarteirão",
      camposQuarteirao,
      registro.quarteiroes.find(
        (quarteirao) => quarteirao.id === Number(valor),
      ),
      (dados) =>
        api(
          `/registros/${registro.id}/quarteiroes${valor ? `/${valor}` : ""}`,
          {
            method: valor ? "PUT" : "POST",
            body: dados,
          },
        ),
    );
  }

  async function executarExcluirQuarteirao(valor) {
    const registro = estado.registroAberto;

    if (!confirm("Excluir este quarteirão?")) return;
    await api(`/registros/${registro.id}/quarteiroes/${valor}`, {
      method: "DELETE",
    });

    await render();
  }

  return {
    "novo-registro": executarNovoRegistro,
    "editar-registro": executarEditarRegistro,
    "enviar-registro": executarEnviarRegistro,
    duplicar: executarDuplicar,
    pdf: executarPdf,
    "excluir-registro": executarExcluirRegistro,
    "novo-quarteirao": executarNovoQuarteirao,
    "editar-quarteirao": executarNovoQuarteirao,
    "excluir-quarteirao": executarExcluirQuarteirao,
  };
}
