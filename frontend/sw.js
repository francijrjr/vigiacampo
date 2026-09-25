// Só arquivos públicos da interface entram no cache. Respostas da API nunca são armazenadas.
const CACHE = "alberio-interface-v5";
const ASSETS = [
  "/",
  "/static/styles.css",
  "/static/icons-and-card.css",
  "/static/boletim.css",
  "/static/app.js",
  "/static/controllers/acoes.js",
  "/static/controllers/aplicacao.js",
  "/static/controllers/boletins-acoes.js",
  "/static/controllers/equipe-acoes.js",
  "/static/controllers/navegacao-acoes.js",
  "/static/controllers/rascunhos-acoes.js",
  "/static/controllers/registros-acoes.js",
  "/static/controllers/sessao-acoes.js",
  "/static/controllers/telas.js",
  "/static/controllers/visitas-acoes.js",
  "/static/models/api.js",
  "/static/models/consultas.js",
  "/static/models/estado.js",
  "/static/models/rascunhos.js",
  "/static/utils/datas.js",
  "/static/utils/download.js",
  "/static/views/boletim.js",
  "/static/views/componentes.js",
  "/static/views/conta.js",
  "/static/views/equipe.js",
  "/static/views/formularios.js",
  "/static/views/fotos.js",
  "/static/views/icones.js",
  "/static/views/inicio.js",
  "/static/views/interface.js",
  "/static/views/layout.js",
  "/static/views/rascunhos.js",
  "/static/views/registros.js",
  "/static/views/relatorios.js",
  "/static/views/visita.js",
];
self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
});
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter(
              (key) => key.startsWith("alberio-interface-") && key !== CACHE,
            )
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (
    event.request.method !== "GET" ||
    url.origin !== self.location.origin ||
    !ASSETS.includes(url.pathname)
  )
    return;
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request)),
  );
});
