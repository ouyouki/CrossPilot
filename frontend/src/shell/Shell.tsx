import { useEffect, useState, type ReactNode } from "react";
import { hydrate } from "./hydrate";

/**
 * 画面外壳:结构照 design/screens/assets/cp2.js 注入的那一份(顶栏 + 左侧导航 + 主区 + 右栏 + toast),
 * 类名与层级一致,样式直接由 cp2.css 提供。改动的地方在下面标了「改动」。
 */

const ICONS: Record<string, string> = {
  today: '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  direction: '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
  candidates: '<path d="M4 6h16M4 12h10M4 18h6"/><circle cx="18" cy="16" r="3"/><path d="M20.2 18.2L22 20"/>',
  sourcing: '<path d="M3 8l9-5 9 5v8l-9 5-9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
  assets: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-8 9"/>',
  listing: '<path d="M9 4h6a1 1 0 0 1 1 1v1H8V5a1 1 0 0 1 1-1z"/><rect x="5" y="6" width="14" height="15" rx="2"/><path d="M9 12h6M9 16h4"/>',
  approvals: '<path d="M8 12.5l3 3 5-6"/><rect x="3" y="3" width="18" height="18" rx="4"/>',
  grants: '<path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
  audit: '<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4M10 12h6M10 16h6"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
};

function Icon({ name }: { name: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: ICONS[name] ?? "" }}
    />
  );
}

type PageKey = "today" | "candidates";

type NavItem = [string, string, PageKey | null, number?];

const NAV: [string, NavItem[]][] = [
  ["", [["today", "今日", "today"]]],
  [
    "流水线",
    [
      ["direction", "方向", null],
      ["candidates", "选品", "candidates"],
      ["sourcing", "货源", null],
      ["assets", "素材", null],
      ["listing", "上架", null],
    ],
  ],
  [
    "治理",
    [
      ["approvals", "待批", null, 5],
      ["grants", "授权清单", null],
      ["audit", "审计", null],
    ],
  ],
  ["", [["settings", "设置", null]]],
];

const SKINS = [
  ["mint", "明亮·青", "默认。浅色侧栏，青色主色", ["#F7FBFA", "#DDF0F0", "#0B6E73"]],
  ["sky", "天空·蓝", "浅蓝侧栏，蓝色主色", ["#F3F8FE", "#DCE9FB", "#1D5FD0"]],
  ["violet", "薰衣草·紫", "浅紫侧栏，紫色主色", ["#F8F6FD", "#E7E2FA", "#5B45C9"]],
  ["paper", "纸白·靛蓝", "中性白灰，靛蓝主色", ["#FFFFFF", "#E8EAFB", "#3B49C4"]],
  ["navy", "深蓝·橙", "深蓝侧栏，橙色品牌点缀", ["#14264A", "#2A4A8C", "#F26B1D"]],
  ["carbon", "碳黑·青", "碳黑侧栏，青色强调", ["#14171C", "#2A323C", "#17B8C9"]],
] as const;

const SKIN_KEY = "cp.skin";

function readSkin(): string {
  try {
    const stored = localStorage.getItem(SKIN_KEY);
    if (stored) return stored;
  } catch {
    /* 隐私模式下忽略 */
  }
  return "mint";
}

