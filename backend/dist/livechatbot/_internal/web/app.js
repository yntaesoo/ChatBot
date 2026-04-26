const statusEl = document.getElementById("status");
const chatLogEl = document.getElementById("chatLog");
const composerEl = document.getElementById("composer");
const inputEl = document.getElementById("messageInput");

class AvatarDriver {
  async speak(_audioUrl) {}
  setMouthOpen(_value01) {}
  setExpression(_name, _weight01, _durationMs) {}
  setIdle(_state) {}
}

/**
 * MVP용 더미 아바타.
 * Live2D SDK/모델을 붙이면 Live2DAvatarDriver로 교체한다.
 */
class CanvasMouthAvatarDriver extends AvatarDriver {
  constructor(canvas) {
    super();
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.mouth = 0;
    this._draw();
  }

  setMouthOpen(value01) {
    this.mouth = Math.max(0, Math.min(1, value01));
    this._draw();
  }

  _draw() {
    const { width, height } = this.canvas;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, width, height);

    // 배경
    const g = ctx.createLinearGradient(0, 0, 0, height);
    g.addColorStop(0, "rgba(255,255,255,0.06)");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, width, height);

    // 얼굴 원
    ctx.fillStyle = "rgba(255,255,255,0.10)";
    ctx.strokeStyle = "rgba(255,255,255,0.25)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(width / 2, height / 2, 170, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // 눈
    ctx.fillStyle = "rgba(255,255,255,0.65)";
    ctx.beginPath();
    ctx.arc(width / 2 - 55, height / 2 - 45, 12, 0, Math.PI * 2);
    ctx.arc(width / 2 + 55, height / 2 - 45, 12, 0, Math.PI * 2);
    ctx.fill();

    // 입 (mouth open)
    const open = 10 + this.mouth * 70;
    ctx.strokeStyle = "rgba(255,255,255,0.75)";
    ctx.lineWidth = 8;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.ellipse(width / 2, height / 2 + 55, 60, open / 2, 0, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = "rgba(255,255,255,0.55)";
    ctx.font = "14px system-ui, sans-serif";
    ctx.fillText("Live2D 연결 전 더미 아바타", 16, height - 16);
  }
}

let avatarCanvas = document.getElementById("avatarCanvas");
let avatar = null; // Will be initialized with Live2D later
let pixiApp = null;
let activeModel = null;
let modelRaf = null;
let modelBaseScale = 1;
const zoomSettings = {};

let currentAbortController = null;
let isSpeakingAborted = false;
let currentAudio = null;

