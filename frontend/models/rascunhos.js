import { usuarioAtual } from "./api.js";

const filaChave = () => `alberio.fila.${usuarioAtual()?.id}`;
export const fila = () => JSON.parse(localStorage.getItem(filaChave()) || "[]");
export const guardarFila = (registros) =>
  localStorage.setItem(filaChave(), JSON.stringify(registros));
