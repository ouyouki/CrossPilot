import { useState } from "react";
import { Shell } from "./shell/Shell";
import { Today, todayDetail } from "./pages/Today";
import { Candidates, candidatesDetail } from "./pages/Candidates";
import { Approvals, approvalsDetail } from "./pages/Approvals";

type PageKey = "today" | "candidates" | "approvals";

const CRUMB: Record<PageKey, string> = {
  today: "今日",
  candidates: "流水线 / 选品",
  approvals: "治理 / 待批",
};

const DETAIL: Record<PageKey, string> = {
  today: todayDetail,
  candidates: candidatesDetail,
  approvals: approvalsDetail,
};

/** 已按原型还原的画面;其余各自 Issue。 */
export default function App() {
  const [page, setPage] = useState<PageKey>("today");

  return (
    <Shell page={page} crumb={CRUMB[page]} detailHtml={DETAIL[page]} onNavigate={setPage}>
      {page === "today" ? <Today /> : page === "candidates" ? <Candidates /> : <Approvals />}
    </Shell>
  );
}