async function maybeEnableLive2D() {
  const params = new URLSearchParams(location.search);
  const disable = params.get("live2d") === "0";
  if (disable) return;

  const debug = params.get("debug") === "1";
  const log = (...args) => console.log("[Live2D]", ...args);
  const debugChat = (msg) => {
    if (debug) addMessage("assistant", msg);
    else log(msg);
  };

  try {
    if (debug && Array.isArray(window.__live2dLoadErrors) && window.__live2dLoadErrors.length) {
      const last = window.__live2dLoadErrors[window.__live2dLoadErrors.length - 1];
      debugChat(`Live2D 최근 에러: ${JSON.stringify(last)}`);
      window.__live2dLoadErrors.length = 0;
    }

    log("Live2D 모드 시작(로딩 중)...");
    setStatus("Live2D 로딩 중…");

    // sandbox.js 와 완벽히 동일한 ESM 직접 로드 방식 적용
    if (!window.Live2DCubismCore && typeof Live2DCubismCore !== "undefined") {
      window.Live2DCubismCore = Live2DCubismCore;
    }
    if (!window.Live2DCubismCore) throw new Error("Live2DCubismCore 로드 실패");

    if (!pixiApp) {
      const PIXI = await import("https://esm.sh/pixi.js@6.5.10");
      const live2d = await import("https://esm.sh/pixi-live2d-display@0.4.0/cubism4");
      window.PIXI = PIXI;

      const { Live2DModel } = live2d;
      if (!Live2DModel) throw new Error("Live2DModel export 없음");
      Live2DModel.registerTicker?.(PIXI.Ticker);

      pixiApp = new PIXI.Application({
        view: avatarCanvas,
        autoStart: true,
        backgroundAlpha: 0,
        antialias: true,
        autoDensity: true,
        resolution: devicePixelRatio || 1,
        sharedTicker: true,
      });
      window.Live2DModel = Live2DModel;
    }

    if (activeModel) {
      pixiApp.stage.removeChild(activeModel);
      activeModel.destroy({ children: true });
      activeModel = null;
    }
    if (modelRaf) {
      cancelAnimationFrame(modelRaf);
      modelRaf = null;
    }

    const MODEL_URL = document.getElementById("modelSelect").value;
    const model = await window.Live2DModel.from(MODEL_URL, { autoInteract: false });
    activeModel = model;
    model.autoUpdate = true;
    model.visible = true;
    model.alpha = 1;

    pixiApp.stage.addChild(model);

    // 배치
    const w = avatarCanvas.clientWidth || 520;
    const h = avatarCanvas.clientHeight || 520;
    try {
      const lb = model.getLocalBounds?.();
      const lw = lb?.width || 0;
      const lh = lb?.height || 0;
      if (lw > 0 && lh > 0) {
        model.pivot?.set?.(lb.x + lw / 2, lb.y + lh / 2);
        const s = Math.min(w / lw, h / lh) * 0.9;
        modelBaseScale = Math.max(0.1, Math.min(20, s));
      } else {
        modelBaseScale = 0.7;
      }
      
      const zoomSlider = document.getElementById("zoomSlider");
      const currentZoom = zoomSettings[MODEL_URL] || 1;
      if (zoomSlider) zoomSlider.value = currentZoom;
      model.scale.set(modelBaseScale * currentZoom);
      
      model.position.set(w / 2, h / 2 + h * 0.15);
    } catch (_) {
      modelBaseScale = 0.7;
      const currentZoom = zoomSettings[MODEL_URL] || 1;
      const zoomSlider = document.getElementById("zoomSlider");
      if (zoomSlider) zoomSlider.value = currentZoom;
      model.position.set(w / 2, h * 0.6);
      model.scale.set(modelBaseScale * currentZoom);
    }

    try {
      await model.motion?.("Idle");
    } catch (_) {}

    // 입모양 연동을 위한 글로벌 avatar 객체화
    avatar = {
      setMouthOpen: (value01) => {
        try {
          const core = model?.internalModel?.coreModel;
          if (core) core.setParameterValueById("ParamMouthOpenY", Math.max(0, Math.min(1, value01)));
        } catch (_) {}
      }
    };

    // 입모양 틱
    const tick = () => {
      // 렌더 루프에서 입모양을 지속적으로 적용
      if (avatar._mouth !== undefined) {
        avatar.setMouthOpen(avatar._mouth);
      }
      modelRaf = requestAnimationFrame(tick);
    };
    tick();

    // avatar.setMouthOpen 오버라이드 (오디오 재생시 호출됨)
    const originalSetMouthOpen = avatar.setMouthOpen;
    avatar.setMouthOpen = (val) => {
      avatar._mouth = val;
      originalSetMouthOpen(val);
    };

    log("Live2D 로드됨(히요리 모델).");
    setStatus("Live2D 로드됨");
  } catch (e) {
    addMessage("assistant", `Live2D 초기화 실패: ${e?.message || String(e)}`);
    setStatus("대기");
  }
}

function setStatus(text) {
  statusEl.textContent = text;
}

function addMessage(role, content) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  const roleEl = document.createElement("div");
  roleEl.className = "role";
  roleEl.textContent = role === "user" ? "나" : "챗봇";
  const cEl = document.createElement("div");
  cEl.className = "content";
  cEl.textContent = content;
  el.appendChild(roleEl);
  el.appendChild(cEl);
  chatLogEl.appendChild(el);
  chatLogEl.scrollTop = chatLogEl.scrollHeight;
  return cEl;
}

