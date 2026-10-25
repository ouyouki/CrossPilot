import { useEffect, useState } from "react";
import { getJson } from "../api";

type CostItem = { key: string; value_jpy: number | null; source: string; status: string; severity: string };
type Row = {
  id: string;
  title: string;
  category: string;
  price_jpy: number;
  status: string;
  revenue: number | null;
  profit: number | null;
  margin: string | null;
  missing: string[];
  cost_items: CostItem[];
};

const yen = (n: number | null) => (n === null ? "—" : `¥${n.toLocaleString("ja-JP")}`);
const pct = (m: string | null) => (m === null ? "—" : `${(Number(m) * 100).toFixed(1)}%`);

export function Candidates() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [notes, setNotes] = useState<string[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJson<{ items: Row[]; notes?: string[] }>("/api/v1/candidates")
      .then((d) => {
        setRows(d.items);
        setNotes(d.notes ?? []);
      })
      .catch((e: unknown) => setError(String(e)));
  }, []);

  if (error) return <div className="empty">读不到候选数据：{error}</div>;
  if (!rows) return <div className="empty">加载中…</div>;
  if (rows.length === 0)
    return <div className="empty">{notes[0] ?? "还没有候选。"}</div>;

  return (
    <section>
      <h1>候选</h1>
      <p className="hint">点一行展开 16 项成本。数字来自 costing.compute，页面不算第二遍。</p>
      <table className="grid">
        <thead>
          <tr>
            <th>商品</th>
            <th>类目</th>
            <th className="num">售价</th>
            <th className="num">毛利</th>
            <th className="num">利润率</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <>
              <tr key={row.id} onClick={() => setOpen(open === row.id ? null : row.id)} className="row">
                <td>{row.title}</td>
                <td>{row.category}</td>
                <td className="num">{yen(row.price_jpy)}</td>
                <td className="num">{yen(row.profit)}</td>
                <td className="num">{pct(row.margin)}</td>
                <td>
                  <span className={row.status === "COMPUTED" ? "pill ok" : "pill block"}>
                    {row.status === "COMPUTED" ? "可算" : "缺数据"}
                  </span>
                </td>
              </tr>
              {open === row.id && (
                <tr key={`${row.id}-detail`} className="detail">
                  <td colSpan={6}>
                    {row.status === "COMPUTED" ? (
                      <div className="costs">
                        {row.cost_items.map((item) => (
                          <div key={item.key} className="cost">
                            <span className="ck">{item.key}</span>
                            <span className="cv">{yen(item.value_jpy)}</span>
                            <span className="cs">{item.source || "—"}</span>
                          </div>
                        ))}
                        <div className="cost total">
                          <span className="ck">合计成本</span>
                          <span className="cv">{yen(row.cost_items.reduce((s, i) => s + (i.value_jpy ?? 0), 0))}</span>
                          <span className="cs">营收 {yen(row.revenue)}</span>
                        </div>
                      </div>
                    ) : (
                      <div className="empty">缺：{row.missing.join("、")}（补齐前不给金额）</div>
                    )}
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </section>
  );
}
