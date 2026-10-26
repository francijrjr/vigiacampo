import { baixar } from "../utils/download.js";
import { api } from "../models/api.js";
import { lerFichaAntivetorial } from "../views/antivetorial.js";

export function criarAcoesAntivetorial({ render, avisar }) {
  async function salvarAntivetorial() {
    const formulario = document.querySelector("#antivetorial-form");
    if (!formulario || formulario.dataset.editavel !== "true") return;
    const botao = formulario.querySelector("[type=submit]");
    botao.disabled = true;
    try {
      const id = location.hash.split("/")[1];
      await api(`/registros/${id}/antivetorial`, { method: "PUT", body: lerFichaAntivetorial(formulario) });
      avisar("Ficha antivetorial salva com sucesso.");
      await render();
    } finally { botao.disabled = false; }
  }
  async function pdfAntivetorial() {
    const id = location.hash.split("/")[1];
    return baixar(`/registros/${id}/antivetorial/pdf`, `registro-antivetorial-${id}.pdf`);
  }
  return { "salvar-antivetorial": salvarAntivetorial, "pdf-antivetorial": pdfAntivetorial };
}
