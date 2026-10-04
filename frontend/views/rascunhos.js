import { dataBr } from "../utils/datas.js";
import { escapar as e } from "./formularios.js";
import { botao } from "./componentes.js";

export function listaRascunhos(itens) {
  return `<p class="muted">Estes rascunhos ainda não foram enviados. Eles ficam neste navegador, vinculados à sua conta.</p>${itens
    .map(
      (item, i) =>
        `<div class="item-card"><div><strong>${dataBr(item.data)} · ${e(item.municipio)}</strong><p>Área ${e(item.codigo_area)}</p></div><div class="actions">${botao("Editar", `editar-fila:${i}`)}${botao("Excluir", `excluir-fila:${i}`, "danger")}</div></div>`,
    )
    .join("")}<br>${botao("Enviar registros", "sincronizar", "primary")}`;
}
