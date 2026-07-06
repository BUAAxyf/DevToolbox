const els = {
  leftText: document.querySelector("#leftText"),
  rightText: document.querySelector("#rightText"),
  leftName: document.querySelector("#leftName"),
  rightName: document.querySelector("#rightName"),
  leftFile: document.querySelector("#leftFile"),
  rightFile: document.querySelector("#rightFile"),
  markdownToggle: document.querySelector("#markdownToggle"),
  swapButton: document.querySelector("#swapButton"),
  compareButton: document.querySelector("#compareButton"),
  diffRows: document.querySelector("#diffRows"),
  addCount: document.querySelector("#addCount"),
  delCount: document.querySelector("#delCount"),
  modCount: document.querySelector("#modCount"),
  sameCount: document.querySelector("#sameCount"),
  diffModeLabel: document.querySelector("#diffModeLabel"),
  diffStatus: document.querySelector("#diffStatus"),
  leftRevision: document.querySelector("#leftRevision"),
  rightRevision: document.querySelector("#rightRevision"),
};

let compareTimer;
let activeRequest = 0;

function setStatus(message, state = "") {
  els.diffStatus.textContent = message;
  els.diffStatus.className = `status ${state}`.trim();
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function highlightPair(left, right) {
  let prefix = 0;
  while (prefix < left.length && prefix < right.length && left[prefix] === right[prefix]) {
    prefix += 1;
  }

  let suffix = 0;
  while (
    suffix + prefix < left.length &&
    suffix + prefix < right.length &&
    left[left.length - 1 - suffix] === right[right.length - 1 - suffix]
  ) {
    suffix += 1;
  }

  const leftMid = left.slice(prefix, left.length - suffix);
  const rightMid = right.slice(prefix, right.length - suffix);
  const leftStart = escapeHtml(left.slice(0, prefix));
  const rightStart = escapeHtml(right.slice(0, prefix));
  const leftEnd = escapeHtml(left.slice(left.length - suffix));
  const rightEnd = escapeHtml(right.slice(right.length - suffix));

  return {
    left: `${leftStart}<span class="inline-del">${escapeHtml(leftMid)}</span>${leftEnd}`,
    right: `${rightStart}<span class="inline-add">${escapeHtml(rightMid)}</span>${rightEnd}`,
  };
}

function rowHtml(row) {
  const className = `${row.kind}-row`;
  let left = escapeHtml(row.left || "");
  let right = escapeHtml(row.right || "");

  if (row.kind === "mod") {
    const highlighted = highlightPair(row.left || "", row.right || "");
    left = highlighted.left;
    right = highlighted.right;
  }

  return `<tr class="${className}">
    <td class="diff-line-no">${row.left_no ?? ""}</td>
    <td class="diff-content">${left}</td>
    <td class="diff-line-no">${row.right_no ?? ""}</td>
    <td class="diff-content">${right}</td>
  </tr>`;
}

function renderResult(result) {
  els.leftRevision.textContent = result.left_name;
  els.rightRevision.textContent = result.right_name;
  els.addCount.textContent = result.stats.added;
  els.delCount.textContent = result.stats.deleted;
  els.modCount.textContent = result.stats.modified;
  els.sameCount.textContent = result.stats.same;
  els.diffModeLabel.textContent = result.mode === "markdown-render" ? "Markdown 渲染后对比" : "普通文本模式";
  els.diffRows.innerHTML = result.rows.length
    ? result.rows.map(rowHtml).join("")
    : '<tr class="context-row"><td class="diff-line-no"></td><td class="diff-content">两侧都为空</td><td class="diff-line-no"></td><td class="diff-content"></td></tr>';
}

async function compareNow() {
  const requestId = ++activeRequest;
  setStatus("正在计算差异...");
  const response = await fetch("/api/text-diff/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      left_text: els.leftText.value,
      right_text: els.rightText.value,
      left_name: els.leftName.value,
      right_name: els.rightName.value,
      markdown_render: els.markdownToggle.checked,
    }),
  });

  if (!response.ok) {
    throw new Error(`请求失败：${response.status}`);
  }

  const result = await response.json();
  if (requestId !== activeRequest) return;
  renderResult(result);
  setStatus("差异计算完成", "success");
}

function scheduleCompare() {
  clearTimeout(compareTimer);
  compareTimer = setTimeout(() => {
    compareNow().catch(error => setStatus(error.message, "error"));
  }, 220);
}

async function importFile(input, textarea, nameInput) {
  const file = input.files && input.files[0];
  if (!file) return;
  textarea.value = await file.text();
  nameInput.value = file.name;
  scheduleCompare();
}

els.leftFile.addEventListener("change", () => importFile(els.leftFile, els.leftText, els.leftName));
els.rightFile.addEventListener("change", () => importFile(els.rightFile, els.rightText, els.rightName));
els.leftText.addEventListener("input", scheduleCompare);
els.rightText.addEventListener("input", scheduleCompare);
els.leftName.addEventListener("input", scheduleCompare);
els.rightName.addEventListener("input", scheduleCompare);
els.markdownToggle.addEventListener("change", scheduleCompare);
els.compareButton.addEventListener("click", () => compareNow().catch(error => setStatus(error.message, "error")));
els.swapButton.addEventListener("click", () => {
  const oldLeftText = els.leftText.value;
  els.leftText.value = els.rightText.value;
  els.rightText.value = oldLeftText;

  const oldLeftName = els.leftName.value;
  els.leftName.value = els.rightName.value;
  els.rightName.value = oldLeftName;
  scheduleCompare();
});

compareNow().catch(error => setStatus(error.message, "error"));

