import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles/fonts.css";
import "./styles/cp2.css";
// 原型自己的插画与图表脚本:挂在 window.CP 上,由页面在挂载后调用。
import "./vendor/art.js";
import "./vendor/charts.js";

createRoot(document.getElementById("root")!).render(<App />);
