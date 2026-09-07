<template>
  <div class="chat-page">
    <div class="ambient" aria-hidden="true"></div>

    <header class="topbar">
      <div class="brand">
        <span class="logo" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <path d="M8 21.5V12.5L13 9.5L19 12.5V21.5L13 24.5L8 21.5Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
            <path d="M13 12.6V21.4M8.2 12.6L13 15.4L18.8 12.6" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
            <circle cx="22.5" cy="9.5" r="2.2" fill="#c9642a"/>
          </svg>
        </span>
        <div>
          <h1>Data Agent</h1>
          <p>用自然语言查询数仓</p>
        </div>
      </div>
      <div class="status-pill" :class="{ busy: loading }">
        <span class="status-dot"></span>
        {{ loading ? "正在分析" : "就绪" }}
      </div>
    </header>

    <div ref="messagesEl" class="messages">
      <section v-if="!messages.length" class="empty-state">
        <div class="orbit" aria-hidden="true">
          <span></span><span></span><span></span>
        </div>
        <p class="eyebrow">问数工作台</p>
        <h2>把业务问题交给 Agent 去查</h2>
        <p class="lead">抽取关键词、召回字段与指标，再生成并执行 SQL，结果以表格返回。</p>
        <div class="hints">
          <button
            v-for="hint in hints"
            :key="hint"
            type="button"
            class="hint"
            :disabled="loading"
            @click="sendQuestion(hint)"
          >
            {{ hint }}
          </button>
        </div>
      </section>

      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message-row', msg.role]"
      >
        <div v-if="msg.role === 'assistant'" class="avatar agent" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M5 16.5V8.8L11 5.5L17 8.8V16.5L11 19.8L5 16.5Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M11 8.6V16.4M5.3 8.8L11 11.8L16.7 8.8" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </div>

        <div class="bubble" :class="msg.type">
          <div v-if="msg.type === 'text'" class="text">
            {{ msg.content }}
          </div>

          <div v-else-if="msg.type === 'steps'" class="steps">
            <div class="steps-head">
              <span>分析进度</span>
              <span v-if="msg.steps.length">{{ doneCount(msg.steps) }}/{{ msg.steps.length }}</span>
            </div>
            <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="step" :class="step.status">
              <span class="marker" :class="step.status" aria-hidden="true">
                <span v-if="step.status === 'running'" class="spinner"></span>
                <span v-else-if="step.status === 'success'" class="check"></span>
                <span v-else-if="step.status === 'error'" class="cross"></span>
              </span>
              <span class="step-text">{{ step.text }}</span>
              <span class="step-label">{{ statusLabel(step.status) }}</span>
            </div>
            <p v-if="!msg.steps.length" class="steps-wait">正在接入分析链路…</p>
          </div>

          <div v-else-if="msg.type === 'table'" class="table-card">
            <div class="table-head">
              <strong>查询结果</strong>
              <span>{{ msg.rows.length }} 行</span>
            </div>
            <div v-if="isSingleMetric(msg)" class="metric-hero">
              <span>{{ msg.columns[0] }}</span>
              <strong>{{ formatCell(msg.rows[0][msg.columns[0]]) }}</strong>
            </div>
            <div v-else-if="msg.columns.length" class="table-wrap">
              <table class="result-table">
                <thead>
                  <tr>
                    <th v-for="col in msg.columns" :key="col">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rIdx) in msg.rows" :key="rIdx">
                    <td v-for="col in msg.columns" :key="col">
                      {{ formatCell(row[col]) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-else class="table-empty">没有返回数据行</p>
          </div>

          <div v-else-if="msg.type === 'error'" class="error-card">
            <span class="error-icon" aria-hidden="true">!</span>
            <div>
              <strong>分析中断</strong>
              <p>{{ msg.content }}</p>
            </div>
          </div>
        </div>

        <div v-if="msg.role === 'user'" class="avatar user" aria-hidden="true">你</div>
      </div>

      <div class="messages-bottom-spacer"></div>
    </div>

    <div class="input-wrapper">
      <form class="input-box" @submit.prevent="sendQuestion()">
        <textarea
          v-model="question"
          rows="1"
          :disabled="loading"
          placeholder="用一句话描述你想查的数据，回车发送"
          @keydown.enter.exact.prevent="sendQuestion()"
        ></textarea>
        <button type="submit" :disabled="loading || !question.trim()">
          {{ loading ? "分析中" : "发送" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref } from "vue";

const API_URL = "/api/query";

const question = ref("");
const loading = ref(false);
const messages = ref([]);
const messagesEl = ref(null);
const hints = [
  "统计华北地区的销售总额",
  "统计各区域的销售总额",
  "销量最高的前 10 个商品",
  "苹果品牌的成交总额",
];

function statusLabel(status) {
  if (status === "running") return "进行中";
  if (status === "success") return "完成";
  if (status === "error") return "失败";
  return "";
}

function doneCount(steps) {
  return steps.filter((step) => step.status === "success").length;
}

function isSingleMetric(msg) {
  return msg.columns.length === 1 && msg.rows.length === 1;
}

function formatCell(value) {
  if (value === null || value === undefined || value === "") return "—";
  const numeric = typeof value === "number"
    ? value
    : (typeof value === "string" && /^-?\d+(\.\d+)?$/.test(value) ? Number(value) : null);
  if (numeric !== null && Number.isFinite(numeric)) {
    return numeric.toLocaleString("zh-CN", { maximumFractionDigits: 4 });
  }
  return value;
}

function scrollToBottom() {
  const el = messagesEl.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

async function sendQuestion(preset) {
  const q = (typeof preset === "string" ? preset : question.value).trim();
  if (!q || loading.value) return;

  question.value = "";
  loading.value = true;

  messages.value.push({ role: "user", type: "text", content: q });

  const stepIndex =
    messages.value.push({
      role: "assistant",
      type: "steps",
      steps: [],
    }) - 1;

  await nextTick();
  scrollToBottom();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q }),
    });

    if (!response.ok) throw new Error(`服务返回 ${response.status}`);
    if (!response.body) throw new Error("服务器未返回流");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const evt of events) {
        const line = evt.trim();
        if (!line.startsWith("data:")) continue;

        let data;
        try {
          data = JSON.parse(line.replace(/^data:\s*/, ""));
        } catch {
          continue;
        }

        const steps = messages.value[stepIndex].steps;

        if (data.type === "progress") {
          let step = steps.find((s) => s.text === data.step);

          if (!step) {
            step = {
              text: data.step,
              status: data.status,
            };
            steps.push(step);
          } else {
            step.status = data.status;
          }
        } else if (data.type === "result" && Array.isArray(data.data)) {
          const rows = data.data;
          messages.value.push({
            role: "assistant",
            type: "table",
            columns: rows.length ? Object.keys(rows[0]) : [],
            rows,
          });
        } else if (data.type === "error") {
          messages.value.push({
            role: "assistant",
            type: "error",
            content: data.message || "发生错误",
          });
        }

        await nextTick();
        scrollToBottom();
      }
    }
  } catch (e) {
    messages.value.push({
      role: "assistant",
      type: "error",
      content: e?.message || "请求失败",
    });
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
}
</script>

