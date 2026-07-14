const rawInput = document.querySelector("#rawInput");
const rawLineNumbers = document.querySelector("#rawLineNumbers");
const rawFoldGutter = document.querySelector("#rawFoldGutter");
const rawMeasure = document.querySelector("#rawMeasure");
const resultViewer = document.querySelector("#resultViewer");
const resultOutput = document.querySelector("#resultOutput");
const statusText = document.querySelector("#status");
const formatButton = document.querySelector("#formatButton");
const fontSizeInput = document.querySelector("#fontSizeInput");
const resultModeLabel = document.querySelector("#resultModeLabel");
const editorGrid = document.querySelector("#jsonEditorGrid");
const copyInputButton = document.querySelector("#copyInputButton");
const copyResultButton = document.querySelector("#copyResultButton");
const wrapInputButton = document.querySelector("#wrapInputButton");
const wrapResultButton = document.querySelector("#wrapResultButton");
const clearInputButton = document.querySelector("#clearInputButton");

let repairTimer;
let rawGutterFrame;
let activeRequest = 0;
let rawSourceText = rawInput.value;
let resultText = "";
let repairedText = "";
let formattedText = "";
let isFormattedView = false;
let isWrapped = false;
let rawFoldedRanges = new Map();
let foldedRanges = new Map();

function setStatus(message, state = "") {
  statusText.textContent = message;
  statusText.className = `status ${state}`.trim();
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function updateFontSize(size) {
  const nextSize = Math.min(Math.max(Number(size) || 14, 11), 24);
  document.documentElement.style.setProperty("--editor-font-size", `${nextSize}px`);
  document.documentElement.style.setProperty("--line-height", `${Math.round(nextSize * 1.55 * 10) / 10}px`);
  fontSizeInput.value = String(nextSize);
  scheduleRawGutterRender();
}

function updateFormatButton() {
  formatButton.textContent = isFormattedView ? "原文" : "格式化";
  formatButton.dataset.mode = isFormattedView ? "formatted" : "repaired";
  resultModeLabel.textContent = isFormattedView ? "格式化视图" : "修复视图";
}

function updateWrapButtons() {
  const label = isWrapped ? "取消换行" : "换行";
  [wrapInputButton, wrapResultButton].forEach((button) => {
    button.textContent = label;
    button.setAttribute("aria-pressed", String(isWrapped));
  });
}

function getIndent(line) {
  return line.match(/^\s*/)[0].length;
}

function isFoldStart(line) {
  const trimmed = line.trimEnd();
  return trimmed.endsWith("{") || trimmed.endsWith("[");
}

function findFoldRanges(lines) {
  const ranges = new Map();
  const stack = [];

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (isFoldStart(line)) {
      stack.push({ line: index, indent: getIndent(line) });
      return;
    }

    if ((trimmed.startsWith("}") || trimmed.startsWith("]")) && stack.length > 0) {
      const start = stack.pop();
      if (index > start.line) {
        ranges.set(start.line, { end: index, indent: start.indent });
      }
    }
  });

  return ranges;
}

function rawVisibleLines() {
  const lines = rawSourceText ? rawSourceText.split("\n") : [""];
  const ranges = findFoldRanges(lines);
  const visibleLines = [];

  for (let index = 0; index < lines.length; index += 1) {
    const range = ranges.get(index);
    const isCollapsed = rawFoldedRanges.has(index) && range;
    let displayText = lines[index];

    if (isCollapsed) {
      displayText += ` … ${range.end - index} 行已折叠`;
    }

    visibleLines.push({ sourceLine: index, displayText, range, isCollapsed });

    if (isCollapsed) {
      index = range.end;
    }
  }

  return visibleLines;
}

function rawLineHeights(visibleLines) {
  rawMeasure.style.width = `${rawInput.clientWidth}px`;
  rawMeasure.classList.toggle("soft-wrap", isWrapped);
  rawMeasure.innerHTML = visibleLines
    .map(({ displayText }) => `<span class="raw-measure-line">${escapeHtml(displayText) || " "}</span>`)
    .join("");

  return Array.from(rawMeasure.children, line => Math.max(line.getBoundingClientRect().height, 1));
}

