/**
 * 候选页的「活」部分:把表格行换成接口数据、勾选上限、提交同意 1。
 * 原型的标记与样式照用,这里只做数据与交互(02-设计 §2)。
 */

type Row = {
  id: string;
  title: string;
  category: string;
  price_jpy: number;
  status: string;
  profit: number | null;
  margin: string | null;
  missing: string[];
};

export const SELECTION_CAP = 10;

const yen = (n: number | null) => (n === null ? "—" : `¥${n.toLocaleString("ja-JP")}`);
const pct = (m: string | null) => (m === null ? "—" : `${(Number(m) * 100).toFixed(1)}%`);
const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function toast(message: string) {
  document.dispatchEvent(new CustomEvent("cp:toast", { detail: message }));
}

function rowHtml(row: Row): string {
  const ok = row.status === "COMPUTED";
  const reason = ok
    ? `毛利 ${pct(row.margin)} · 类目 ${esc(row.category)}`
    : `缺:${row.missing.map(esc).join("、")}`;
  return `
    <tr data-detail="d-gen" data-candidate="${esc(row.id)}">
      <td><input type="checkbox" data-pick="1" ${ok ? "" : "disabled"} aria-label="选择 ${esc(row.title)}"></td>
      <td>
        <div class="prod">
          <span class="thumb" data-art="box"></span>
          <div>
            <div class="t"><a href="#" lang="ja">${esc(row.title)}</a></div>
            <div class="s">${ok ? esc(row.category) : "数据不全,补完才能选"}</div>
          </div>
        </div>
      </td>
      <td class="num">${yen(row.price_jpy)}</td>
      <td class="num">${yen(row.profit)}<br><span class="small muted">${pct(row.margin)}</span></td>
      <td class="num">—</td>
      <td class="small">样例</td>
      <td class="num">—</td>
      <td class="small">${reason}</td>
    </tr>`;
}

export async function mountCandidates(): Promise<() => void> {
  const table = document.querySelector(".main .tbl tbody") as HTMLElement | null;
  if (!table) return () => {};
  const original = table.innerHTML;

  const response = await fetch("/api/v1/candidates");
  const data = (await response.json()) as { items: Row[] };
  table.innerHTML = data.items.map(rowHtml).join("");

  // 提交按钮:放进卡片头部的工具区
  const tools = document.querySelector(".main .card-head .tools");
  const button = document.createElement("button");
  button.className = "btn primary sm";
  button.type = "button";
  button.textContent = "提交同意 1(0)";
  button.disabled = true;
  button.dataset.submitSelection = "1";
  tools?.prepend(button);

  const picks = () => Array.from(table.querySelectorAll<HTMLInputElement>("input[data-pick]:checked"));
  const refresh = () => {
    const n = picks().length;
    button.textContent = `提交同意 1(${n})`;
    button.disabled = n === 0;
  };

  const onChange = (event: Event) => {
    const input = event.target as HTMLInputElement;
    if (!input.matches("input[data-pick]")) return;
    if (picks().length > SELECTION_CAP) {
      input.checked = false;
      toast(`单批最多勾选 ${SELECTION_CAP} 个`);
    }
    refresh();
  };

  const onClick = async (event: Event) => {
    const target = event.target as HTMLElement;
    if (!target.closest("[data-submit-selection]")) return;
    const ids = picks()
      .map((input) => input.closest("tr")?.dataset.candidate ?? "")
      .filter(Boolean);
    if (ids.length === 0) return;
    button.disabled = true;
    try {
      const result = await fetch("/api/v1/approvals/selection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject_refs: ids }),
      });
      const body = (await result.json()) as { approval_id?: string; duplicate?: boolean; detail?: string };
      if (!result.ok) {
        toast(body.detail ?? `提交失败(${result.status})`);
        button.disabled = false;
        return;
      }
      toast(body.duplicate ? "已经提交过同一批,未重复建单" : "已创建同意 1 审批单,待你批");
      document.dispatchEvent(new CustomEvent("cp:approvals-changed"));
      picks().forEach((input) => (input.checked = false));
      refresh();
    } catch (error) {
      toast(`提交失败:${String(error)}`);
      button.disabled = false;
    }
  };

  table.addEventListener("change", onChange);
  document.addEventListener("click", onClick);
  refresh();

  return () => {
    table.innerHTML = original;
    table.removeEventListener("change", onChange);
    document.removeEventListener("click", onClick);
    button.remove();
  };
}
