/**
 * 挂载原型自带的能力:商品插画、图表、含假名的文本标 lang=ja。
 * 原型由 cp2.js 在整页加载后调用一次;这里是按需调用(Switch 页、换详情之后)。
 */

declare global {
  interface Window {
    CP?: {
      hydrateArt?: (root: ParentNode) => void;
      mountCharts?: (root: ParentNode) => void;
    };
  }
}

const KANA = /[\u3040-\u30ff\u31f0-\u31ff\uff66-\uff9f]/;

export function tagJa(scope: ParentNode): void {
  scope.querySelectorAll(".main *, .detail *").forEach((element) => {
    const closest = element.closest("[lang]");
    if (closest && closest !== document.documentElement && closest.getAttribute("lang")?.startsWith("ja")) {
      return;
    }
    if (element.children.length === 0 && KANA.test(element.textContent ?? "")) {
      element.setAttribute("lang", "ja");
    }
  });
}

export function hydrate(scope: ParentNode): void {
  window.CP?.hydrateArt?.(scope);
  window.CP?.mountCharts?.(scope);
  tagJa(scope);
}
