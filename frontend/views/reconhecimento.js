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
  ["logradouros", "Ruas / logradouros da quadra", "optional"],
  ["residenciais", "Imóveis residenciais (R)", "number"],
  ["comerciais", "Imóveis comerciais (C)", "number"],
  ["terrenos_baldios", "Terrenos baldios (TB)", "number"],
  ["pontos_estrategicos", "Pontos estratégicos (PE)", "number"],
  ["outros", "Outros imóveis (O)", "number"],
  ["observacoes", "Referências e limites do quarteirão", "textarea"],
];

function tabelaTerritorio(itens, supervisor) {
  if (!itens.length) {
    return empty(
      "Nenhum quarteirão permanente cadastrado",
      "Cadastre localidades e quarteirões permanentes para estruturar o Reconhecimento Geográfico do município.",
      botao("+ Cadastrar quarteirão permanente", "novo-territorio", "primary"),
    );
  }
  return `<div class="table-wrap"><table><thead><tr><th>Localidade / categoria</th><th>Zona / distrito</th><th>Quarteirão</th><th>Imóveis (R · C · TB · PE · O)</th><th>Mapa</th><th></th></tr></thead><tbody>${itens
    .map((item) => {
      const temMapa = Boolean(item.geometria);
      return `<tr>
        <td>
          <strong>${e(item.localidade)}</strong>
          <small>${e(item.municipio)} · ${e(item.categoria)}${item.codigo_localidade ? ` · Cód. ${e(item.codigo_localidade)}` : ""}</small>
        </td>
        <td>
          <strong>${e(item.zona || "Zona geral")}</strong>
          <small>${e(item.distrito || "20ª CRES")}</small>
        </td>
        <td>
          <strong>QT ${e(item.quarteirao_numero)}</strong>
          <small>${e(item.lados)} lados${item.logradouros ? ` · ${e(item.logradouros)}` : ""}</small>
        </td>
        <td>
          <strong>${item.total_imoveis} imóveis</strong>
          <small>R:${item.residenciais} · C:${item.comerciais} · TB:${item.terrenos_baldios} · PE:${item.pontos_estrategicos} · O:${item.outros}</small>
        </td>
        <td>
          <span class="badge ${temMapa ? "SYNCED" : "DRAFT"}">${icone(temMapa ? "map-pin" : "circle-dashed")} ${temMapa ? "Mapeado" : "Sem croqui"}</span>
        </td>
        <td>
          <div class="actions">
            ${botao("Editar", `editar-territorio:${item.id}`)}
            ${supervisor ? botao("Excluir", `excluir-territorio:${item.id}`, "danger") : ""}
          </div>
        </td>
      </tr>`;
    })
    .join("")}</tbody></table></div>`;
}

export function telaReconhecimento({ resumo, itens, filtros, usuario }) {
  const supervisor = usuario.role === "SUPERVISOR";
  const moduloInfo = CATALOGO_MODULOS.find((m) => m.id === "reconhecimento");

  return (
    barraRetornoModulos(moduloInfo, usuario) +
    titulo(
      "Reconhecimento Geográfico",
      "Cadastro territorial permanente de localidades, quarteirões georreferenciados e estrutura de imóveis.",
      `<div class="actions">${botao("+ Novo quarteirão permanente", "novo-territorio", "primary")}</div>`,
    ) +
    `<section class="territorio-permissoes-card" aria-label="Controle de acesso do módulo">
      <div>
        <span class="eyebrow">${icone("map-pin")} Controle de acesso · ${supervisor ? "Perfil Supervisor" : "Perfil Agente de Campo"}</span>
        <h2>${supervisor ? "Gestão completa da base territorial permanente" : "Consulta e atualização territorial em campo"}</h2>
        <p>${
          supervisor
            ? "Como supervisor, você pode cadastrar, editar, revisar contornos geográficos no mapa e excluir registros territoriais permanentes de toda a equipe."
            : "Como agente de campo, você pode consultar a base territorial do município, cadastrar novos quarteirões permanentes e atualizar a estrutura de imóveis e contornos no mapa. A exclusão permanente é exclusiva do supervisor."
        }</p>
      </div>
      <div class="territorio-permissoes-acoes">
        ${botao("+ Cadastrar quarteirão", "novo-territorio", "primary")}
      </div>
    </section>` +
    `<div class="metrics">${[
      [
        "Localidades permanentes",
        resumo.total_localidades ?? 0,
        "Bairros e localidades ativas",
        "map-pin",
      ],
      [
        "Quarteirões cadastrados",
        resumo.total_quarteiroes ?? 0,
        "Cadastro territorial permanente",
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
    `<section class="panel">
      <div class="panel-heading">
        <div>
          <h2>Base territorial permanente</h2>
          <p>Quarteirões permanentes compartilhados com a equipe do município.</p>
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