function splitIntoSpeakableSentences(text) {
  // 한국어/영어 혼용을 고려해 문장 단위로 잘라 TTS 큐를 만든다.
  const chunks = [];
  let buf = "";
  for (const ch of text) {
    buf += ch;
    if (/[.!?。！？\n]/.test(ch)) {
      const t = buf.trim();
      if (t) chunks.push(t);
      buf = "";
    }
  }
  const tail = buf.trim();
  if (tail) chunks.push(tail);
  return chunks;
}

async function fetchTTS(text) {
  let voice = "alloy";
  const modelUrl = document.getElementById("modelSelect").value;
  if (modelUrl.includes("haru")) {
    voice = "nova";
  } else if (modelUrl.includes("hiyori")) {
    voice = "shimmer";
  }

  const res = await fetch("/api/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice }),
  });
  if (!res.ok) {
    let detail = "";
    try {
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("application/json")) {
        const j = await res.json();
        detail = j?.error ? ` (${j.error})` : "";
      } else {
        const t = await res.text();
        detail = t ? ` (${t})` : "";
      }
    } catch (_) {
      // ignore
    }
    throw new Error(`TTS 실패: ${res.status}${detail}`);
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

async function playWithVolumeLipSync(audioUrl) {
  if (isSpeakingAborted) return;
  const audio = new Audio(audioUrl);
  currentAudio = audio;
  audio.crossOrigin = "anonymous";

  // WebAudio로 볼륨을 분석해 입 벌림을 구동(1차 MVP)
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  const ctx = new AudioContext();
  const src = ctx.createMediaElementSource(audio);
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 2048;
  src.connect(analyser);
  analyser.connect(ctx.destination);

  const data = new Uint8Array(analyser.fftSize);
  let raf = 0;

  const tick = () => {
    analyser.getByteTimeDomainData(data);
    // RMS
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      const v = (data[i] - 128) / 128;
      sum += v * v;
    }
    const rms = Math.sqrt(sum / data.length);
    // 경험치 기반 스케일(대충 보기 좋게)
    const mouth = Math.max(0, Math.min(1, (rms - 0.02) * 18));
    avatar.setMouthOpen(mouth);
    raf = requestAnimationFrame(tick);
  };

  audio.addEventListener("ended", () => {
    cancelAnimationFrame(raf);
    avatar.setMouthOpen(0);
    ctx.close().catch(() => {});
    URL.revokeObjectURL(audioUrl);
    if (currentAudio === audio) currentAudio = null;
  });

  if (isSpeakingAborted) return;
  await ctx.resume();
  tick();
  await audio.play();
  return new Promise((resolve) => audio.addEventListener("ended", resolve, { once: true }));
}

async function speakByQueue(fullText) {
  const sentences = splitIntoSpeakableSentences(fullText);
  for (const s of sentences) {
    if (isSpeakingAborted) break;
    try {
      const url = await fetchTTS(s);
      if (isSpeakingAborted) break;
      await playWithVolumeLipSync(url);
    } catch (e) {
      if (isSpeakingAborted) break;
      console.error(e);
    }
  }
}

function stopChat() {
  isSpeakingAborted = true;
  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.dispatchEvent(new Event("ended"));
    currentAudio = null;
  }
  const sendBtn = document.getElementById("sendBtn");
  const stopBtn = document.getElementById("stopBtn");
  if (sendBtn && stopBtn) {
    sendBtn.style.display = "inline-block";
    stopBtn.style.display = "none";
  }
  inputEl.disabled = false;
  setStatus("답변 중단됨");
}

document.getElementById("stopBtn").addEventListener("click", stopChat);

