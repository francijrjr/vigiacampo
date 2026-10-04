import { estado } from "../models/estado.js";

export function criarAcoesNavegacao({ render }) {
  async function executarRecarregar() {
    return render();
  }

  async function executarAnterior() {
    estado.pagina--;
    return render();
  }

  async function executarProxima() {
    estado.pagina++;
    return render();
  }

  async function executarLimparFiltros() {
    estado.filtros = {};
    estado.pagina = 0;
    return render();
  }

  return {
    recarregar: executarRecarregar,
    anterior: executarAnterior,
    proxima: executarProxima,
    "limpar-filtros": executarLimparFiltros,
  };
}
