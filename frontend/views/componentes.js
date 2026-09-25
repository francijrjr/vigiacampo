import { escapar as e, situacoes } from "./formularios.js";
import { icone } from "./icones.js";

export const badge = (registro) =>
  `<span class="badge ${e(registro.status)}">${icone(registro.status === "SYNCED" ? "circle-check" : "circle-dashed")} ${e(situacoes[registro.status])}</span>`;
export const empty = (titulo, texto, botao = "") =>
  `<div class="empty"><div class="empty-icon">${icone("clipboard-list")}</div><h3>${e(titulo)}</h3><p>${e(texto)}</p>${botao}</div>`;
export const painel = (titulo, conteudo, acao = "") =>
  `<section class="panel"><div class="panel-heading"><h2>${e(titulo)}</h2>${acao}</div>${conteudo}</section>`;
const iconesAcao = {
  sair: "log-out",
  pdf: "download",
  duplicar: "copy",
  senha: "key-round",
  fila: "clipboard-list",
  sincronizar: "send",
  recarregar: "refresh-cw",
  "enviar-registro": "send",
  "limpar-filtros": "list-filter",
};
export const botao = (texto, acao, classe = "secondary") => {
  const nome = acao.split(":")[0];
  const desenho =
    iconesAcao[nome] ||
    (nome.startsWith("novo") || nome.startsWith("nova")
      ? "plus"
      : nome.startsWith("editar")
        ? "pencil"
        : nome.startsWith("excluir")
          ? "trash-2"
          : null);
  const label = texto.replace(/^\+\s*/, "").replace(/\s*[↗↓]$/, "");
  return `<button class="${classe}" data-action="${acao}">${desenho ? icone(desenho) : ""}<span>${e(label)}</span></button>`;
};
export const titulo = (nome, descricao, acao = "") =>
  `<div class="page-heading"><div><h1>${e(nome)}</h1><p>${e(descricao)}</p></div>${acao}</div>`;