async function streamChat(userText) {
  isSpeakingAborted = false;
  currentAbortController = new AbortController();
  
  const sendBtn = document.getElementById("sendBtn");
  const stopBtn = document.getElementById("stopBtn");
  if (sendBtn && stopBtn) {
    sendBtn.style.display = "none";
    stopBtn.style.display = "inline-block";
  }

  const messages = [{ role: "user", content: userText }];

  const assistantContentEl = addMessage("assistant", "");
  let full = "";

  const langSelect = document.getElementById("langSelect");
  const language = langSelect.options[langSelect.selectedIndex].text.replace("언어: ", "");

  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, language }),
    signal: currentAbortController.signal
  });

  if (!res.ok) throw new Error(`채팅 실패: ${res.status}`);

  const reader = res.body.getReader();
  const dec = new TextDecoder("utf-8");
  let buf = "";

  setStatus("응답 생성 중…");

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });

    // SSE는 \n\n 로 이벤트를 구분
    let idx;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const rawEvent = buf.slice(0, idx);
      buf = buf.slice(idx + 2);

      const line = rawEvent
        .split("\n")
        .find((l) => l.startsWith("data: "));
      if (!line) continue;

      const payload = JSON.parse(line.replace(/^data:\s*/, ""));
      if (payload.type === "delta") {
        full += payload.text;
        assistantContentEl.textContent = full;
        chatLogEl.scrollTop = chatLogEl.scrollHeight;
      } else if (payload.type === "error") {
        throw new Error(payload.message || "알 수 없는 오류");
      }
    }
  }

  setStatus("TTS 생성/재생 중…");
  await speakByQueue(full);
  setStatus("대기");
}

composerEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = "";
  addMessage("user", text);

  try {
    inputEl.disabled = true;
    setStatus("전송 중…");
    await streamChat(text);
  } catch (err) {
    if (err.name === 'AbortError') {
      console.log("Stream aborted by user.");
    } else {
      addMessage("assistant", `오류: ${err?.message || String(err)}`);
      setStatus("오류");
    }
  } finally {
    if (!isSpeakingAborted) {
      const sendBtn = document.getElementById("sendBtn");
      const stopBtn = document.getElementById("stopBtn");
      if (sendBtn && stopBtn) {
        sendBtn.style.display = "inline-block";
        stopBtn.style.display = "none";
      }
    }
    inputEl.disabled = false;
    inputEl.focus();
    if (statusEl.textContent === "오류") {
      // 잠깐 후 복구
      setTimeout(() => setStatus("대기"), 1200);
    }
  }
});

setStatus("대기");
maybeEnableLive2D();

// --- 모델 선택 이벤트 ---
document.getElementById("modelSelect").addEventListener("change", () => {
  maybeEnableLive2D();
});

// --- 줌 슬라이더 이벤트 ---
document.getElementById("zoomSlider").addEventListener("input", (e) => {
  const zoom = parseFloat(e.target.value);
  const MODEL_URL = document.getElementById("modelSelect").value;
  zoomSettings[MODEL_URL] = zoom;
  
  if (activeModel) {
    activeModel.scale.set(modelBaseScale * zoom);
  }
});

// --- 음성 입력 (Web Speech API) ---
const micBtn = document.getElementById("micBtn");
let recognition = null;

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.interimResults = false;
  recognition.continuous = false;

  recognition.onstart = () => {
    micBtn.classList.add("recording");
    inputEl.placeholder = "듣고 있습니다...";
  };

  recognition.onend = () => {
    micBtn.classList.remove("recording");
    inputEl.placeholder = "메시지를 입력하세요";
  };

  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    inputEl.value = text;
    // 자동으로 전송하려면 아래 주석 해제
    // document.getElementById("composer").dispatchEvent(new Event("submit", { cancelable: true }));
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error", event.error);
    micBtn.classList.remove("recording");
    inputEl.placeholder = "메시지를 입력하세요";
  };

  micBtn.addEventListener("click", () => {
    if (micBtn.classList.contains("recording")) {
      recognition.stop();
    } else {
      recognition.lang = document.getElementById("langSelect").value;
      recognition.start();
    }
  });
} else {
  micBtn.style.display = "none";
  console.log("SpeechRecognition API not supported in this browser.");
}

