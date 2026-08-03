const benchmark = [
  {
    id: "Q1",
    type: "số liệu",
    title: "Thời hạn trả hàng",
    query: "Người mua phải gửi yêu cầu trả hàng hoàn tiền trong bao lâu với thực phẩm tươi sống và với các sản phẩm còn lại?",
    filter: "None",
    gold: "Thực phẩm tươi sống/đông lạnh: 24 giờ; sản phẩm còn lại: 15 ngày.",
    score: "2/2",
    docRank: "1",
    evidenceRank: "1",
    rows: [
      ["1", "0.770", "shopee-return-refund-policy", "chunk 7", "Chứa cả mốc 15 ngày và 24 giờ."],
      ["2", "0.627", "shopee-general-return-refund-rules", "chunk 3", "Liên quan thời hạn nhưng không phải gold chính."],
      ["3", "0.619", "shopee-terms-of-service", "chunk 89", "Cùng chủ đề hoàn tiền, ít trực tiếp hơn."]
    ]
  },
  {
    id: "Q2",
    type: "điều kiện",
    title: "Đổi ý còn nguyên bao bì",
    query: "Lý do đổi ý khi sản phẩm còn nguyên tem nhãn mác bao bì áp dụng cho nhóm người mua nào và ngoại trừ những loại nào?",
    filter: '{"customer_role":"buyer"}',
    gold: "Áp dụng cho Kim Cương, Vàng, Shopee VIP; ngoại trừ danh sách hạn chế, Shopee Mart và một số sản phẩm riêng biệt.",
    score: "1/2",
    docRank: "1",
    evidenceRank: "2",
    rows: [
      ["1", "0.545", "shopee-general-return-refund-rules", "chunk 7", "Đúng doc nhưng nói về điều kiện khác."],
      ["2", "0.526", "shopee-general-return-refund-rules", "chunk 8", "Có dòng Đổi ý và ngoại lệ Shopee Mart."],
      ["3", "0.441", "shopee-general-return-refund-rules", "chunk 5", "Bảng điều kiện trả hàng chung."]
    ]
  },
  {
    id: "Q3",
    type: "quy trình + filter",
    title: "Seller phản hồi hàng hoàn",
    query: "Khi hệ thống ghi nhận đã trả hàng thành công nhưng Shop chưa nhận được hàng hoặc hàng hoàn gặp vấn đề thì phải phản hồi khi nào và hạn phản hồi là bao lâu?",
    filter: '{"customer_role":"seller"}',
    gold: "Shop phản hồi từ ngày hệ thống cập nhật trả hàng thành công; hạn phản hồi trong vòng 2 ngày.",
    score: "2/2",
    docRank: "1",
    evidenceRank: "1",
    rows: [
      ["1", "0.687", "shopee-seller-manage-return-refund", "chunk 6", "Bảng seller: thời điểm phản hồi và hạn trong vòng 2 ngày."],
      ["2", "0.667", "shopee-seller-manage-return-refund", "chunk 3", "Trạng thái hàng hoàn của seller."],
      ["3", "0.592", "shopee-seller-manage-return-refund", "chunk 5", "Bước xử lý hàng hoàn sau khi ĐVVC trả thành công."]
    ]
  },
  {
    id: "Q4",
    type: "liệt kê",
    title: "Thời gian hoàn tiền",
    query: "Thời gian nhận tiền hoàn qua Ví ShopeePay, thẻ nội địa Napas, thẻ tín dụng ghi nợ và SPayLater là bao lâu?",
    filter: '{"topic_group":"returns_refunds","customer_role":"buyer"}',
    gold: "ShopeePay: 24 giờ; Napas: 2-5 ngày làm việc; thẻ tín dụng/ghi nợ: 7-14 ngày; SPayLater: 24 giờ.",
    score: "0/2",
    docRank: "1",
    evidenceRank: "None",
    rows: [
      ["1", "0.711", "shopee-refund-time-status", "chunk 7", "Lưu ý về Ví ShopeePay, thiếu Napas và thẻ tín dụng."],
      ["2", "0.685", "shopee-refund-time-status", "chunk 8", "Lưu ý SPayLater kết hợp phương thức khác."],
      ["3", "0.653", "shopee-refund-time-status", "chunk 0", "Title, không chứa bảng trả lời."]
    ]
  },
  {
    id: "Q5",
    type: "ngoại lệ",
    title: "Lỗi thanh toán M10",
    query: "Nếu thanh toán báo lỗi M10 vượt hạn mức thanh toán trong ngày thì Shopee hướng dẫn xử lý thế nào?",
    filter: '{"category":"payment-troubleshooting"}',
    gold: "Với lỗi M10, người mua nên đặt hàng lại vào ngày mai.",
    score: "1/2",
    docRank: "1",
    evidenceRank: "2",
    rows: [
      ["1", "0.529", "shopee-order-payment-errors", "chunk 0", "Title tài liệu lỗi thanh toán."],
      ["2", "0.514", "shopee-order-payment-errors", "chunk 5", "Có dòng M10 và hướng dẫn đặt hàng lại ngày mai."],
      ["3", "0.473", "shopee-order-payment-errors", "chunk 1", "Mở đầu bảng lỗi thanh toán."]
    ]
  }
];

