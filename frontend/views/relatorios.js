import { escapar as e } from "./formularios.js";

import { dataBr } from "../utils/datas.js";
import { empty, botao, titulo } from "./componentes.js";

export function relatorios({ dados, filtros }) {
  return (
    titulo("Relatórios", "Acompanhe os resultados dos registros enviados.") +
    `<section class="panel"><form id="filters" class="filters"><label>De<input type="date" name="data_inicio" value="${e(filtros.data_inicio)}"></label><label>Até<input type="date" name="data_fim" value="${e(filtros.data_fim)}"></label><label>Zona<input name="zona" value="${e(filtros.zona)}"></label><button class="primary">Filtrar</button>${botao("Limpar", "limpar-filtros")}</form>${dados.length ? `<div class="table-wrap"><table><thead><tr><th>Agente</th><th>Registros</th><th>Imóveis</th><th>Depósitos inspecionados</th><th>Período</th></tr></thead><tbody>${dados.map((resultado) => `<tr><td><strong>${e(resultado.agente_nome)}</strong></td><td>${resultado.total_registros}</td><td>${resultado.total_imoveis}</td><td>${resultado.total_inspecoes}</td><td>${dataBr(resultado.periodo_inicio)} a ${dataBr(resultado.periodo_fim)}</td></tr>`).join("")}</tbody></table></div>` : empty("Sem resultados no período", "Os resultados aparecem depois que os registros são enviados.")}</section><p class="muted">Para baixar o PDF de uma atividade, abra o registro e clique em “Baixar PDF”.</p>`
  );
}
