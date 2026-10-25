import { useEffect } from "react";
import { todayHtml } from "./todayHtml";
import { todayDetailHtml } from "./todayDetailHtml";
import { hydrate } from "../shell/hydrate";
// 页面级样式(原型的 <style> 块),必须在 cp2.css 之后生效。
import "./today.css";

/** 今日页:标记原样来自原型(见 todayHtml.ts 的说明)。 */
export function Today() {
  useEffect(() => {
    hydrate(document);
  }, []);

  return <div dangerouslySetInnerHTML={{ __html: todayHtml }} />;
}

export const todayDetail = todayDetailHtml;