function renderRawGutters(visibleLines = rawVisibleLines()) {
  const lineHeights = rawLineHeights(visibleLines);

  rawLineNumbers.innerHTML = visibleLines
    .map(({ sourceLine }, index) => `<div class="raw-gutter-row" style="height:${lineHeights[index]}px">${sourceLine + 1}</div>`)
    .join("");
  rawFoldGutter.innerHTML = visibleLines
    .map(({ sourceLine, range, isCollapsed }, index) => {
      let control = "";
      if (range) {
        const arrow = isCollapsed ? "▶" : "▼";
        const label = isCollapsed ? "展开层级" : "折叠层级";
        control = `<button class="fold-button" type="button" data-line="${sourceLine}" aria-label="${label} ${sourceLine + 1} 行">${arrow}</button>`;
      }
      return `<div class="raw-fold-row" style="height:${lineHeights[index]}px">${control}</div>`;
    })
    .join("");
  rawLineNumbers.scrollTop = rawInput.scrollTop;
  rawFoldGutter.scrollTop = rawInput.scrollTop;
}

function scheduleRawGutterRender() {
  cancelAnimationFrame(rawGutterFrame);
  rawGutterFrame = requestAnimationFrame(() => renderRawGutters());
}

function renderRawInput() {
  const visibleLines = rawVisibleLines();
  const displayText = visibleLines.map(({ displayText: line }) => line).join("\n");
  const scrollTop = rawInput.scrollTop;

  if (rawInput.value !== displayText) {
    rawInput.value = displayText;
  }
  rawInput.scrollTop = scrollTop;
  renderRawGutters(visibleLines);
}

function expandRawFoldsForEditing() {
  if (rawFoldedRanges.size === 0) return;

  rawFoldedRanges = new Map();
  renderRawInput();
  setStatus("已展开原始输入，可继续编辑", "success");
}

function renderResult(text) {
  resultText = text;
  const lines = text ? text.split("\n") : [""];
  const ranges = findFoldRanges(lines);
  const rows = [];

  for (let index = 0; index < lines.length; index += 1) {
    const range = ranges.get(index);
    const isCollapsed = foldedRanges.has(index) && range;
    let foldControl = "";
    let lineContent = escapeHtml(lines[index]);

    if (range) {
      const arrow = isCollapsed ? "▶" : "▼";
      const label = isCollapsed ? "展开层级" : "折叠层级";
      foldControl = `<button class="fold-button" type="button" data-line="${index}" aria-label="${label} ${index + 1} 行">${arrow}</button>`;
    }

    if (isCollapsed) {
      const skippedCount = range.end - index;
      lineContent += ` <span class="collapsed-marker">… ${skippedCount} 行已折叠</span>`;
    }

    rows.push(
      `<div class="result-line" data-source-line="${index}">` +
        `<span class="result-line-number" aria-hidden="true">${index + 1}</span>` +
        `<span class="result-fold-cell">${foldControl}</span>` +
        `<span class="result-code-line">${lineContent}</span>` +
      `</div>`,
    );

    if (isCollapsed) {
      index = range.end;
    }
  }

  resultOutput.innerHTML = rows.join("");
}

function setResultText(text, { resetFolds = false } = {}) {
  if (resetFolds) {
    foldedRanges = new Map();
  }
  renderResult(text);
}

function resetResultState(text = "") {
  repairedText = text;
  formattedText = "";
  isFormattedView = false;
  setResultText(text, { resetFolds: true });
  updateFormatButton();
}

async function postJson(endpoint, text) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`请求失败：${response.status}`);
  }

  return response.json();
}

async function repairInput() {
  const text = rawSourceText;
  const requestId = ++activeRequest;

  if (!text.trim()) {
    resetResultState("");
    setStatus("等待输入");
    return;
  }

  setStatus("正在自动修复...");

  try {
    const result = await postJson("/api/json/repair", text);
    if (requestId !== activeRequest) return;

    if (result.valid) {
      resetResultState(result.repaired);
      setStatus("已自动修复，可点击格式化查看缩进结果", "success");
    } else {
      resetResultState("");
      setStatus(result.error || "修复失败", "error");
    }
  } catch (error) {
    if (requestId !== activeRequest) return;
    setStatus(error.message, "error");
  }
}

function scheduleRepair() {
  scheduleRawGutterRender();
  clearTimeout(repairTimer);
  repairTimer = setTimeout(repairInput, 250);
}

