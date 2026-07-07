const markdownEls = {
  input: document.querySelector("#markdownInput"),
  preview: document.querySelector("#markdownPreview"),
  status: document.querySelector("#markdownStatus"),
  decodeButton: document.querySelector("#decodeEscapesButton"),
  clearButton: document.querySelector("#clearMarkdownButton"),
  sourceStats: document.querySelector("#sourceStats"),
  renderModeLabel: document.querySelector("#renderModeLabel"),
};

let markdownTimer;
let activeMarkdownRequest = 0;

function setMarkdownStatus(message, state = "") {
  markdownEls.status.textContent = message;
  markdownEls.status.className = `status ${state}`.trim();
}

function updateSourceStats() {
  const text = markdownEls.input.value;
  const lines = text ? text.split(/\r?\n/).length : 0;
  markdownEls.sourceStats.textContent = `${text.length} 字 / ${lines} 行`;
}

async function renderMarkdown({ decodeEscapes = false } = {}) {
  const requestId = ++activeMarkdownRequest;
  updateSourceStats();
  setMarkdownStatus(decodeEscapes ? "正在转换转义符并渲染..." : "正在渲染...");

  const response = await fetch("/api/markdown/render", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: markdownEls.input.value,
      decode_escapes: decodeEscapes,
    }),
  });

  if (!response.ok) {
    throw new Error(`请求失败：${response.status}`);
  }

  const payload = await response.json();
  if (requestId !== activeMarkdownRequest) return;

  if (decodeEscapes) {
    markdownEls.input.value = payload.source;
    updateSourceStats();
  }

  markdownEls.preview.innerHTML = payload.html || '<p class="empty-preview">暂无渲染内容</p>';
  markdownEls.renderModeLabel.textContent = payload.decoded ? "已转义并渲染" : "实时预览";
  setMarkdownStatus(payload.decoded ? "转义符已转换，渲染完成" : "渲染完成", "success");
}

function scheduleMarkdownRender() {
  updateSourceStats();
  clearTimeout(markdownTimer);
  markdownTimer = setTimeout(() => {
    renderMarkdown().catch(error => setMarkdownStatus(error.message, "error"));
  }, 220);
}

markdownEls.input.addEventListener("input", scheduleMarkdownRender);
markdownEls.decodeButton.addEventListener("click", () => {
  renderMarkdown({ decodeEscapes: true }).catch(error => setMarkdownStatus(error.message, "error"));
});
markdownEls.clearButton.addEventListener("click", () => {
  markdownEls.input.value = "";
  markdownEls.preview.innerHTML = '<p class="empty-preview">暂无渲染内容</p>';
  markdownEls.renderModeLabel.textContent = "实时预览";
  updateSourceStats();
  setMarkdownStatus("等待渲染");
});

renderMarkdown().catch(error => setMarkdownStatus(error.message, "error"));

