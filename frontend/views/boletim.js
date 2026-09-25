import { escapar as e, tipos } from "./formularios.js";
import { icone } from "./icones.js";

export const funcoesResponsavel = {
  AGENTE: "Agente",
  INSPETOR: "Inspetor",
  CHEFE_EQUIPE: "Chefe de equipe",
  INSPETOR_GERAL: "Inspetor geral",
};
const ufs = Object.fromEntries(
  [
    "",
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
  ].map((uf) => [uf, uf || "Selecione a UF"]),
);
export const camposBoletim = [
  ["uf", "UF", "select", ufs],
  ["distrito", "Distrito", "text"],
  ["municipio", "Município", "text"],
  ["localidade", "Localidade", "text"],
  ["subdistrito", "Subdist.", "optional"],
  ["sublocal", "Sublocal", "optional"],
  ["categoria", "Categoria", "text"],
  ["quarteirao_numero", "Quart. nº", "text"],
  ["responsavel", "Responsável — nome", "text"],
  ["funcao_responsavel", "Função do responsável", "select", funcoesResponsavel],
  ["data", "Data", "date"],
];
export const camposImovelBoletim = [
  ["logradouro", "Rua ou logradouro", "text"],
  ["numero", "Número", "text"],
  ["lado", "Lado", "text"],
  ["tipo", "Tipo de imóvel", "select", tipos],
];
const siglas = {
  RESIDENCIAL: "R",
  COMERCIAL: "C",
  TERRENO: "TB",
  PONTO_ESTRATEGICO: "PE",
  OUTRO: "O",
};
const acao = (texto, nome, desenho, classe = "secondary") =>
  `<button class="${classe}" data-action="${nome}">${icone(desenho)}<span>${texto}</span></button>`;

export function cartoesBoletins(boletins, registroId, editavel) {
  return `<section class="panel"><div class="panel-heading"><div><h2>Boletim de Reconhecimento</h2><p>Identifique a localidade e cadastre as ruas e os imóveis de cada quarteirão.</p></div>${editavel ? acao("Novo boletim", "novo-boletim", "plus", "primary") : ""}</div>${boletins.length ? boletins.map((boletim) => `<div class="item-card"><div><strong>Quarteirão ${e(boletim.quarteirao_numero)} · ${e(boletim.localidade)}</strong><p>${e(boletim.municipio)} / ${e(boletim.uf)} · ${boletim.fechamento.total} imóveis · ${e(boletim.responsavel)}</p></div><a class="text-button" href="#boletim/${registroId}/${boletim.id}">Abrir boletim ${icone("arrow-right")}</a></div>`).join("") : `<div class="empty boletim-empty">${icone("clipboard-list")}<h3>Prepare o boletim para a visita</h3><p>Preencha UF, distrito, localidade e responsável. Depois, inclua os imóveis reconhecidos.</p>${editavel ? acao("Criar boletim", "novo-boletim", "plus", "primary") : ""}</div>`}</section>`;
}

export function telaBoletim(boletim) {
  const campo = (label, valor) =>
    `<div class="ficha-campo"><span>${e(label)}</span><strong>${e(valor || "—")}</strong></div>`;
  const qtd = Math.max(12, Math.ceil(boletim.imoveis.length / 2));
  function tabela(inicio) {
    const linhas = Array.from(
      { length: qtd },
      (_, i) => boletim.imoveis[inicio + i],
    );
    return `<div class="ficha-table-wrap"><table class="ficha-table"><thead><tr><th>Rua ou logradouro</th><th>Número</th><th>Lado</th><th>Tipo</th><th class="ficha-acoes">Visita</th></tr></thead><tbody>${linhas.map((imovel) => (imovel ? `<tr><td>${e(imovel.logradouro || "—")}</td><td>${e(imovel.numero)}</td><td>${e(imovel.lado || "—")}</td><td><abbr title="${e(tipos[imovel.tipo])}">${siglas[imovel.tipo]}</abbr></td><td class="ficha-acoes"><div><a class="icon-button" href="#visita/${boletim.registro_id}/${imovel.id}" aria-label="Abrir visita do imóvel ${e(imovel.numero)}" title="Abrir visita">${icone("arrow-right")}</a>${boletim.editavel ? `<button class="icon-button" data-action="editar-imovel-boletim:${imovel.id}" aria-label="Editar imóvel ${e(imovel.numero)}" title="Editar imóvel">${icone("pencil")}</button><button class="icon-button" data-action="excluir-imovel-boletim:${imovel.id}" aria-label="Excluir imóvel ${e(imovel.numero)}" title="Excluir imóvel">${icone("trash-2")}</button>` : ""}</div></td></tr>` : '<tr class="linha-vazia"><td>&nbsp;</td><td></td><td></td><td></td><td class="ficha-acoes"></td></tr>')).join("")}</tbody></table></div>`;
  }
  return `<a class="subtle-link" href="#registro/${boletim.registro_id}">${icone("arrow-left")} Voltar ao registro</a><div class="page-heading boletim-heading"><div><h1>Boletim de Reconhecimento</h1><p>Quarteirão ${e(boletim.quarteirao_numero)} · ${e(boletim.localidade)} · ${boletim.fechamento.total} imóveis</p></div><div class="actions">${acao("Baixar PDF / imprimir", "pdf-boletim", "download")}${boletim.editavel ? acao("Editar cabeçalho", "editar-boletim", "pencil") : ""}</div></div><section class="ficha"><header class="ficha-title"><span class="eyebrow">PCFAD</span><p>Programa de Controle da Febre Amarela e Dengue</p><h2>Boletim de Reconhecimento</h2></header><div class="ficha-cabecalho">${campo("UF", boletim.uf)}${campo("Distrito", boletim.distrito)}${campo("Município", boletim.municipio)}${campo("Localidade", boletim.localidade)}${campo("Subdist.", boletim.subdistrito)}${campo("Sublocal", boletim.sublocal)}${campo("Categoria", boletim.categoria)}${campo("Quart. nº", boletim.quarteirao_numero)}${campo("Responsável", boletim.responsavel)}${campo("Função do responsável", funcoesResponsavel[boletim.funcao_responsavel])}</div><div class="ficha-section-heading"><div><h3>Ruas e imóveis</h3><p>R · Residencial &nbsp; C · Comercial &nbsp; TB · Terreno Baldio &nbsp; PE · Ponto Estratégico &nbsp; O · Outros</p></div>${boletim.editavel ? acao("Adicionar imóvel", "novo-imovel-boletim", "plus", "primary") : ""}</div><div class="ficha-colunas">${tabela(0)}${tabela(qtd)}</div><section class="ficha-fechamento"><h3>Fechamento</h3><div>${[
    ["Residencial", "residencial", "R"],
    ["Comercial", "comercial", "C"],
    ["Terreno Baldio", "terreno_baldio", "TB"],
    ["Ponto Estratégico", "ponto_estrategico", "PE"],
    ["Outros", "outros", "O"],
    ["Total geral", "total", ""],
  ]
    .map(
      ([label, chave, sigla]) =>
        `<article class="${chave === "total" ? "total" : ""}"><span>${label} <small>${sigla}</small></span><strong>${boletim.fechamento[chave]}</strong></article>`,
    )
    .join(
      "",
    )}</div></section><footer class="ficha-footer">${campo("Nome", boletim.responsavel)}${campo("Data", new Date(boletim.data + "T12:00:00").toLocaleDateString("pt-BR"))}<div class="ficha-assinatura">Assinatura: <span></span><small>Preencher na via impressa.</small></div></footer></section>`;
}
