import { colecoes, escapar as e, pendencias, tipos } from "./formularios.js";
import { icone } from "./icones.js";

import { empty, botao, titulo } from "./componentes.js";

export function visita({
  registro: registro,
  imovel: imovel,
  editar,
  abaVisita,
}) {
  const abas = {
    ...Object.fromEntries(
      Object.entries(colecoes).map(([k, v]) => [k, v.titulo]),
    ),
    fotos: "Fotos",
  };
  let conteudo;
  if (abaVisita === "fotos") {
    conteudo = imovel.fotos.length
      ? `<div class="photos">${imovel.fotos.map((f) => `<article><img data-foto="${f.id}" alt="${e(f.descricao || "Foto da visita")}" loading="lazy"><p>${e(f.descricao || "Evidência da visita")}</p>${editar ? botao("Excluir", `excluir-foto:${f.id}`, "danger") : ""}</article>`).join("")}</div>`
      : empty(
          "Nenhuma foto adicionada",
          "As fotos ficam vinculadas à visita e não entram no PDF.",
        );
  } else {
    const definicao = colecoes[abaVisita],
      itens = imovel[abaVisita.replaceAll("-", "_")];
    conteudo = itens.length
      ? itens
          .map(
            (item) =>
              `<div class="item-card"><div>${definicao.campos.map(([k, label, tipo, opcoes]) => `<p><strong>${e(label)}:</strong> ${e(tipo === "select" ? opcoes[item[k]] : (item[k] ?? "—"))}</p>`).join("")}</div>${editar ? `<div class="actions">${botao("Editar", `editar-item:${item.id}`)}${botao("Excluir", `excluir-item:${item.id}`, "danger")}</div>` : ""}</div>`,
          )
          .join("")
      : empty(
          `Sem ${definicao.titulo.toLowerCase()} nesta visita`,
          "Adicione os dados encontrados em campo.",
        );
  }
  return (
    `<a class="subtle-link" href="#registro/${registro.id}">${icone("arrow-left")} Voltar ao registro</a><br><br>` +
    titulo(
      `Visita ao imóvel nº ${imovel.numero}`,
      `${tipos[imovel.tipo]} · ${pendencias[imovel.pendencia]}`,
      editar ? botao("Editar imóvel", "editar-imovel") : "",
    ) +
    `<section class="panel"><div class="visit-tabs">${Object.entries(abas)
      .map(
        ([k, v]) =>
          `<button class="secondary ${abaVisita === k ? "active" : ""}" data-action="aba:${k}">${v}</button>`,
      )
      .join(
        "",
      )}</div><div class="panel-heading"><h2>${e(abas[abaVisita])}</h2>${editar ? botao("+ Adicionar", abaVisita === "fotos" ? "nova-foto" : "novo-item", "primary") : ""}</div>${conteudo}</section>${editar ? botao("Excluir imóvel", "excluir-imovel", "danger") : ""}`
  );
}
