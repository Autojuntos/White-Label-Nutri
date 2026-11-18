// Cadastro de ingrediente: alterna entre g e mL.
// Em mL, mostra o campo de densidade com o asterisco de obrigatório e troca a
// unidade no rótulo da quantidade. O servidor (forms.IngredienteForm) valida a
// densidade e converte para gramas ao salvar.
(function () {
  var unidade = document.getElementById("id_unidade");
  var densidade = document.getElementById("id_densidade");
  if (!unidade || !densidade) return;
  var campoDensidade = densidade.closest("[data-campo-densidade]");
  var rotuloQtde = document.querySelector('label[for="id_qtdeDoIngrediente"]');
  var rotuloDensidade = document.querySelector('label[for="id_densidade"]');

  // Troca só o texto do rótulo (não o asterisco, que é um <span>).
  function trocarUnidadeNoRotulo(valor) {
    if (!rotuloQtde) return;
    rotuloQtde.childNodes.forEach(function (no) {
      if (no.nodeType === Node.TEXT_NODE) {
        no.nodeValue = no.nodeValue.replace(/\((g|mL)\)/, "(" + valor + ")");
      }
    });
  }

  // Mesmo asterisco do _campo.html, só que controlado pelo JS.
  function marcarObrigatorio(obrigatorio) {
    if (!rotuloDensidade) return;
    var asterisco = rotuloDensidade.querySelector(".text-danger");
    if (obrigatorio && !asterisco) {
      var span = document.createElement("span");
      span.className = "text-danger ms-1";
      span.setAttribute("aria-hidden", "true");
      span.textContent = "*";
      rotuloDensidade.appendChild(span);
    } else if (!obrigatorio && asterisco) {
      asterisco.remove();
    }
  }

  function atualizar() {
    var emMl = unidade.value === "mL";
    if (campoDensidade) campoDensidade.hidden = !emMl;
    marcarObrigatorio(emMl);
    trocarUnidadeNoRotulo(unidade.value);
  }

  unidade.addEventListener("change", atualizar);
  atualizar();
})();