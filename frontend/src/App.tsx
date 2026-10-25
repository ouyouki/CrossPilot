import { useState } from "react";
import { Shell } from "./shell/Shell";
import { Today, todayDetail } from "./pages/Today";

type PageKey = "today" | "candidates";

/**
 * 本阶段的页面容器:只做「今日」,候选页等外壳确认后再按原型重做(见 #? 的 02-设计)。
 */
export default function App() {
  const [page, setPage] = useState<PageKey>("today");

  const detail =
    page === "today"
      ? todayDetail
      : '<h3>候选</h3><p class="muted" style="margin:0;font-size:15px">这一屏还没按原型重做。外壳确认后,下一件事就是它。</p>';

  return (
    <Shell page={page} crumb={page === "today" ? "今日" : "选品"} detailHtml={detail} onNavigate={setPage}>
      {page === "today" ? (
        <Today />
      ) : (
        <div className="card">
          <div className="card-head">
            <h2>候选页待重做</h2>
            <span className="meta">按 03-candidates.html 的标记做</span>
          </div>
          <p className="muted" style={{ margin: "0 0 0 0" }}>
            先把外壳和今日页对齐原型——你确认视觉方向之后,它们才是可以照着铺的模板。
          </p>
        </div>
      )}
    </Shell>
  );
}
