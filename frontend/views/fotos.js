export function formularioFoto() {
  return `<form id="photo-form"><label>Foto (JPEG, PNG ou WebP, até 10 MB)<input name="file" type="file" accept="image/jpeg,image/png,image/webp" required></label><label>Descrição<input name="descricao" maxlength="500"></label><p class="form-error" role="alert"></p><footer><button class="primary">Enviar foto</button></footer></form>`;
}
