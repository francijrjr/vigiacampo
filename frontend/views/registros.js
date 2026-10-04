import { cartoesBoletins } from "./boletim.js";
import {
  atividades,
  escapar as e,
  pendencias,
  situacoes,
  tipos,
} from "./formularios.js";
import { icone } from "./icones.js";
import { dataBr } from "../utils/datas.js";
import { badge, empty, painel, botao, titulo } from "./componentes.js";
import { filaPainel } from "./layout.js";

export function tabelaRegistros(registros) {
  if (!registros.length)
    return empty(
      "Nenhum registro por aqui",
      "Comece registrando as atividades do seu dia.",
      botao("+ Criar registro", "novo-registro", "primary"),
    );
  return `<div class="table-wrap"><table><thead><tr><th>Data / município</th><th>Área / ciclo</th><th>Atividade</th><th>Imóveis</th><th>Situação</th><th></th></tr></thead><tbody>${registros.map((registro) => `<tr class="registro-linha" data-registro-linha><td><strong>${dataBr(registro.data)}</strong><small>${e(registro.municipio)}</small></td><td><strong>${e(registro.codigo_area)}</strong><small>Ciclo ${e(registro.ciclo)}</small></td><td>${e(atividades[registro.atividade] || registro.atividade)}</td><td>${registro.resumo_imoveis_trabalhados}</td><td>${badge(registro)}</td><td><a class="text-button" data-abrir-registro href="#registro/${registro.id}">Abrir ${icone("arrow-right")}</a></td></tr>`).join("")}</tbody></table></div>`;
}

export function registros({ dados, filtros, pagina, pendentes }) {
  return (
    titulo(
      "Registros diários",
      "O histórico de cada ação em campo.",
      botao("+ Novo registro", "novo-registro", "primary"),
    ) +
    filaPainel(pendentes) +
    `<section class="panel"><form id="filters" class="filters"><label>De<input type="date" name="data_inicio" value="${e(filtros.data_inicio)}"></label><label>Até<input type="date" name="data_fim" value="${e(filtros.data_fim)}"></label><label>Zona / bairro<input name="zona" value="${e(filtros.zona)}" placeholder="Todas as zonas"></label><label>Situação<select name="status"><option value="">Todas</option>${Object.entries(
      situacoes,
    )
      .map(
        ([k, v]) =>
          `<option value="${k}" ${filtros.status === k ? "selected" : ""}>${v}</option>`,
      )
      .join(
        "",
      )}</select></label><button class="primary">Filtrar</button>${botao("Limpar", "limpar-filtros")}</form>${tabelaRegistros(dados)}<div class="pager"><button class="secondary" data-action="anterior" ${!pagina ? "disabled" : ""}>${icone("arrow-left")} Anterior</button><span>Página ${pagina + 1}</span><button class="secondary" data-action="proxima" ${dados.length < 20 ? "disabled" : ""}>Próxima ${icone("arrow-right")}</button></div></section>`
  );
}

export function detalheRegistro({
  registro: registro,
  boletins,
  editar,
  supervisor,
}) {
  return (
    `<a class="subtle-link" href="#registros">${icone("arrow-left")} Voltar aos registros</a><br><br>` +
    titulo(
      `Registro de ${dataBr(registro.data)}`,
      `${registro.municipio} · Área ${registro.codigo_area} · Ciclo ${registro.ciclo}`,
      badge(registro),
    ) +
    cartoesBoletins(boletins, registro.id, editar) +
    `<div class="actions" style="margin-bottom:24px">${editar ? botao("Editar informações", "editar-registro") : ""}${registro.status !== "SYNCED" ? botao("Enviar registro", "enviar-registro", "primary") : ""}${botao("Duplicar", "duplicar")}${supervisor ? botao("Baixar PDF ↓", "pdf") : ""}${editar ? botao("Excluir registro", "excluir-registro", "danger") : ""}</div>` +
    `<div class="detail-grid">${painel("Informações do dia", `<div class="detail-body"><dl class="data-list"><div><dt>Código de série</dt><dd>${e(registro.codigo_serie || "Não informado")}</dd></div><div><dt>Atividade</dt><dd>${e(atividades[registro.atividade])}</dd></div><div><dt>Zona / bairro</dt><dd>${e(registro.zona || "Não informado")}</dd></div><div><dt>Imóveis</dt><dd>${registro.resumo_imoveis_trabalhados}</dd></div><div><dt>Pendências</dt><dd>${registro.resumo_pendencias}</dd></div><div><dt>Depósitos inspecionados</dt><dd>${registro.resumo_depositos_inspecionados}</dd></div><div><dt>Exemplares encontrados</dt><dd>${registro.resumo_exemplares}</dd></div></dl><p class="muted">Observações</p><p style="white-space:pre-wrap">${e(registro.observacoes || "Nenhuma observação.")}</p></div>`)}
    ${painel("Quarteirões", registro.quarteiroes.length ? registro.quarteiroes.map((quarteirao) => `<div class="item-card"><div><strong>Quarteirão ${e(quarteirao.numero)}</strong><p>${e(quarteirao.logradouro || "Rua não informada")}</p></div>${editar ? `<div class="actions">${botao("Editar", `editar-quarteirao:${quarteirao.id}`)}${botao("Excluir", `excluir-quarteirao:${quarteirao.id}`, "danger")}</div>` : ""}</div>`).join("") : empty("Cadastre o primeiro quarteirão", "Organize os imóveis por rua ou quarteirão."), editar ? botao("+ Adicionar", "novo-quarteirao") : "")}</div>` +
    painel(
      "Imóveis e visitas",
      registro.imoveis.length
        ? `<div class="table-wrap"><table><thead><tr><th>Imóvel</th><th>Quarteirão</th><th>Tipo</th><th>Pendência</th><th></th></tr></thead><tbody>${registro.imoveis.map((imovel) => `<tr><td><strong>Nº ${e(imovel.numero)}</strong><small>${e(imovel.complemento)}</small></td><td>${e(registro.quarteiroes.find((quarteirao) => quarteirao.id === imovel.quarteirao_id)?.numero || "—")}</td><td>${e(tipos[imovel.tipo])}</td><td>${e(pendencias[imovel.pendencia])}</td><td><a class="text-button" href="#visita/${registro.id}/${imovel.id}">Abrir visita ${icone("arrow-right")}</a></td></tr>`).join("")}</tbody></table></div>`
        : empty(
            "Ainda não há imóveis",
            "Adicione um imóvel para registrar inspeções, coletas e tratamentos.",
          ),
      editar ? botao("+ Adicionar imóvel", "novo-imovel", "primary") : "",
    )
  );
}
