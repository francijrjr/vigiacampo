import { escapar as e } from "./formularios.js";
import { icone } from "./icones.js";
import { botao, empty, painel, titulo } from "./componentes.js";
import { CATALOGO_MODULOS, barraRetornoModulos } from "./modulos.js";

export const categoriasTerritorio = {
  Urbana: "Urbana",
  Rural: "Rural",
};

export const camposTerritorio = [
  ["municipio", "Município", "text"],
  ["distrito", "Distrito / CRES", "optional"],
  ["codigo_localidade", "Código da localidade", "optional"],
  ["localidade", "Localidade / bairro", "text"],
  ["categoria", "Categoria", "select", categoriasTerritorio],
  ["zona", "Zona / setor", "optional"],
  ["quarteirao_numero", "Quarteirão nº", "text"],
  ["lados", "Quantidade de lados", "number"],
  ["logradouros", "Ruas / logradouros da quadra", "logradouros"],
  ["residenciais", "Imóveis residenciais (R)", "number"],
  ["comerciais", "Imóveis comerciais (C)", "number"],
  ["terrenos_baldios", "Terrenos baldios (TB)", "number"],
  ["pontos_estrategicos", "Pontos estratégicos (PE)", "number"],
  ["outros", "Outros imóveis (O)", "number"],
  ["observacoes", "Referências e limites do quarteirão", "textarea"],
];

export function visualizacaoTerritorio(item) {
  const ruas = String(item.logradouros || "")
    .split(/[;\n]+/)
    .map((rua) => rua.trim())
    .filter(Boolean);
  const temMapa = Boolean(item.geometria);
  const total = item.total_imoveis ?? 0;
  return `<article class="territorio-visualizacao">
    <div class="territorio-visualizacao-topo">
      <div>
        <span class="territorio-visualizacao-label">Base territorial</span>
        <h3>QT ${e(item.quarteirao_numero)} · ${e(item.localidade)}</h3>
        <p>${e(item.municipio)} · ${e(item.categoria)}${item.zona ? ` · ${e(item.zona)}` : ""}</p>
      </div>
      <span class="badge ${temMapa ? "SYNCED" : "DRAFT"}">${icone(temMapa ? "map-pin" : "circle-dashed")} ${temMapa ? "Croqui disponível" : "Sem croqui"}</span>
    </div>
    <section class="territorio-resumo" aria-label="Resumo de imóveis">
      <div><strong>${total}</strong><span>imóveis</span></div>
      <div><strong>${item.residenciais}</strong><span>residenciais</span></div>
      <div><strong>${item.comerciais}</strong><span>comerciais</span></div>
      <div><strong>${item.terrenos_baldios}</strong><span>terrenos baldios</span></div>
      <div><strong>${item.pontos_estrategicos}</strong><span>pontos estratégicos</span></div>
      <div><strong>${item.outros}</strong><span>outros</span></div>
    </section>
    <div class="territorio-ficha-grid">
      <section class="territorio-ficha-bloco">
        <span>Identificação</span>
        <dl><div><dt>Distrito / CRES</dt><dd>${e(item.distrito || "Não informado")}</dd></div><div><dt>Lados</dt><dd>${e(item.lados)} lados</dd></div>${item.codigo_localidade ? `<div><dt>Código da localidade</dt><dd>${e(item.codigo_localidade)}</dd></div>` : ""}</dl>
      </section>
      <section class="territorio-ficha-bloco">
        <span>Ruas e logradouros</span>
        ${ruas.length ? `<ul class="territorio-ruas">${ruas.map((rua) => `<li>${e(rua)}</li>`).join("")}</ul>` : '<p class="muted">Nenhuma rua informada.</p>'}
      </section>
    </div>
    ${item.observacoes ? `<section class="territorio-observacoes"><span>Referências e limites</span><p>${e(item.observacoes)}</p></section>` : ""}
    ${temMapa ? '<section class="territorio-mapa-visualizacao"><div><span>Croqui do quarteirão</span><small>Representação cadastrada para consulta.</small></div><div class="territorio-mapa-canvas" aria-label="Mapa do quarteirão"></div></section>' : ""}
    <footer><button type="button" class="secondary" data-fechar-visualizacao>Fechar</button></footer>
  </article>`;
}

function tabelaTerritorio(itens, supervisor) {
  if (!itens.length) {
    return empty(
      "Nenhum quarteirão cadastrado",
      "Cadastre localidades e quarteirões para estruturar o Reconhecimento Geográfico do município.",
      botao("+ Cadastrar quarteirão", "novo-territorio", "primary"),
    );
  }
  return `<div class="table-wrap territorio-table-wrap"><table class="territorio-tabela"><thead><tr><th>Localidade / categoria</th><th>Zona / distrito</th><th>Quarteirão</th><th>Imóveis (R · C · TB · PE · O)</th><th>Mapa</th><th></th></tr></thead><tbody>${itens
    .map((item) => {
      const temMapa = Boolean(item.geometria);
      return `<tr>
        <td data-label="Localidade / categoria">
          <strong>${e(item.localidade)}</strong>
          <small>${e(item.municipio)} · ${e(item.categoria)}${item.codigo_localidade ? ` · Cód. ${e(item.codigo_localidade)}` : ""}</small>
        </td>
        <td data-label="Zona / distrito">
          <strong>${e(item.zona || "Zona geral")}</strong>
          <small>${e(item.distrito || "20ª CRES")}</small>
        </td>
        <td data-label="Quarteirão">
          <strong>QT ${e(item.quarteirao_numero)}</strong>
          <small>${e(item.lados)} lados${item.logradouros ? ` · ${e(item.logradouros)}` : ""}</small>
        </td>
        <td data-label="Imóveis">
          <strong>${item.total_imoveis} imóveis</strong>
          <small>R:${item.residenciais} · C:${item.comerciais} · TB:${item.terrenos_baldios} · PE:${item.pontos_estrategicos} · O:${item.outros}</small>
        </td>
        <td data-label="Mapa">
          <span class="badge ${temMapa ? "SYNCED" : "DRAFT"}">${icone(temMapa ? "map-pin" : "circle-dashed")} ${temMapa ? "Mapeado" : "Sem croqui"}</span>
        </td>
        <td data-label="Ações">
          <div class="actions">
            ${botao("Ver", `ver-territorio:${item.id}`)}
            ${botao("Editar", `editar-territorio:${item.id}`)}
            ${supervisor ? botao("Excluir", `excluir-territorio:${item.id}`, "danger") : ""}
          </div>
        </td>
      </tr>`;
    })
    .join("")}</tbody></table></div>`;
}

