import { useEffect, useState } from "react";
import { getJson } from "../api";

type ReadinessItem = { key: string; label: string; ok: boolean; fix: string };
type TodayPayload = {
  pending_approvals: number;
  readiness: { items: ReadinessItem[]; missing: string[] };
  reminders: { text: string; url: string }[];
};

export function Today() {
  const [data, setData] = useState<TodayPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJson<TodayPayload>("/api/v1/today")
      .then(setData)
      .catch((e: unknown) => setError(String(e)));
  }, []);

  if (error) return <div className="empty">读不到今日数据：{error}</div>;
  if (!data) return <div className="empty">加载中…</div>;

  return (
    <section>
      <h1>今天</h1>
      <div className="cards">
        <div className="card">
          <div className="card-label">待批</div>
          <div className="card-value">{data.pending_approvals}</div>
          <div className="card-note">同意 1 / 同意 2 的待决单</div>
        </div>
        <div className="card">
          <div className="card-label">开工前置</div>
          <div className="card-value">
            {data.readiness.items.filter((i) => i.ok).length}/{data.readiness.items.length}
          </div>
          <div className="card-note">缺：{data.readiness.missing.join("、") || "无"}</div>
        </div>
        <div className="card">
          <div className="card-label">提醒</div>
          <div className="card-value">{data.reminders.length}</div>
          <div className="card-note">一条提醒 + 一个跳转</div>
        </div>
      </div>

      <h2>开工前置清单</h2>
      <ul className="checklist">
        {data.readiness.items.map((item) => (
          <li key={item.key} className={item.ok ? "ok" : "todo"}>
            <span className="dot" />
            <span className="label">{item.label}</span>
            <span className="fix">{item.ok ? "就绪" : item.fix}</span>
          </li>
        ))}
      </ul>

      <h2>提醒</h2>
      {data.reminders.length === 0 ? (
        <div className="empty">本期没有提醒。</div>
      ) : (
        <ul className="reminders">
          {data.reminders.map((r) => (
            <li key={r.url}>
              {r.text} <a href={r.url}>去处理</a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
