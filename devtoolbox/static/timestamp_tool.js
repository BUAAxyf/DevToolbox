const timestampEls = {
  currentTimestamp: document.querySelector("#currentTimestamp"),
  currentUnitLabel: document.querySelector("#currentUnitLabel"),
  currentDatetime: document.querySelector("#currentDatetime"),
  toggleUnitButton: document.querySelector("#toggleUnitButton"),
  copyCurrentButton: document.querySelector("#copyCurrentButton"),
  pauseNowButton: document.querySelector("#pauseNowButton"),
  timestampInput: document.querySelector("#timestampInput"),
  timestampUnit: document.querySelector("#timestampUnit"),
  timestampTimezone: document.querySelector("#timestampTimezone"),
  timestampToDateButton: document.querySelector("#timestampToDateButton"),
  timestampResult: document.querySelector("#timestampResult"),
  datetimeInput: document.querySelector("#datetimeInput"),
  datetimeTimezone: document.querySelector("#datetimeTimezone"),
  dateToTimestampButton: document.querySelector("#dateToTimestampButton"),
  datetimeResult: document.querySelector("#datetimeResult"),
  datetimeUnit: document.querySelector("#datetimeUnit"),
  status: document.querySelector("#timestampStatus"),
};

let currentUnit = "seconds";
let currentRunning = true;
let currentTimer;

function setTimestampStatus(message, state = "") {
  timestampEls.status.textContent = message;
  timestampEls.status.className = `status ${state}`.trim();
}

function unitLabel(unit) {
  return unit === "milliseconds" ? "毫秒" : "秒";
}

async function copyText(text) {
  if (!text || text === "--") return;
  await navigator.clipboard.writeText(text);
  setTimestampStatus("已复制当前时间戳", "success");
}

async function fetchCurrentTimestamp() {
  if (!currentRunning) return;
  const response = await fetch(`/api/timestamp/now?timezone=Asia/Shanghai&unit=${currentUnit}`);
  if (!response.ok) {
    throw new Error(`当前时间戳请求失败：${response.status}`);
  }
  const payload = await response.json();
  if (!payload.valid) {
    throw new Error(payload.error || "当前时间戳获取失败");
  }

  timestampEls.currentTimestamp.textContent = payload.timestamp;
  timestampEls.currentUnitLabel.textContent = unitLabel(payload.unit);
  timestampEls.currentDatetime.textContent = `${payload.datetime_text} / ${payload.timezone}`;
}

function scheduleCurrentTimestamp() {
  clearInterval(currentTimer);
  fetchCurrentTimestamp().catch(error => setTimestampStatus(error.message, "error"));
  currentTimer = setInterval(() => {
    fetchCurrentTimestamp().catch(error => setTimestampStatus(error.message, "error"));
  }, currentUnit === "milliseconds" ? 300 : 1000);
}

async function postTimestampApi(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`请求失败：${response.status}`);
  }
  return response.json();
}

async function convertTimestampToDatetime() {
  setTimestampStatus("正在转换时间戳...");
  const payload = await postTimestampApi("/api/timestamp/to-datetime", {
    timestamp: timestampEls.timestampInput.value,
    unit: timestampEls.timestampUnit.value,
    timezone: timestampEls.timestampTimezone.value,
  });
  timestampEls.timestampResult.value = payload.result || "";
  setTimestampStatus(payload.valid ? "转换完成" : payload.error, payload.valid ? "success" : "error");
}

async function convertDatetimeToTimestamp() {
  setTimestampStatus("正在转换日期时间...");
  const payload = await postTimestampApi("/api/timestamp/from-datetime", {
    datetime_text: timestampEls.datetimeInput.value,
    unit: timestampEls.datetimeUnit.value,
    timezone: timestampEls.datetimeTimezone.value,
  });
  timestampEls.datetimeResult.value = payload.result || "";
  setTimestampStatus(payload.valid ? "转换完成" : payload.error, payload.valid ? "success" : "error");
}

timestampEls.toggleUnitButton.addEventListener("click", () => {
  currentUnit = currentUnit === "seconds" ? "milliseconds" : "seconds";
  scheduleCurrentTimestamp();
});

timestampEls.copyCurrentButton.addEventListener("click", () => {
  copyText(timestampEls.currentTimestamp.textContent).catch(error => setTimestampStatus(error.message, "error"));
});

timestampEls.pauseNowButton.addEventListener("click", () => {
  currentRunning = !currentRunning;
  timestampEls.pauseNowButton.textContent = currentRunning ? "停止" : "继续";
  timestampEls.pauseNowButton.classList.toggle("danger", currentRunning);
  if (currentRunning) {
    scheduleCurrentTimestamp();
    setTimestampStatus("已继续刷新当前时间戳", "success");
  } else {
    clearInterval(currentTimer);
    setTimestampStatus("已停止刷新当前时间戳");
  }
});

timestampEls.timestampToDateButton.addEventListener("click", () => {
  convertTimestampToDatetime().catch(error => setTimestampStatus(error.message, "error"));
});
timestampEls.dateToTimestampButton.addEventListener("click", () => {
  convertDatetimeToTimestamp().catch(error => setTimestampStatus(error.message, "error"));
});

scheduleCurrentTimestamp();