async function formatOutput() {
  if (isFormattedView) {
    isFormattedView = false;
    setResultText(repairedText, { resetFolds: true });
    updateFormatButton();
    setStatus("已切换回原文修复结果", "success");
    return;
  }

  if (formattedText) {
    isFormattedView = true;
    setResultText(formattedText, { resetFolds: true });
    updateFormatButton();
    setStatus("已切换到格式化结果，可点击右侧箭头折叠层级", "success");
    return;
  }

  const text = repairedText || resultText || rawSourceText;

  if (!text.trim()) {
    setStatus("请输入需要格式化的内容", "error");
    return;
  }

  setStatus("正在格式化...");

  try {
    const result = await postJson("/api/json/format", text);
    if (result.valid) {
      repairedText = result.repaired;
      formattedText = result.formatted;
      isFormattedView = true;
      setResultText(formattedText, { resetFolds: true });
      updateFormatButton();
      setStatus("格式化完成，可点击右侧箭头折叠层级", "success");
    } else {
      setStatus(result.error || "格式化失败", "error");
    }
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function copyResult() {
  await copyText(resultText, "当前没有可复制的结果", "结果已复制到剪贴板");
}

async function copyText(text, emptyMessage, successMessage) {
  if (!text) {
    setStatus(emptyMessage, "error");
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    setStatus(successMessage, "success");
  } catch {
    setStatus("复制失败，请检查剪贴板权限", "error");
  }
}

function toggleWrap() {
  isWrapped = !isWrapped;
  rawInput.setAttribute("wrap", isWrapped ? "soft" : "off");
  resultOutput.classList.toggle("soft-wrap", isWrapped);
  editorGrid.classList.toggle("wrap-enabled", isWrapped);

  if (isWrapped && foldedRanges.size > 0) {
    setResultText(resultText, { resetFolds: true });
  }

  updateWrapButtons();
  scheduleRawGutterRender();
  setStatus(isWrapped ? "已开启双栏自动换行" : "已关闭双栏自动换行", "success");
}

rawInput.addEventListener("focus", expandRawFoldsForEditing);
rawInput.addEventListener("input", () => {
  rawSourceText = rawInput.value;
  rawFoldedRanges = new Map();
  scheduleRepair();
});
rawInput.addEventListener("scroll", () => {
  rawLineNumbers.scrollTop = rawInput.scrollTop;
  rawFoldGutter.scrollTop = rawInput.scrollTop;
});

rawFoldGutter.addEventListener("click", (event) => {
  const button = event.target.closest(".fold-button");
  if (!button) return;

  const line = Number(button.dataset.line);
  const isCollapsed = rawFoldedRanges.has(line);
  if (isCollapsed) {
    rawFoldedRanges.delete(line);
  } else {
    rawFoldedRanges.set(line, true);
  }
  renderRawInput();
  setStatus(isCollapsed ? "已展开原始输入层级" : "原始输入已折叠；点击输入框可自动展开后编辑", "success");
});

resultViewer.addEventListener("click", (event) => {
  const button = event.target.closest(".fold-button");
  if (!button) return;

  const line = Number(button.dataset.line);
  if (foldedRanges.has(line)) {
    foldedRanges.delete(line);
  } else {
    foldedRanges.set(line, true);
  }
  renderResult(resultText);
});

formatButton.addEventListener("click", formatOutput);
copyInputButton.addEventListener("click", () => {
  copyText(rawSourceText, "当前没有可复制的原始输入", "原始输入已复制到剪贴板");
});
copyResultButton.addEventListener("click", copyResult);
wrapInputButton.addEventListener("click", toggleWrap);
wrapResultButton.addEventListener("click", toggleWrap);
clearInputButton.addEventListener("click", () => {
  rawSourceText = "";
  rawFoldedRanges = new Map();
  rawInput.value = "";
  renderRawInput();
  resetResultState("");
  setStatus("等待输入");
});
fontSizeInput.addEventListener("change", () => updateFontSize(fontSizeInput.value));
fontSizeInput.addEventListener("input", () => updateFontSize(fontSizeInput.value));

updateFormatButton();
updateWrapButtons();
renderRawInput();
renderResult("");
new ResizeObserver(scheduleRawGutterRender).observe(rawInput);
