const logEl = document.getElementById("log");
function log(...args) {
  const s = args
    .map((a) => {
      try {
        return typeof a === "string" ? a : JSON.stringify(a);
      } catch {
        return String(a);
      }
    })
    .join(" ");
  logEl.textContent += s + "\n";
}

const MODEL_URL =
  "/static/assets/live2d/hiyori/hiyori_free_ko/runtime/hiyori_free_t08.model3.json";

function assertCore() {
  // 일부 환경에서 전역 var가 window에 안 붙는 경우 보정
  if (!window.Live2DCubismCore && typeof Live2DCubismCore !== "undefined") {
    window.Live2DCubismCore = Live2DCubismCore;
  }
  if (!window.Live2DCubismCore) {
    throw new Error("Live2DCubismCore 로드 실패");
  }
}

async function main() {
  assertCore();

  log("sandbox: ESM으로 Pixi/Live2D 로딩…");

  // “현재 vendor 조합”을 완전히 우회하기 위해 ESM import를 사용
  const PIXI = await import("https://esm.sh/pixi.js@6.5.10");
  const live2d = await import("https://esm.sh/pixi-live2d-display@0.4.0/cubism4");

  // 일부 런타임은 window.PIXI를 기대하므로 노출
  window.PIXI = PIXI;

  const { Live2DModel } = live2d;
  if (!Live2DModel) throw new Error("Live2DModel export 없음(ESM 로딩 실패)");

  Live2DModel.registerTicker?.(PIXI.Ticker);

  const canvas = document.getElementById("c");
  const app = new PIXI.Application({
    view: canvas,
    autoStart: true,
    backgroundAlpha: 0,
    antialias: true,
    autoDensity: true,
    resolution: devicePixelRatio || 1,
    sharedTicker: true,
  });

  // 샌드박스는 “Pixi 렌더 살아있음”을 눈으로 확인
  const cross = new PIXI.Graphics();
  cross.lineStyle(3, 0x00ff88, 0.9);
  cross.drawCircle(260, 374, 10);
  cross.moveTo(260 - 24, 374);
  cross.lineTo(260 + 24, 374);
  cross.moveTo(260, 374 - 24);
  cross.lineTo(260, 374 + 24);
  app.stage.addChild(cross);

  log("sandbox: 모델 로드 시도", { MODEL_URL });

  const model = await Live2DModel.from(MODEL_URL, { autoInteract: false });
  model.autoUpdate = true;
  model.visible = true;
  model.alpha = 1;

  // 마스킹 토글(샌드박스에서만)
  const keepMask = new URLSearchParams(location.search).get("mask") === "1";
  if (!keepMask) {
    try {
      const core = model?.internalModel?.coreModel;
      const r = model?.internalModel?.renderer;
      const usingMasking =
        typeof core?.isUsingMasking === "function" ? Boolean(core.isUsingMasking()) : false;
      if (usingMasking && r) {
        if ("_clippingManager" in r) r._clippingManager = null;
        if ("_clippingContextBufferForMask" in r) r._clippingContextBufferForMask = null;
        if ("_clippingContextBufferForDraw" in r) r._clippingContextBufferForDraw = null;
        if ("firstDraw" in r) r.firstDraw = true;
        if (core && typeof core.isUsingMasking === "function") core.isUsingMasking = () => false;
      }
    } catch {}
  }

  app.stage.addChild(model);

  // 배치
  try {
    const lb = model.getLocalBounds?.();
    const lw = lb?.width || 0;
    const lh = lb?.height || 0;
    if (lw > 0 && lh > 0) {
      model.pivot?.set?.(lb.x + lw / 2, lb.y + lh / 2);
      const s = Math.min(520 / lw, 520 / lh) * 0.9;
      model.scale.set(Math.max(0.55, Math.min(20, s)));
    } else {
      model.scale.set(0.7);
    }
    model.position.set(260, 374);
  } catch {
    model.position.set(260, 374);
    model.scale.set(0.7);
  }

  try {
    await model.motion?.("Idle");
  } catch {}

  // 상태 로그
  const coreMeta = (() => {
    try {
      const core = model?.internalModel?.coreModel;
      return {
        isUsingMasking:
          typeof core?.isUsingMasking === "function" ? Boolean(core.isUsingMasking()) : null,
      };
    } catch {
      return null;
    }
  })();
  log("sandbox: loaded OK", {
    coreMeta,
    bounds: model.getBounds?.(),
    scale: { x: model.scale?.x, y: model.scale?.y },
  });
}

main().catch((e) => {
  log("sandbox: FAILED", e?.message || String(e));
  log(e?.stack || "");
});