const fullCommand = `cd D:\\codein\\misp@ce\\aiaction\\K4-Day07-Gehihi36
conda activate vmec-clinical-copilot
$env:PYTHONIOENCODING='utf-8'
$env:EMBEDDING_PROVIDER='local'
$env:VECTOR_STORE='chroma'
$env:CHROMA_DIR='.chroma\\shopee_heading_700'
$env:CHUNKER='heading'
$env:CHUNK_SIZE='700'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
python bench.py`;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
const escapeHtml = (text) => text.replace(/[&<>"']/g, (char) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#039;"
}[char]));
const pipelineMessages = [
  "Loaded 10 cleaned Shopee policy documents with provenance metadata.",
  "Chunked with HeadingAwareChunker(700): 392 chunks, headings preserved.",
  "Embedded chunks with sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2.",
  "Wrote vectors and metadata into Chroma persistent collection.",
  "Retrieved top-3 chunks with metadata_filter and cosine ranking.",
  "Evaluated doc hit, evidence hit, chunk-level score, and failure notes."
];
let pipelineStep = -1;
let pipelineTimer = null;

function scoreMeaning(item) {
  if (item.score === "2/2") return "Top-3 has the answer evidence and the answer is grounded.";
  if (item.score === "1/2") return "Relevant evidence appears, but not at rank 1 or context is incomplete.";
  return "Top-3 misses the answer evidence, even if the document is related.";
}

function rowJudgement(item, row) {
  if (item.evidenceRank === row[0]) return ["relevant", "Answer evidence"];
  if (row[2] === item.rows[0][2] && item.evidenceRank !== "None") return ["partial", "Related context"];
  if (item.evidenceRank === "None") return ["miss", "Missing evidence"];
  return ["partial", "Supporting context"];
}

function renderChunkCards(item, limit = 3) {
  return item.rows.slice(0, limit).map((row) => {
    const [tone, label] = rowJudgement(item, row);
    return `
      <article class="chunk-card ${tone}">
        <div class="chunk-head">
          <b>#${row[0]}</b>
          <code>${row[2]} / ${row[3]}</code>
          <span>${row[1]}</span>
        </div>
        <p>${row[4]}</p>
        <div class="chunk-eval">
          <span>${label}</span>
          <small>${tone === "relevant" ? "Use this as citation context." : "Useful for ranking analysis, not enough alone."}</small>
        </div>
      </article>
    `;
  }).join("");
}

function renderTabs() {
  $("#queryTabs").innerHTML = benchmark.map((item, index) => `
    <button class="query-tab ${index === 0 ? "active" : ""}" type="button" data-id="${item.id}">
      <b>${item.id}</b>
      <span>${item.type}</span>
      <small>${item.score}</small>
    </button>
  `).join("");
}

