import { listaRascunhos } from "../views/rascunhos.js";

import { api } from "../models/api.js";

import { camposRegistro } from "../views/formularios.js";

import { fila, guardarFila } from "../models/rascunhos.js";

export function criarAcoesRascunhos({ render, dialog, modal, avisar }) {
  async function executarFila() {
    document.querySelector("#dialog-title").textContent =
      "Registros neste aparelho";
    document.querySelector("#dialog-body").innerHTML = listaRascunhos(fila());
    dialog.showModal();
    return;
  }

  async function executarEditarFila(valor) {
    dialog.close();
    return modal(
      "Editar registro neste aparelho",
      camposRegistro,
      fila()[Number(valor)],
      (dados) => {
        const itens = fila();
        itens[Number(valor)] = { ...itens[Number(valor)], ...dados };
        guardarFila(itens);
      },
    );
  }

  async function executarExcluirFila(valor) {
    if (!confirm("Excluir este rascunho do aparelho?")) return;
    guardarFila(fila().filter((_, i) => i !== Number(valor)));
    dialog.close();

    await render();
  }

  async function executarSincronizar() {
    const itens = fila();
    if (!itens.length) return;
    await api("/registros/sync", {
      method: "POST",
      body: { registros: itens },
    });
    guardarFila([]);
    dialog.close();
    avisar("Registros enviados com sucesso.");

    await render();
  }

  return {
    fila: executarFila,
    "editar-fila": executarEditarFila,
    "excluir-fila": executarExcluirFila,
    sincronizar: executarSincronizar,
  };
}