<style scoped>
.chat-page {
  position: relative;
  height: 100%;
  overflow: hidden;
  color: var(--ink);
}

.ambient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(900px 480px at 12% -10%, rgba(232, 215, 176, 0.7), transparent 58%),
    radial-gradient(700px 420px at 92% 8%, rgba(22, 53, 43, 0.12), transparent 50%),
    linear-gradient(180deg, #f7f3ea 0%, var(--parchment) 46%, #ece4d4 100%);
  pointer-events: none;
}

.ambient::after {
  content: "";
  position: absolute;
  inset: 0;
  opacity: 0.28;
  background-image:
    linear-gradient(rgba(28, 25, 21, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(28, 25, 21, 0.035) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(180deg, #000 0%, transparent 78%);
}

.topbar,
.messages,
.input-wrapper {
  position: relative;
  z-index: 1;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 76px;
  padding: 0 clamp(20px, 6vw, 88px);
  border-bottom: 1px solid var(--line);
  background: rgba(255, 252, 246, 0.72);
  backdrop-filter: blur(16px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: var(--copper-soft);
  background: var(--forest);
  box-shadow: 0 8px 20px rgba(22, 53, 43, 0.2);
}

.logo svg {
  width: 22px;
  height: 22px;
}

.brand h1 {
  margin: 0;
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 560;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.brand p {
  margin: 3px 0 0;
  color: var(--ink-soft);
  font-size: 13px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--paper);
  color: var(--ink-soft);
  font-size: 13px;
  font-weight: 600;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2f8f62;
  box-shadow: 0 0 0 4px rgba(47, 143, 98, 0.12);
}

.status-pill.busy .status-dot {
  background: var(--copper);
  box-shadow: 0 0 0 4px rgba(201, 100, 42, 0.16);
  animation: pulse 1.2s ease-in-out infinite;
}

.messages {
  height: calc(100% - 76px);
  overflow-y: auto;
  padding: 28px clamp(16px, 8vw, 120px) 0;
}

.empty-state {
  max-width: 640px;
  margin: 48px auto 0;
  text-align: center;
}

.orbit {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 18px;
}

.orbit span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--forest);
}

.orbit span:nth-child(2) {
  background: var(--copper);
  transform: translateY(-4px);
}

.orbit span:nth-child(3) {
  background: var(--copper-soft);
}

.eyebrow {
  margin: 0 0 10px;
  color: var(--copper);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.empty-state h2 {
  margin: 0;
  font-family: var(--serif);
  font-size: clamp(32px, 5vw, 46px);
  font-weight: 560;
  letter-spacing: -0.03em;
  line-height: 1.15;
}

.lead {
  margin: 14px auto 0;
  max-width: 460px;
  color: var(--ink-soft);
  font-size: 16px;
}

.hints {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin: 28px auto 0;
  max-width: 520px;
}

.hint {
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(255, 252, 246, 0.86);
  color: var(--ink);
  font-size: 13px;
  text-align: left;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.hint:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(22, 53, 43, 0.28);
  box-shadow: 0 8px 18px rgba(28, 25, 21, 0.06);
}

.hint:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin: 0 auto 18px;
  max-width: 880px;
}

.message-row.user {
  justify-content: flex-end;
}

.avatar {
  flex: 0 0 36px;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: grid;
  place-items: center;
}

.avatar.agent {
  color: var(--copper-soft);
  background: var(--forest);
}

.avatar.agent svg {
  width: 18px;
  height: 18px;
}

.avatar.user {
  background: var(--copper-soft);
  color: var(--forest);
  font-size: 12px;
  font-weight: 700;
}

.bubble {
  max-width: min(760px, calc(100% - 92px));
}

.bubble.text,
.message-row.user .bubble {
  padding: 12px 16px;
  border-radius: 18px 18px 6px 18px;
  background: var(--forest);
  color: #f6f0e4;
  box-shadow: var(--shadow);
}

.message-row.assistant .bubble.text,
.message-row.assistant .bubble.steps,
.message-row.assistant .bubble.table,
.message-row.assistant .bubble.error {
  border-radius: 6px 18px 18px 18px;
}

.message-row.assistant .bubble.steps,
.message-row.assistant .bubble.table,
.message-row.assistant .bubble.error {
  width: min(760px, 100%);
  padding: 16px 18px;
  background: var(--paper);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

.steps-head,
.table-head strong {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.steps-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: var(--ink-soft);
}

.step {
  display: grid;
  grid-template-columns: 18px 1fr auto;
  align-items: center;
  gap: 10px;
  position: relative;
  padding: 4px 0;
  color: var(--ink);
  font-size: 13px;
}

.step:not(:last-child)::before {
  content: "";
  position: absolute;
  left: 8px;
  top: 26px;
  bottom: -2px;
  width: 1px;
  background: var(--line);
}

.marker {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--parchment-deep);
}

.marker.running {
  background: #f4e2c4;
}

.marker.success {
  background: #d8eadc;
}

.marker.error {
  background: #f3d4cf;
}

.spinner {
  width: 10px;
  height: 10px;
  border: 1.6px solid rgba(201, 100, 42, 0.25);
  border-top-color: var(--copper);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.check,
.cross {
  width: 8px;
  height: 5px;
  border-left: 1.7px solid #1f7a4d;
  border-bottom: 1.7px solid #1f7a4d;
  transform: rotate(-45deg) translateY(-1px);
}

.cross {
  width: 8px;
  height: 8px;
  border: none;
  position: relative;
  transform: none;
}

.cross::before,
.cross::after {
  content: "";
  position: absolute;
  left: 3px;
  top: 0;
  width: 1.7px;
  height: 8px;
  background: #b42318;
  border-radius: 2px;
}

.cross::before {
  transform: rotate(45deg);
}

.cross::after {
  transform: rotate(-45deg);
}

.step-label {
  color: var(--ink-soft);
  font-size: 12px;
}

.step.success .step-label {
  display: none;
}

.step.running .step-text {
  font-weight: 600;
}

.steps-wait {
  margin: 0;
  color: var(--ink-soft);
  font-size: 13px;
}

.table-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12px;
}

.table-head span,
.table-empty {
  color: var(--ink-soft);
  font-size: 12px;
}

.table-empty {
  margin: 0;
}

.metric-hero {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px 20px;
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(232, 215, 176, 0.35), rgba(255, 252, 246, 0.2)),
    var(--parchment);
  border: 1px solid var(--line);
}

.metric-hero span {
  color: var(--ink-soft);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.metric-hero strong {
  font-family: var(--sans);
  font-size: 36px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
  color: var(--forest);
}

.table-wrap {
  max-width: 100%;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 12px;
}

.result-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
}

.result-table th,
.result-table td {
  padding: 9px 14px;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
  font-size: 13px;
  text-align: left;
}

.result-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f6f1e6;
  font-weight: 700;
  color: var(--ink-soft);
}