export function Shell({
  page,
  crumb,
  detailHtml,
  onNavigate,
  children,
}: {
  page: PageKey;
  crumb: string;
  detailHtml: string;
  onNavigate: (page: PageKey) => void;
  children: ReactNode;
}) {
  const [skin, setSkin] = useState<string>(readSkin);
  const [skinOpen, setSkinOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-skin", skin);
    try {
      localStorage.setItem(SKIN_KEY, skin);
    } catch {
      /* 忽略 */
    }
  }, [skin]);

  useEffect(() => {
    let timer: number | undefined;
    const show = (message: string) => {
      setToast(message);
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setToast(null), 2200);
    };
    const onClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const withToast = target.closest("[data-toast]") as HTMLElement | null;
      if (withToast) {
        show(withToast.dataset.toast ?? "");
        event.preventDefault();
      }
      const copy = target.closest("[data-copy]") as HTMLElement | null;
      if (copy) {
        void navigator.clipboard?.writeText(copy.dataset.copy ?? "");
        show("已复制");
      }
      // 行 → 右栏详情(照 cp2.js:去掉别的 .sel,填模板内容,重新挂载插画/图表)
      const row = target.closest("[data-detail]") as HTMLElement | null;
      if (row && !target.closest("input,button,a,select,textarea")) {
        document.querySelectorAll(".sel").forEach((element) => element.classList.remove("sel"));
        row.classList.add("sel");
        const template = document.getElementById(row.dataset.detail ?? "");
        const detail = document.getElementById("detail");
        if (template && detail) {
          detail.innerHTML = (template as HTMLTemplateElement).innerHTML;
          hydrate(detail);
          detail.scrollTop = 0;
        }
      }
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSkinOpen(false);
      if (event.altKey && /^[1-6]$/.test(event.key)) {
        setSkin(SKINS[Number(event.key) - 1][0]);
        event.preventDefault();
      }
    };
    document.addEventListener("click", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("click", onClick);
      document.removeEventListener("keydown", onKey);
      window.clearTimeout(timer);
    };
  }, []);

  return (
    <>
      <header className="topbar">
        <div className="brand">
          <i>
            <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 3l7 17-7-4-7 4z" />
            </svg>
          </i>
          CrossPilot
        </div>
        <span className="crumb">{crumb}</span>
        <div className="sysbar">
          <span className="sys" data-tip="规则库 2026-10-20 版，新鲜度正常">
            <span className="dot" />
            规则库 <b>FRESH</b>
          </span>
          <span className="sys" data-tip="今日模型花费 ¥312 / 上限 ¥1,500；未设上限=不生成">
            <b>¥312</b>
            <span className="mini">
              <i style={{ width: "21%" }} />
            </span>
            ¥1,500
          </span>
          <span className="sys wait" data-tip="没有第二位审批人：系统用延迟生效、抽检和查看门槛补偿">
            <span className="dot" />
            <b>单人运行</b>
          </span>
          <span className="sys">JP-01 日本站</span>
          <span className="skin-btn">
            <button
              className="btn sm"
              aria-haspopup="true"
              aria-expanded={skinOpen}
              onClick={(event) => {
                event.stopPropagation();
                setSkinOpen((open) => !open);
              }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3a9 9 0 1 0 0 18c1.2 0 2-.8 2-1.8 0-.5-.2-.9-.5-1.3-.3-.4-.5-.8-.5-1.3 0-1 .8-1.8 1.8-1.8H17a4 4 0 0 0 4-4c0-4.4-4-8-9-8z" />
                <circle cx="7.5" cy="11" r="1" />
                <circle cx="10.5" cy="7" r="1" />
                <circle cx="15" cy="7" r="1" />
              </svg>
              <span>换肤</span>
            </button>
            {skinOpen && (
              <div className="skin-pop on" role="menu" onClick={(event) => event.stopPropagation()}>
                <h4>换肤 · 框架配色</h4>
                {SKINS.map(([key, name, desc, colors]) => (
                  <button
                    key={key}
                    className="skin-opt"
                    role="menuitemradio"
                    aria-pressed={skin === key}
                    onClick={() => {
                      setSkin(key);
                      setToast(`已换肤：${name}`);
                    }}
                  >
                    <span className="swatch">
                      <i style={{ background: colors[0] }} />
                      <i style={{ background: `linear-gradient(90deg,${colors[1]} 50%,${colors[2]} 50%)` }} />
                    </span>
                    <span>
                      <b>{name}</b>
                      <span className="d">{desc}</span>
                    </span>
                  </button>
                ))}
                <p className="hint">快捷键：Alt + 1–6。选择会记住。语义色与图表色不随皮肤变化。</p>
              </div>
            )}
          </span>
          <button className="btn sm" onClick={() => setToast("站内通知：无未读")}>
            通知
          </button>
        </div>
      </header>

      <div className="shell">
        <nav className="nav" aria-label="主导航">
          {NAV.map(([group, items], index) => (
            <span key={`${group}-${index}`}>
              {group && <h4>{group}</h4>}
              {items.map(([icon, label, target, count]) => (
                <a
                  key={icon}
                  href="#"
                  aria-current={target === page ? "page" : undefined}
                  onClick={(event) => {
                    event.preventDefault();
                    if (target) onNavigate(target);
                    else setToast("该画面还没做（本阶段只做今日 + 候选）");
                  }}
                >
                  <Icon name={icon} />
                  <span>{label}</span>
                  {count ? <span className="cnt">{count}</span> : null}
                </a>
              ))}
            </span>
          ))}
          <div className="foot">
            <b>ouyouki</b>Owner + Operator · 单人运行
            <br />
            日本站 JP-01 · 跨境直邮
            <br />
            上架通道 A（执行清单）
            <br />
            <a href="#" onClick={(event) => event.preventDefault()}>
              退出登录
            </a>
          </div>
        </nav>
        <main className="main" id="main">
          {children}
        </main>
        <aside
          key={page}
          className="detail"
          id="detail"
          aria-label="详情"
          dangerouslySetInnerHTML={{ __html: detailHtml }}
        />
      </div>
      <div className={toast ? "toast on" : "toast"} id="toast" role="status">
        {toast}
      </div>
      <div className="demo">演示数据 · 非平台事实</div>
    </>
  );
}