function renderQuery(item) {
  $("#queryType").textContent = `${item.id} / ${item.type}`;
  $("#queryTitle").textContent = item.title;
  $("#queryScore").textContent = item.score;
  $("#queryText").textContent = item.query;
  $("#queryFilter").innerHTML = `<b>metadata_filter</b><code>${item.filter}</code>`;
  $("#queryGold").textContent = item.gold;
  $("#docRank").textContent = item.docRank;
  $("#evidenceRank").textContent = item.evidenceRank;
  $("#chunkCards").innerHTML = `
    <div class="score-guide">
      <b>How to read this result</b>
      <span>${scoreMeaning(item)}</span>
    </div>
    ${renderChunkCards(item)}
  `;
  $("#retrievalRows").innerHTML = `
    <div class="row head"><span>Rank</span><span>Score</span><span>Document</span><span>Chunk</span><span>Evidence note</span></div>
    ${item.rows.map((row) => `
      <div class="row">
        <span>${row[0]}</span>
        <span>${row[1]}</span>
        <code>${row[2]}</code>
        <span>${row[3]}</span>
        <span>${row[4]}</span>
      </div>
    `).join("")}
  `;
  $$(".query-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.id === item.id));
}

function selectedScenario() {
  return benchmark.find((item) => item.id === $("#pipelineScenario").value) || benchmark[2];
}

function resetPipeline() {
  pipelineStep = -1;
  clearTimeout(pipelineTimer);
  $$(".pipeline-stage").forEach((stage) => stage.classList.remove("active", "done"));
  $("#pipelineLog").innerHTML = '<p><span>$</span> Ready. Choose a query and run the pipeline.</p>';
  $("#pipelineResult").innerHTML = '<span class="empty-state">No run yet</span>';
}

function renderPipelineResult(item) {
  const evidenceOk = item.evidenceRank !== "None";
  $("#pipelineResult").innerHTML = `
    <div class="result-card ${evidenceOk ? "ok" : "miss"}">
      <span>${item.id} result</span>
      <strong>${item.score}</strong>
      <p>${evidenceOk ? "Evidence appears in top-3." : "Expected document appears, but evidence is missing from top-3."}</p>
    </div>
    <div class="result-lines">
      <div><b>Expected doc rank</b><span>${item.docRank}</span></div>
      <div><b>Evidence rank</b><span>${item.evidenceRank}</span></div>
      <div><b>Filter</b><code>${item.filter}</code></div>
      <div><b>Top-1</b><code>${item.rows[0][2]} / ${item.rows[0][3]}</code></div>
    </div>
    <div class="pipeline-chunks">
      <b>Retrieved chunks</b>
      ${renderChunkCards(item)}
    </div>
  `;
}

function advancePipeline() {
  if (pipelineStep >= 5) return;
  pipelineStep += 1;
  const item = selectedScenario();
  $$(".pipeline-stage").forEach((stage, index) => {
    stage.classList.toggle("done", index < pipelineStep);
    stage.classList.toggle("active", index === pipelineStep);
  });
  $("#pipelineLog").insertAdjacentHTML("beforeend", `<p><span>${String(pipelineStep + 1).padStart(2, "0")}</span> ${pipelineMessages[pipelineStep]}</p>`);
  $("#pipelineLog").scrollTop = $("#pipelineLog").scrollHeight;
  if (pipelineStep >= 4) renderQuery(item);
  if (pipelineStep === 5) renderPipelineResult(item);
}

function runPipeline() {
  resetPipeline();
  const tick = () => {
    advancePipeline();
    if (pipelineStep < 5) pipelineTimer = setTimeout(tick, 520);
  };
  tick();
}

function runAllQueries() {
  resetPipeline();
  pipelineStep = 5;
  $$(".pipeline-stage").forEach((stage) => stage.classList.add("done"));
  $("#pipelineLog").innerHTML = pipelineMessages.map((message, index) =>
    `<p><span>${String(index + 1).padStart(2, "0")}</span> ${message}</p>`
  ).join("") + benchmark.map((item) =>
    `<p><span>${item.id}</span> score ${item.score}; doc rank ${item.docRank}; evidence rank ${item.evidenceRank}</p>`
  ).join("");
  $("#pipelineResult").innerHTML = `
    <div class="result-card ok">
      <span>Batch benchmark</span>
      <strong>5/5</strong>
      <p>All fixed benchmark queries were tested with the same strategy, embedder, and Chroma store.</p>
    </div>
    <div class="batch-summary">
      ${benchmark.map((item) => `
        <button type="button" data-batch-id="${item.id}">
          <b>${item.id}</b>
          <span>${item.score}</span>
          <small>doc ${item.docRank} / evidence ${item.evidenceRank}</small>
        </button>
      `).join("")}
    </div>
  `;
  renderQuery(benchmark[0]);
  location.hash = "#benchmark";
}

function copyCommand() {
  navigator.clipboard?.writeText(fullCommand).then(() => showToast("Đã copy lệnh chạy benchmark"));
}

async function runRealBenchmark() {
  const output = $("#realBenchmarkOutput");
  output.textContent = "Running bench.py with EMBEDDING_PROVIDER=local and VECTOR_STORE=chroma...\nThis may take a little while on the first run.";
  try {
    const response = await fetch("/api/benchmark", { method: "POST" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    const summary = result.summary || {};
    const summaryText = Object.keys(summary).length ? [
      "[live summary]",
      `Python: ${result.python}`,
      `Embedding: ${summary.Embedding || "unknown"}`,
      `Vector store: ${summary["Vector store"] || "unknown"}`,
      `Chroma dir: ${summary["Chroma dir"] || "unknown"}`,
      `Chunks loaded: ${summary["Chunks loaded"] || "unknown"}`,
      `Doc hit@3: ${summary["Doc hit@3"] || "unknown"}`,
      `Evidence hit@3: ${summary["Evidence hit@3"] || "unknown"}`,
      `Chunk-level score: ${summary["Chunk-level score"] || "unknown"}`,
      ""
    ].join("\n") : "";
    const text = [
      summaryText,
      result.output || "",
      result.error ? `\n[stderr]\n${result.error}` : "",
      result.ok ? "\n[done] benchmark completed" : `\n[failed] return code ${result.returncode ?? "unknown"}`
    ].join("");
    output.innerHTML = escapeHtml(text.trim());
    showToast(result.ok ? "Benchmark thật đã chạy xong" : "Benchmark thật bị lỗi, xem output");
  } catch (error) {
    output.textContent = `Cannot call /api/benchmark.\nStart the live demo server instead:\npython demo_ui\\server.py\n\n${error}`;
    showToast("Cần chạy demo_ui/server.py");
  }
}

async function runStrategySweep() {
  const table = $("#strategyCompare");
  table.innerHTML = '<div class="row head"><span>Strategy</span><span>Chunks</span><span>Doc hit@3</span><span>Evidence hit@3</span><span>Chunk score</span></div><div class="row muted-row"><span>Running sweep... this can take several minutes.</span></div>';
  try {
    const response = await fetch("/api/strategy-sweep", { method: "POST" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    table.innerHTML = `
      <div class="row head"><span>Strategy</span><span>Chunks</span><span>Doc hit@3</span><span>Evidence hit@3</span><span>Chunk score</span></div>
      ${result.runs.map((run) => {
        const summary = run.summary || {};
        return `
          <div class="row ${run.ok ? "" : "bad-row"}">
            <span>${run.strategy}</span>
            <span>${summary["Chunks loaded"] || "-"}</span>
            <span>${summary["Doc hit@3"] || "-"}</span>
            <span>${summary["Evidence hit@3"] || "-"}</span>
            <span>${summary["Chunk-level score"] || "failed"}</span>
          </div>
        `;
      }).join("")}
    `;
    showToast(result.ok ? "Strategy sweep đã chạy xong" : "Sweep dừng vì có lỗi");
  } catch (error) {
    table.innerHTML = `<div class="row muted-row"><span>Cannot call /api/strategy-sweep. Run live server: python demo_ui\\server.py. ${escapeHtml(String(error))}</span></div>`;
    showToast("Cần chạy demo_ui/server.py");
  }
}

function showToast(text) {
  const toast = $("#toast");
  toast.textContent = text;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 1800);
}

function setupNav() {
  const links = $$(".sidebar nav a");
  const sections = links.map((link) => document.querySelector(link.getAttribute("href"))).filter(Boolean);
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      links.forEach((link) => link.classList.toggle("active", link.getAttribute("href") === `#${entry.target.id}`));
    });
  }, { rootMargin: "-20% 0px -65% 0px" });
  sections.forEach((section) => observer.observe(section));
}

function init() {
  renderTabs();
  renderQuery(benchmark[0]);
  $("#queryTabs").addEventListener("click", (event) => {
    const tab = event.target.closest(".query-tab");
    if (!tab) return;
    renderQuery(benchmark.find((item) => item.id === tab.dataset.id));
  });
  $$("[data-copy-command]").forEach((button) => button.addEventListener("click", copyCommand));
  $("#runPipeline").addEventListener("click", runPipeline);
  $("#runAllQueries").addEventListener("click", runAllQueries);
  $("#runRealBenchmark").addEventListener("click", runRealBenchmark);
  $("#runStrategySweep").addEventListener("click", runStrategySweep);
  $("#nextPipeline").addEventListener("click", advancePipeline);
  $("#resetPipeline").addEventListener("click", resetPipeline);
  $("#pipelineResult").addEventListener("click", (event) => {
    const button = event.target.closest("[data-batch-id]");
    if (!button) return;
    renderQuery(benchmark.find((item) => item.id === button.dataset.batchId));
    location.hash = "#benchmark";
  });
  $("#pipelineScenario").addEventListener("change", () => renderQuery(selectedScenario()));
  setupNav();
}

document.addEventListener("DOMContentLoaded", init);
