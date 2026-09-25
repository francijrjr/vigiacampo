// Lucide 0.468.0 — https://lucide.dev — licença em lucide-LICENSE.txt
// SVGs locais: funcionam sem CDN e sem etapa de compilação.
const icones = {
  "layout-dashboard":
    '<rect width="7" height="9" x="3" y="3" rx="1" />\n  <rect width="7" height="5" x="14" y="3" rx="1" />\n  <rect width="7" height="9" x="14" y="12" rx="1" />\n  <rect width="7" height="5" x="3" y="16" rx="1" />',
  "clipboard-list":
    '<rect width="8" height="4" x="8" y="2" rx="1" ry="1" />\n  <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />\n  <path d="M12 11h4" />\n  <path d="M12 16h4" />\n  <path d="M8 11h.01" />\n  <path d="M8 16h.01" />',
  users:
    '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />\n  <circle cx="9" cy="7" r="4" />\n  <path d="M22 21v-2a4 4 0 0 0-3-3.87" />\n  <path d="M16 3.13a4 4 0 0 1 0 7.75" />',
  "chart-no-axes-combined":
    '<path d="M12 16v5" />\n  <path d="M16 14v7" />\n  <path d="M20 10v11" />\n  <path d="m22 3-8.646 8.646a.5.5 0 0 1-.708 0L9.354 8.354a.5.5 0 0 0-.707 0L2 15" />\n  <path d="M4 18v3" />\n  <path d="M8 14v7" />',
  settings:
    '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />\n  <circle cx="12" cy="12" r="3" />',
  house:
    '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" />\n  <path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />',
  send: '<path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z" />\n  <path d="m21.854 2.147-10.94 10.939" />',
  "file-pen-line":
    '<path d="m18 5-2.414-2.414A2 2 0 0 0 14.172 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2" />\n  <path d="M21.378 12.626a1 1 0 0 0-3.004-3.004l-4.01 4.012a2 2 0 0 0-.506.854l-.837 2.87a.5.5 0 0 0 .62.62l2.87-.837a2 2 0 0 0 .854-.506z" />\n  <path d="M8 18h1" />',
  plus: '<path d="M5 12h14" />\n  <path d="M12 5v14" />',
  "arrow-right": '<path d="M5 12h14" />\n  <path d="m12 5 7 7-7 7" />',
  "arrow-left": '<path d="m12 19-7-7 7-7" />\n  <path d="M19 12H5" />',
  "arrow-up-right": '<path d="M7 7h10v10" />\n  <path d="M7 17 17 7" />',
  download:
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />\n  <polyline points="7 10 12 15 17 10" />\n  <line x1="12" x2="12" y1="15" y2="3" />',
  "log-out":
    '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />\n  <polyline points="16 17 21 12 16 7" />\n  <line x1="21" x2="9" y1="12" y2="12" />',
  "trash-2":
    '<path d="M3 6h18" />\n  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />\n  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />\n  <line x1="10" x2="10" y1="11" y2="17" />\n  <line x1="14" x2="14" y1="11" y2="17" />',
  pencil:
    '<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" />\n  <path d="m15 5 4 4" />',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2" />\n  <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />',
  camera:
    '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />\n  <circle cx="12" cy="13" r="3" />',
  "refresh-cw":
    '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />\n  <path d="M21 3v5h-5" />\n  <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />\n  <path d="M8 16H3v5" />',
  x: '<path d="M18 6 6 18" />\n  <path d="m6 6 12 12" />',
  "clipboard-check":
    '<rect width="8" height="4" x="8" y="2" rx="1" ry="1" />\n  <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />\n  <path d="m9 14 2 2 4-4" />',
  "calendar-days":
    '<path d="M8 2v4" />\n  <path d="M16 2v4" />\n  <rect width="18" height="18" x="3" y="4" rx="2" />\n  <path d="M3 10h18" />\n  <path d="M8 14h.01" />\n  <path d="M12 14h.01" />\n  <path d="M16 14h.01" />\n  <path d="M8 18h.01" />\n  <path d="M12 18h.01" />\n  <path d="M16 18h.01" />',
  "circle-check":
    '<circle cx="12" cy="12" r="10" />\n  <path d="m9 12 2 2 4-4" />',
  "circle-dashed":
    '<path d="M10.1 2.182a10 10 0 0 1 3.8 0" />\n  <path d="M13.9 21.818a10 10 0 0 1-3.8 0" />\n  <path d="M17.609 3.721a10 10 0 0 1 2.69 2.7" />\n  <path d="M2.182 13.9a10 10 0 0 1 0-3.8" />\n  <path d="M20.279 17.609a10 10 0 0 1-2.7 2.69" />\n  <path d="M21.818 10.1a10 10 0 0 1 0 3.8" />\n  <path d="M3.721 6.391a10 10 0 0 1 2.7-2.69" />\n  <path d="M6.391 20.279a10 10 0 0 1-2.69-2.7" />',
  "map-pin":
    '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0" />\n  <circle cx="12" cy="10" r="3" />',
  wifi: '<path d="M12 20h.01" />\n  <path d="M2 8.82a15 15 0 0 1 20 0" />\n  <path d="M5 12.859a10 10 0 0 1 14 0" />\n  <path d="M8.5 16.429a5 5 0 0 1 7 0" />',
  "wifi-off":
    '<path d="M12 20h.01" />\n  <path d="M8.5 16.429a5 5 0 0 1 7 0" />\n  <path d="M5 12.859a10 10 0 0 1 5.17-2.69" />\n  <path d="M19 12.859a10 10 0 0 0-2.007-1.523" />\n  <path d="M2 8.82a15 15 0 0 1 4.177-2.643" />\n  <path d="M22 8.82a15 15 0 0 0-11.288-3.764" />\n  <path d="m2 2 20 20" />',
  "list-filter":
    '<path d="M3 6h18" />\n  <path d="M7 12h10" />\n  <path d="M10 18h4" />',
  "key-round":
    '<path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z" />\n  <circle cx="16.5" cy="7.5" r=".5" fill="currentColor" />',
};

export function icone(nome) {
  if (!icones[nome]) throw new Error(`Ícone não encontrado: ${nome}`);
  return `<svg class="lucide" data-icon="${nome}" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${icones[nome]}</svg>`;
}