.result-table tbody tr:nth-child(even) {
  background: rgba(243, 239, 230, 0.45);
}

.result-table tbody tr:hover {
  background: rgba(232, 215, 176, 0.35);
}

.result-table tr:last-child td {
  border-bottom: none;
}

.error-card {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.error-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #f3d4cf;
  color: #b42318;
  font-weight: 800;
}

.error-card strong {
  display: block;
  margin-bottom: 4px;
}

.error-card p {
  margin: 0;
  color: #8a2a22;
  font-size: 14px;
}

.input-wrapper {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 22px;
  display: flex;
  justify-content: center;
  padding: 0 16px;
  pointer-events: none;
}

.input-box {
  pointer-events: auto;
  width: 100%;
  max-width: 760px;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 12px 12px 12px 18px;
  border-radius: 22px;
  background: rgba(255, 252, 246, 0.92);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(28, 25, 21, 0.1);
  box-shadow: 0 16px 40px rgba(28, 25, 21, 0.12);
}

.input-box textarea {
  flex: 1;
  min-height: 28px;
  max-height: 120px;
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  color: var(--ink);
  font-size: 15px;
  line-height: 1.45;
}

.input-box button {
  padding: 9px 18px;
  border: none;
  border-radius: 999px;
  background: var(--forest);
  color: #f6f0e4;
  font-size: 14px;
  font-weight: 700;
  transition: transform 0.16s ease, opacity 0.16s ease, background 0.16s ease;
}

.input-box button:hover:not(:disabled) {
  background: var(--forest-mid);
  transform: translateY(-1px);
}

.input-box button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.messages-bottom-spacer {
  height: 148px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  50% {
    opacity: 0.45;
  }
}

@media (max-width: 720px) {
  .topbar {
    height: auto;
    padding: 14px 16px;
  }

  .messages {
    height: calc(100% - 72px);
    padding: 20px 14px 0;
  }

  .empty-state {
    margin-top: 28px;
  }

  .bubble {
    max-width: calc(100% - 46px);
  }

  .avatar.user {
    display: none;
  }

  .status-pill {
    display: none;
  }

  .hints {
    grid-template-columns: 1fr;
  }
}
</style>
