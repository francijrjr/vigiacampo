import { categoriasDepositos, escapar as e } from "./formularios.js";

export function legendaDepositos() {
  return `<aside class="depositos-legenda" aria-label="Legenda dos tipos de depósitos"><div><strong>Tipos de depósitos</strong><p>Use esta referência ao registrar as inspeções.</p></div><dl>${Object.entries(categoriasDepositos).map(([codigo, [nome, exemplo]]) => `<div><dt>${e(codigo)}</dt><dd><strong>${e(nome)}</strong><span>${e(exemplo)}</span></dd></div>`).join("")}</dl></aside>`;
}
