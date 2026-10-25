import { useEffect } from "react";
import { candidatesHtml } from "./candidatesHtml";
import { candidatesDetailHtml } from "./candidatesDetailHtml";
import { candidatesTemplatesHtml } from "./candidatesTemplatesHtml";
import { hydrate } from "../shell/hydrate";
import { mountCandidates } from "./selection";
import "./candidates.css";

/**
 * 候选页:主区与行详情模板原样来自原型;表格行、勾选、提交同意 1 由 selection.ts 接上。
 */
export function Candidates() {
  useEffect(() => {
    let cleanup: (() => void) | undefined;
    let cancelled = false;

    void (async () => {
      try {
        cleanup = await mountCandidates();
        if (cancelled) cleanup?.();
        else hydrate(document);
      } catch {
        // 接口不可用时保留原型里的演示行,页面不至于空掉
      }
    })();

    return () => {
      cancelled = true;
      cleanup?.();
    };
  }, []);

  return (
    <>
      <div dangerouslySetInnerHTML={{ __html: candidatesHtml }} />
      <div hidden dangerouslySetInnerHTML={{ __html: candidatesTemplatesHtml }} />
    </>
  );
}

export const candidatesDetail = candidatesDetailHtml;
