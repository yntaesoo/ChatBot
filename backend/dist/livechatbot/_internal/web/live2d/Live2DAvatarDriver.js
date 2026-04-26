/**
 * Live2D(Cubism4) + PixiJS 최소 드라이버.
 * - “샌드박스에서 정상 동작한 경로”를 그대로 본 앱에 이식합니다.
 * - 입모양(ParamMouthOpenY)만 추가로 반영합니다.
 */
export class Live2DAvatarDriver {
  constructor({ canvas, modelUrl, mouthParamId = "ParamMouthOpenY" }) {
    this.canvas = canvas;
    this.modelUrl = modelUrl;
    this.mouthParamId = mouthParamId;

    this._app = null;
    this._model = null;
    this._destroyed = false;
    this._mouth = 0;
    this._raf = 0;
    this._debugInfo = null;

    if (!window.Live2DCubismCore && typeof Live2DCubismCore !== "undefined") {
      window.Live2DCubismCore = Live2DCubismCore;
    }
    if (!window.Live2DCubismCore) {
      throw new Error("Live2DCubismCore 로드 실패");
    }
  }

  get ready() {
    return Boolean(this._model && this._app);
  }

  get debugInfo() {
    return this._debugInfo;
  }

  async load() {
    const PIXI = await import("https://esm.sh/pixi.js@6.5.10");
    const live2d = await import("https://esm.sh/pixi-live2d-display@0.4.0/cubism4");
    const { Live2DModel } = live2d;
    if (!Live2DModel) throw new Error("Live2DModel 로드 실패(ESM import)");

    window.PIXI = PIXI;
    Live2DModel.registerTicker?.(PIXI.Ticker);

    const app = new PIXI.Application({
      view: this.canvas,
      autoStart: true,
      backgroundAlpha: 0,
      antialias: true,
      autoDensity: true,
      resolution: devicePixelRatio || 1,
      sharedTicker: true,
    });
    this._app = app;

    // 모델 로드
    const model = await Live2DModel.from(this.modelUrl, { autoInteract: false });
    this._model = model;

    // 마스킹 버그 우회 (sandbox.js 참고)
    try {
      const core = model?.internalModel?.coreModel;
      const r = model?.internalModel?.renderer;
      const usingMasking = typeof core?.isUsingMasking === "function" ? Boolean(core.isUsingMasking()) : false;
      if (usingMasking && r) {
        if ("_clippingManager" in r) r._clippingManager = null;
        if ("_clippingContextBufferForMask" in r) r._clippingContextBufferForMask = null;
        if ("_clippingContextBufferForDraw" in r) r._clippingContextBufferForDraw = null;
        if ("firstDraw" in r) r.firstDraw = true;
        if (core && typeof core.isUsingMasking === "function") core.isUsingMasking = () => false;
      }
    } catch (_) {}

    model.autoUpdate = true;
    model.visible = true;
    model.alpha = 1;
    app.stage.addChild(model);

    // fit-to-canvas (bounds 기반)
    this._fitToCanvas();

    try {
      await model.motion?.("Idle");
    } catch (_) {}

    const tick = () => {
      if (this._destroyed) return;
      this._applyMouth();
      this._raf = requestAnimationFrame(tick);
    };
    tick();

    this._debugInfo = this._collectDebugInfo();
  }

  _fitToCanvas() {
    const app = this._app;
    const model = this._model;
    if (!app || !model) return;

    const w = this.canvas.clientWidth || this.canvas.width || 520;
    const h = this.canvas.clientHeight || this.canvas.height || 520;

    try {
      const lb = model.getLocalBounds?.();
      const lw = lb?.width || 0;
      const lh = lb?.height || 0;
      if (lw > 0 && lh > 0) {
        model.pivot?.set?.(lb.x + lw / 2, lb.y + lh / 2);
        const s = Math.min(w / lw, h / lh) * 0.9;
        model.scale.set(Math.max(0.1, Math.min(20, s)));
      } else {
        model.scale.set(0.7);
      }
      // Center the model in the canvas
      model.position.set(w / 2, h / 2 + h * 0.15); // slightly lower than center for head
    } catch (_) {
      model.position.set(w / 2, h * 0.6);
      model.scale.set(0.7);
    }
  }

  setMouthOpen(value01) {
    this._mouth = Math.max(0, Math.min(1, value01));
  }

  _applyMouth() {
    const m = this._model;
    if (!m) return;
    const core = m?.internalModel?.coreModel;
    if (!core) return;
    try {
      core.setParameterValueById(this.mouthParamId, this._mouth);
    } catch (_) {}
  }

  _collectDebugInfo() {
    try {
      const m = this._model;
      const im = m?.internalModel;
      const core = im?.coreModel;
      const b = m?.getBounds?.(true);
      return {
        modelUrl: this.modelUrl,
        hasInternalModel: Boolean(im),
        hasCoreModel: Boolean(core),
        bounds: b ? { x: b.x, y: b.y, w: b.width, h: b.height } : null,
        pos: m ? { x: m.x, y: m.y } : null,
        scale: m ? { x: m.scale?.x, y: m.scale?.y } : null,
        coreMeta: {
          isUsingMasking:
            typeof core?.isUsingMasking === "function" ? Boolean(core.isUsingMasking()) : null,
        },
      };
    } catch (_) {
      return { modelUrl: this.modelUrl };
    }
  }

  destroy() {
    this._destroyed = true;
    if (this._raf) cancelAnimationFrame(this._raf);
    this._raf = 0;
    try {
      this._app?.destroy?.(true);
    } catch (_) {}
    this._app = null;
    this._model = null;
  }
}