function registrosDoDia(registros) {
  if (!registros.length)
    return empty(
      "Comece pelo registro diário",
      "Crie o registro de hoje para iniciar o reconhecimento em campo.",
      botao("+ Criar registro diário", "novo-registro", "primary"),
    );
  return `<div class="reconhecimento-registros-lista">${registros.map((registro) => `<a href="#registro/${registro.id}" class="reconhecimento-registro">
    <span class="reconhecimento-registro-data">${new Date(`${registro.data}T12:00:00`).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}</span>
    <span class="reconhecimento-registro-copy"><strong>${e(registro.municipio)}</strong><small>${e(registro.zona || "Sem zona definida")} · ${e(registro.atividade)}</small></span>
    <span class="badge ${e(registro.status)}">${e(registro.status === "SYNCED" ? "Enviado" : registro.status === "DRAFT" ? "Rascunho" : "Pendente")}</span>
    ${icone("arrow-right")}
  </a>`).join("")}</div>`;
}

export function telaReconhecimento({ resumo, itens, filtros, usuario, registros }) {
  const supervisor = usuario.role === "SUPERVISOR";
  const moduloInfo = CATALOGO_MODULOS.find((m) => m.id === "reconhecimento");

  return (
    barraRetornoModulos(moduloInfo, usuario) +
    titulo(
      "Reconhecimento Geográfico",
      "O registro diário organiza o trabalho antes do mapeamento de quarteirões.",
      `<div class="actions">${botao("+ Novo registro diário", "novo-registro", "primary")}</div>`,
    ) +
    `<section class="reconhecimento-etapa" aria-label="Primeira etapa: registro diário">
      <div class="reconhecimento-etapa-cabecalho"><div><span class="reconhecimento-etapa-numero">1</span><div><h2>Registro diário</h2><p>Inicie por aqui e acompanhe os registros recentes da equipe.</p></div></div>${botao("Ver registros", "ir-registros", "secondary")}</div>
      ${registrosDoDia(registros)}
    </section>` +
    `<p class="territorio-intro">${icone("map-pin")} <strong>2. Reconhecimento geográfico</strong><span>Cadastre e mapeie os quarteirões vinculados ao trabalho de campo.</span></p>` +
    `<div class="metrics">${[
      [
        "Localidades",
        resumo.total_localidades ?? 0,
        "Bairros e localidades ativas",
        "map-pin",
      ],
      [
        "Quarteirões cadastrados",
        resumo.total_quarteiroes ?? 0,
        "Cadastro territorial",
        "clipboard-list",
      ],
      [
        "Quarteirões mapeados",
        resumo.total_mapeados ?? 0,
        "Com polígono GeoJSON salvo",
        "clipboard-check",
      ],
      [
        "Imóveis estruturais",
        resumo.total_imoveis ?? 0,
        "Soma de R, C, TB, PE e Outros",
        "house",
      ],
    ]
      .map(
        ([label, valor, ajuda, nomeIcone]) =>
          `<article class="metric"><div class="metric-header">${label}<span class="metric-icon">${icone(nomeIcone)}</span></div><strong>${valor}</strong><small>${ajuda}</small></article>`,
      )
      .join("")}</div>` +
    `<section class="panel territorio-panel">
      <div class="panel-heading">
        <div>
          <h2>Base territorial</h2>
          <p>Quarteirões compartilhados com a equipe do município.</p>
        </div>
        ${botao("+ Adicionar quarteirão", "novo-territorio", "secondary")}
      </div>
      <form id="territorio-filters" class="filters">
        <label>Localidade / bairro<input name="localidade" value="${e(filtros.localidade)}" placeholder="Todas as localidades"></label>
        <label>Zona / setor<input name="zona" value="${e(filtros.zona)}" placeholder="Todas as zonas"></label>
        <label>Categoria<select name="categoria"><option value="">Todas</option>${Object.entries(
          categoriasTerritorio,
        )
          .map(
            ([k, v]) =>
              `<option value="${k}" ${filtros.categoria === k ? "selected" : ""}>${v}</option>`,
          )
          .join("")}</select></label>
        <button class="primary" type="submit">Filtrar</button>
        ${botao("Limpar", "limpar-filtros-territorio")}
      </form>
      ${tabelaTerritorio(itens, supervisor)}
    </section>`
  );
}
