import { useState } from "react";
import { Shell } from "./shell/Shell";
import { Today, todayDetail } from "./pages/Today";
import { Candidates, candidatesDetail } from "./pages/Candidates";

type PageKey = "today" | "candidates";

/** 已按原型还原的两屏:今日、候选。其余画面各自 Issue。 */
export default function App() {
  const [page, setPage] = useState<PageKey>("today");

  return (
    <Shell
      page={page}
      crumb={page === "today" ? "今日" : "流水线 / 选品"}
      detailHtml={page === "today" ? todayDetail : candidatesDetail}
      onNavigate={setPage}
    >
      {page === "today" ? <Today /> : <Candidates />}
    </Shell>
  );
}
