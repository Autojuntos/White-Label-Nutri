// Copia o rótulo preservando a formatação para colar no Google Docs.
// Usa a Clipboard API (text/html) com fallback para execCommand nos navegadores
// que ainda não a suportam — o original só tinha o execCommand (deprecated).
(function () {
  "use strict";

  const LARGURA_LUPA = 140; // px — tamanho esperado da lupa no documento final

  function ajustarLupas(raiz) {
    const originais = [];
    raiz.querySelectorAll(".imagem-lupa-copia").forEach(function (img) {
      const larguraNatural = img.naturalWidth || img.width;
      const alturaNatural = img.naturalHeight || img.height;
      const estilo = img.getAttribute("style") || "";
      let altura = alturaNatural;
      if (larguraNatural > 0) {
        altura = Math.round(LARGURA_LUPA * (alturaNatural / larguraNatural));
      }
      img.setAttribute("width", LARGURA_LUPA);
      img.setAttribute("height", altura);
      img.style.cssText = estilo + "; width: " + LARGURA_LUPA + "px; height: " + altura + "px;";
      originais.push({ img: img, estilo: estilo });
    });
    return function reverter() {
      originais.forEach(function (item) {
        item.img.removeAttribute("width");
        item.img.removeAttribute("height");
        if (item.estilo) {
          item.img.setAttribute("style", item.estilo);
        } else {
          item.img.removeAttribute("style");
        }
      });
    };
  }

  // O Google Docs ignora as classes CSS da página ao colar: só lê estilo inline e
  // atributos. Sem isso a tabela chega sem bordas, tamanhos e alinhamentos.
  const PROPRIEDADES = [
    "border-top-width", "border-top-style", "border-top-color",
    "border-right-width", "border-right-style", "border-right-color",
    "border-bottom-width", "border-bottom-style", "border-bottom-color",
    "border-left-width", "border-left-style", "border-left-color",
    "border-collapse", "padding-top", "padding-right", "padding-bottom", "padding-left",
    "font-family", "font-size", "font-weight", "color", "background-color",
    "text-align", "vertical-align", "white-space", "width",
  ];

  function comEstiloInline(original) {
    const copia = original.cloneNode(true);
    const origens = [original].concat(Array.from(original.querySelectorAll("*")));
    const destinos = [copia].concat(Array.from(copia.querySelectorAll("*")));
    origens.forEach(function (el, i) {
      const destino = destinos[i];
      const calculado = window.getComputedStyle(el);
      const partes = PROPRIEDADES.map(function (prop) {
        return prop + ": " + calculado.getPropertyValue(prop);
      });
      const proprio = el.getAttribute("style");
      destino.setAttribute("style", partes.join("; ") + (proprio ? "; " + proprio : ""));
      destino.removeAttribute("class");
      if (el.tagName === "TABLE") {
        destino.setAttribute("cellspacing", "0");
        destino.setAttribute("cellpadding", "5");
        destino.style.width = el.getBoundingClientRect().width + "px";
      }
    });
    return copia;
  }

  function copiarSelecao(elemento) {
    // Fallback: seleciona uma cópia já com estilo inline, fora da tela.
    const copia = comEstiloInline(elemento);
    copia.style.position = "fixed";
    copia.style.left = "-10000px";
    document.body.appendChild(copia);
    const range = document.createRange();
    range.selectNode(copia);
    const selecao = window.getSelection();
    selecao.removeAllRanges();
    selecao.addRange(range);
    let ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (erro) {
      ok = false;
    }
    selecao.removeAllRanges();
    copia.remove();
    return ok;
  }

  async function copiar(elemento) {
    if (navigator.clipboard && window.ClipboardItem) {
      try {
        await navigator.clipboard.write([
          new ClipboardItem({
            "text/html": new Blob([comEstiloInline(elemento).innerHTML], { type: "text/html" }),
            "text/plain": new Blob([elemento.innerText], { type: "text/plain" }),
          }),
        ]);
        return true;
      } catch (erro) {
        // cai no fallback
      }
    }
    return copiarSelecao(elemento);
  }

  document.addEventListener("DOMContentLoaded", function () {
    const botao = document.querySelector("[data-rotulo-copiar]");
    const conteudo = document.getElementById("conteudo-para-copiar");
    if (!botao || !conteudo) return;

    botao.addEventListener("click", async function () {
      const reverter = ajustarLupas(conteudo);
      const textoOriginal = botao.textContent;
      const ok = await copiar(conteudo);
      reverter();
      botao.textContent = ok ? "Copiado!" : "Falha ao copiar";
      botao.disabled = true;
      setTimeout(function () {
        botao.textContent = textoOriginal;
        botao.disabled = false;
      }, 2000);
    });
  });
})();
