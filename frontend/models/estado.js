// Estado compartilhado de navegação e da tela aberta. A sessão fica em api.js.
export const estado = {
  pagina: 0,
  filtros: {},
  renderAtual: 0,
  urlsFotos: [],
  registroAberto: null,
  imovelAberto: null,
  boletimAberto: null,
  abaVisita: "inspecoes",
  equipeAtual: [],
};
