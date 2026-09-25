export const hoje = () => new Date().toLocaleDateString("en-CA");
export const dataBr = (valor) =>
  valor ? new Date(`${valor}T12:00:00`).toLocaleDateString("pt-BR") : "—";
