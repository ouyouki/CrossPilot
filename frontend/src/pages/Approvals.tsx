import { useCallback, useEffect, useState } from "react";
import { approvalsDetailHtml } from "./approvalsDetailHtml";
import { hydrate } from "../shell/hydrate";
import "./approvals.css";

type Item = { id: string; action_type: string; status: string; subject_refs: string[]; title: string; created_at: string | null };
type CostItem = { key: string; value_jpy: number | null; source: string };
type Evidence = {
  id: string;
  title?: string;
  category?: string;
  price_jpy?: number;
  status: string;
  profit?: number | null;
  margin?: string | null;
  missing?: string[];
  cost_items?: CostItem[];
};
type Detail = Item & {
  version: number;
  payload_hash: string;
  required_viewed: string[];
  viewed: string[];
  evidence: Evidence[];
};

const yen = (n: number | null | undefined) => (n === null || n === undefined ? "—" : `¥${n.toLocaleString("ja-JP")}`);
const pct = (m: string | null | undefined) => (m === null || m === undefined ? "—" : `${(Number(m) * 100).toFixed(1)}%`);

function toast(message: string) {
  document.dispatchEvent(new CustomEvent("cp:toast", { detail: message }));
}

export function Approvals() {
  const [items, setItems] = useState<Item[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/approvals");
      const body = (await response.json()) as { items: Item[] };
      setItems(body.items);
      if (body.items.length === 0) {
        setOpenId(null);
        setDetail(null);
      } else if (!body.items.some((item) => item.id === openId)) {
        setOpenId(body.items[0].id);
      }
    } catch (cause) {
      setError(String(cause));
    }
  }, [openId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!openId) return;
    void fetch(`/api/v1/approvals/${openId}`)
      .then((response) => response.json())
      .then((body: Detail) => setDetail(body))
      .catch((cause: unknown) => toast(`读不到单据:${String(cause)}`));
  }, [openId]);

  useEffect(() => {
    hydrate(document);
  }, [detail, items]);

  const view = async (section: string) => {
    if (!openId) return;
    await fetch(`/api/v1/approvals/${openId}/views`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ section }),
    });
    const refreshed = (await (await fetch(`/api/v1/approvals/${openId}`)).json()) as Detail;
    setDetail(refreshed);
  };

  const decide = async (decision: string, extra: Record<string, string> = {}) => {
    if (!detail) return;
    setBusy(true);
    try {
      const response = await fetch(`/api/v1/approvals/${detail.id}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decision,
          version: detail.version,
          payload_hash: detail.payload_hash,
          ...extra,
        }),
      });
      const body = (await response.json()) as { status?: string; detail?: string; code?: string };
      if (!response.ok) {
        toast(body.detail ?? `失败(${response.status})`);
        return;
      }
      toast(`已${decision === "APPROVE" ? "批准" : decision === "RETURN" ? "退回" : "拒绝"}:${body.status}`);
      document.dispatchEvent(new CustomEvent("cp:approvals-changed"));
      await load();
    } finally {
      setBusy(false);
    }
  };

  if (error) return <div className="card">读不到待批:{error}</div>;
  if (!items) return <div className="card">加载中…</div>;
  if (items.length === 0)
    return (
      <div className="card flush">
        <div className="tk">
          <div className="tk-head">
            <div>
              <h2>没有待批的单</h2>
              <div className="sub">去「选品」勾几个候选,提交「同意 1」,这里就会出现。</div>
            </div>
          </div>
        </div>
      </div>
    );

  const allViewed = detail ? detail.required_viewed.every((section) => detail.viewed.includes(section)) : false;

  return (
    <div>
      <div className="card flush" style={{ marginBottom: 16 }}>
        <div className="tk">
          <div className="tk-head">
            <div>
              <h2>待批 {items.length} 张</h2>
              <div className="sub">同意 1(选品)· 内存态,重启清空</div>
            </div>
            <div className="badges">
              {items.map((item) => (
                <button
                  key={item.id}
                  className={item.id === openId ? "btn sm primary" : "btn sm"}
                  onClick={() => setOpenId(item.id)}
                  type="button"
                >
                  {item.id}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {detail && (
        <div className="card flush" data-approval id={detail.id}>
          <div className="tk">
            <div className="tk-head">
              <div>
                <h2>
                  {detail.title} <span className="badge wait">{detail.status}</span>
                </h2>
                <div className="sub">
                  版本 v{detail.version} · 对象 {detail.subject_refs.length} 个 · 由人批准(Agent 无批准权)
                </div>
              </div>
            </div>

            <div className="three">
              {detail.evidence.map((card) => (
                <div className="mini" key={card.id}>
                  <div className="k">{card.title ?? card.id}</div>
                  <div className="v">
                    {yen(card.price_jpy)} · 毛利 {yen(card.profit)} · {pct(card.margin)}
                  </div>
                  <div className="n">{card.status === "COMPUTED" ? "数据齐全" : `缺:${(card.missing ?? []).join("、")}`}</div>
                </div>
              ))}
            </div>

            <div className="hr" />

            <h4>必看证据</h4>
            <div className="badges">
              {detail.required_viewed.map((section) => {
                const seen = detail.viewed.includes(section);
                return (
                  <button
                    key={section}
                    type="button"
                    className={seen ? "badge ok" : "badge wait"}
                    onClick={() => (seen ? undefined : void view(section))}
                    title={seen ? "已查看" : "点一下标记为已查看"}
                  >
                    {seen ? "✓ " : ""}
                    {section}
                  </button>
                );
              })}
            </div>

            {detail.evidence[0]?.cost_items && detail.evidence[0].cost_items.length > 0 && (
              <>
                <h4>成本分项({detail.evidence[0].title})</h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 120px 1fr", gap: "2px 12px", fontSize: 13 }}>
                  {detail.evidence[0].cost_items.map((item) => (
                    <div key={item.key} style={{ display: "contents" }}>
                      <span className="small" style={{ fontFamily: "var(--font-mono)", color: "var(--text-2)" }}>{item.key}</span>
                      <span className="num">{yen(item.value_jpy)}</span>
                      <span className="small muted">{item.source || "—"}</span>
                    </div>
                  ))}
                </div>
              </>
            )}

            <div className="row wrap" style={{ gap: 10, marginTop: 18 }}>
              <button
                type="button"
                className="btn primary"
                disabled={busy || !allViewed}
                onClick={() => void decide("APPROVE")}
                title={allViewed ? "" : "先把必看证据都看完"}
              >
                批准
              </button>
              <button
                type="button"
                className="btn"
                disabled={busy || !allViewed}
                onClick={() => void decide("RETURN", { return_reason_code: "WORDING", note: "文案需要调整" })}
              >
                退回(文案)
              </button>
              <button
                type="button"
                className="btn"
                disabled={busy || !allViewed}
                onClick={() => void decide("REJECT", { note: "不做了" })}
              >
                拒绝
              </button>
              {!allViewed && <span className="small muted">展开并确认全部必看证据后才能批</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export const approvalsDetail = approvalsDetailHtml;
