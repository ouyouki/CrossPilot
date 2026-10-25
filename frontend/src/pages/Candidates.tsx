import { useEffect } from "react";
import { candidatesHtml } from "./candidatesHtml";
import { candidatesDetailHtml } from "./candidatesDetailHtml";
import { candidatesTemplatesHtml } from "./candidatesTemplatesHtml";
import { hydrate } from "../shell/hydrate";
import "./candidates.css";

/**
 * 候选页:主区与行详情模板都原样来自原型(见各自 .ts 的说明)。
 * 点行切换右栏的行为照 cp2.js:见 shell/Shell.tsx 的 [data-detail] 分支。
 */
export function Candidates() {
  useEffect(() => {
    hydrate(document);
  }, []);

  return (
    <>
      <div dangerouslySetInnerHTML={{ __html: candidatesHtml }} />
      {/* 行详情模板:原样输出,平时不可见,点行时按 id 取内容 */}
      <div hidden dangerouslySetInnerHTML={{ __html: candidatesTemplatesHtml }} />
    </>
  );
}

export const candidatesDetail = candidatesDetailHtml;
