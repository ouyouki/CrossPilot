import { useEffect } from "react";
import { todayHtml } from "./todayHtml";
import { todayDetailHtml } from "./todayDetailHtml";
// 页面级样式(原型的 <style> 块),必须在 cp2.css 之后生效。
import "./today.css";

declare global {
  interface Window {
    CP?: {
      hydrateArt?: (root: ParentNode) => void;
      mountCharts?: (root: ParentNode) => void;
      tagJa?: (root: ParentNode) => void;
    };
  }
}

const KANA = /[\u3040-\u30ff\u31f0-\u31ff\uff66-\uff9f]/;

function tagJa(scope: ParentNode) {
  scope.querySelectorAll(".main *, .detail *").forEach((element) => {
    const closest = element.closest("[lang]");
    if (closest && closest !== document.documentElement && closest.getAttribute("lang")?.startsWith("ja")) return;
    if (element.children.length === 0 && KANA.test(element.textContent ?? "")) {
      element.setAttribute("lang", "ja");
    }
  });
}

/**
 * 今日页:标记原样来自原型(见 todayHtml.ts 的说明)。
 * 这里只负责挂载原型自己的插画与图表脚本,以及含假名的文本标 lang=ja。
 */
export function Today() {
  useEffect(() => {
    window.CP?.hydrateArt?.(document);
    window.CP?.mountCharts?.(document);
    tagJa(document);
  }, []);

  return <div dangerouslySetInnerHTML={{ __html: todayHtml }} />;
}

export const todayDetail = todayDetailHtml;
