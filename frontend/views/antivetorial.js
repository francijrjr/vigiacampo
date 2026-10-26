import { escapar as e } from "./formularios.js";
import { botao, titulo } from "./componentes.js";
import { legendaDepositos } from "./legenda-depositos.js";

const depositos = ["a1", "a2", "b", "c", "d1", "d2", "e"];
const campos = [
  ["codigo_localidade", "Código e nome da localidade"],
  ["categoria_localidade", "Categoria / localidade"],
  ["zona", "Zona"],
  ["conclusao", "Conclusão"],
  ["atividade", "Atividade"],
  ["agente", "Agente"],
  ["supervisor", "Supervisor"],
  ["data_entrada", "Data de entrada", "date"],
  ["data_conclusao", "Data da conclusão", "date"],
  ["laboratorio", "Laboratório"],
  ["laboratorista", "Laboratorista"],
];

function input(nome, valor, tipo = "text") {
  return `<input name="${nome}" type="${tipo}" value="${e(valor || "")}">`;
}

function linha(ordem, dados = {}) {
  const celula = (nome, valor = "", tipo = "text") =>
    `<td>${input(`linha-${ordem}-${nome}`, valor, tipo)}</td>`;
  return `<tr><th scope="row">${ordem}</th>${celula("quarteirao", dados.quarteirao)}${celula("lado", dados.lado)}${celula("logradouro", dados.logradouro)}${celula("numero", dados.numero)}${celula("tipo_imovel", dados.tipo_imovel)}${celula("visita", dados.visita)}${depositos.map((nome) => celula(nome, dados[nome] || 0, "number")).join("")}<td><input aria-label="Foco na linha ${ordem}" name="linha-${ordem}-foco" type="checkbox" ${dados.foco ? "checked" : ""}></td>${celula("tratamento", dados.tratamento)}</tr>`;
}

export function fichaAntivetorial({ registro, dados = {}, editar }) {
  const linhas = Object.fromEntries((dados.linhas || []).map((item) => [item.ordem, item]));
  const valores = { atividade: "Pesquisa entomológica / tratamento", agente: registro.agente_nome, ...dados };
  return `<a class="subtle-link" href="#registro/${registro.id}">← Voltar ao registro</a><br><br>${titulo("Registro diário do serviço antivetorial", `Registro de ${registro.municipio} em ${registro.data}`, editar ? `${botao("Baixar PDF ↓", "pdf-antivetorial", "secondary")}` : botao("Baixar PDF ↓", "pdf-antivetorial", "secondary"))}
  <form id="antivetorial-form" class="antivetorial-form" data-editavel="${editar}">
    <section class="panel antivetorial-sheet"><div class="antivetorial-header"><p>Prefeitura Municipal de ${e(registro.municipio)}</p><strong>REGISTRO DIÁRIO DO SERVIÇO ANTIVETORIAL</strong></div>
    <div class="form-grid antivetorial-cabecalho">${campos.map(([nome, rotulo, tipo]) => `<label>${e(rotulo)}${input(nome, valores[nome], tipo)}</label>`).join("")}</div>
    ${legendaDepositos()}
    <div class="table-wrap antivetorial-table"><table><thead><tr><th>Nº</th><th>Quart. nº</th><th>Lado</th><th>Logradouro</th><th>Nº</th><th>Tipo</th><th>Visita</th>${depositos.map((nome) => `<th>${nome.toUpperCase()}</th>`).join("")}<th>Foco</th><th>Tratamento</th></tr></thead><tbody>${Array.from({ length: 20 }, (_, index) => linha(index + 1, linhas[index + 1])).join("")}</tbody></table></div>
    <label class="wide">Observações<textarea name="observacoes" rows="3">${e(valores.observacoes || "")}</textarea></label>
    ${editar ? `<footer><button class="primary" type="submit">Salvar ficha</button></footer>` : ""}</section></form>`;
}

export function lerFichaAntivetorial(form) {
  const dados = Object.fromEntries(new FormData(form));
  const linhas = [];
  for (let ordem = 1; ordem <= 20; ordem += 1) {
    const prefixo = `linha-${ordem}-`;
    const linha = { ordem, foco: form.elements[`${prefixo}foco`].checked };
    let preenchida = linha.foco;
    for (const nome of ["quarteirao", "lado", "logradouro", "numero", "tipo_imovel", "visita", "tratamento"]) {
      const valor = dados[`${prefixo}${nome}`]?.trim();
      if (valor) { linha[nome] = valor; preenchida = true; }
    }
    for (const nome of depositos) {
      const valor = Number(dados[`${prefixo}${nome}`] || 0);
      linha[nome] = valor;
      if (valor) preenchida = true;
    }
    if (preenchida) linhas.push(linha);
    for (const nome of [...depositos, "quarteirao", "lado", "logradouro", "numero", "tipo_imovel", "visita", "tratamento", "foco"])
      delete dados[`${prefixo}${nome}`];
  }
  for (const [nome, valor] of Object.entries(dados)) if (!valor) dados[nome] = null;
  return { ...dados, linhas };
}
