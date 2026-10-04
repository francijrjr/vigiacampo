import { api } from "./api.js";

export const consultarPainel = () => api("/painel");
export const consultarRegistro = (id) => api(`/registros/${id}`);
export const consultarBoletins = (registroId) =>
  api(`/registros/${registroId}/boletins`);

export function consultarRegistros(filtros = {}, pagina = 0, limite = 20) {
  const parametros = new URLSearchParams({
    ...filtros,
    skip: pagina * limite,
    limit: limite,
  });
  return api(`/registros/?${parametros}`);
}

export function consultarEquipe(pagina) {
  return api(`/users/?skip=${pagina * 100}&limit=100`);
}

export function consultarRelatorios(filtros) {
  const parametros = Object.fromEntries(
    Object.entries(filtros).filter(([campo]) => campo !== "status"),
  );
  return api(`/relatorios/estatisticas?${new URLSearchParams(parametros)}`);
}

export function podeEditarRegistro(registro, usuario) {
  return registro.status !== "SYNCED" || usuario.role === "SUPERVISOR";
}
