import { html, css, LitElement, type PropertyValues } from "lit";
import { property } from "lit/decorators.js";
import type { LoadingIndicatorElement } from "../loading-indicator-element/LoadingIndicatorElement";
import "../loading-indicator-element/loading-indicator-element"

// The AladinLite API does not provide a way to draw arbitrary text at an arbitrary location in an overlay layer.
// This implements the methods necessary to do so when provided as an input to layer.add(). This approach was
// preferable to the others (possibilities included directly getting and drawing on the actual canvas element that the
// other overlay elements are drawn on, or creating another canvas element and placing it directly on top of
// the others) as the text that is drawn will then be integrated with the draw/destroy/redraw loops within aladin,
// and the text will show up in the generated data url that is used for saving an image without having to do anything extra.
class CustomAladinText {
  private x: number;
  private y: number;
  private text: string;
  private color: string;
  private align: string;
  private baseline: string;
  private overlay: unknown;
  private options: Record<string, any>;
  private lineWidth: number = 1;

  constructor(
    x: number,
    y: number,
    text: string,
    options: Record<string, any>,
  ) {
    this.options = options || {};
    this.x = x;
    this.y = y;
    this.text = text || "";
    this.color = options["color"] || "#f72521";
    this.align = options["align"] || "center";
    this.baseline = options["baseline"] || "alphabetic";
    this.overlay = null;
  }

  getOptions() {
    return this.options;
  }

  getOverlay() {
    return this.overlay;
  }

  setOverlay(overlay: unknown) {
    this.overlay = overlay;
  }

  getLineWidth() {
    return this.lineWidth;
  }

  setLineWidth(value: any) {
    this.lineWidth = value;
  }

  draw(ctx: any) {
    ctx.fillStyle = this.color;
    ctx.font = "15px Arial";
    ctx.textAlign = this.align;
    ctx.textBaseline = this.baseline;
    ctx.fillText(this.text, this.x, this.y);
  }
}

export class AladinLiteElement extends LitElement {
  static styles = css`
    :host {
      display: flex;
      flex-direction: column;

      /* aladin vars */
      --bg-color: #ececec;
      --text-color: #212121;
      --border-color: #212121;
      --hover-color: green;
      --toggle-color: dodgerblue;
      --border-size: 2px;
      --valid-color: green;
      --error-color: red;
    }

    input,
    select {
      background: #444444;
      border: none;
      color: var(--hd-color--sand);
      padding: 0.5rem;
    }

    * {
      box-sizing: border-box;
    }

    ::slotted(#aladin-div) {
      flex: auto;
      width: 100%;
      height: 100%;
    }

    .inline-flex {
      display: flex;
      flex-direction: row;
    }

    .w-s {
      width: 64px;
    }

    .w-m {
      width: 96px;
    }

    .h-s {
      height: 36px;
    }

    .p-b-s {
      padding-block: 0.3rem;
    }

    .gap-s {
      gap: 1rem;
    }

    .input-label-wrapper {
      display: flex;
      flex-direction: column;
    }

    .align-fe {
      align-items: flex-end;
    }

    .hd-button {
      cursor: pointer;
      display: inline-block;
      padding: 0.46875rem 0.9375rem;
      border: 1px solid var(--hd-color--sand);
      border-radius: 0px;
      font-size: 0.9rem;
      line-height: 1.35rem;
      font-weight: 400;
      color: var(--hd-color--sand);
      text-decoration: none;
      background: transparent;
      box-shadow: none;
    }

    label {
      font-size: 0.8rem;
      color: var(--hd-color--sand-light);
    }
  `;

  private aladin: any;
  private A: any;
  private intersectionObserver: IntersectionObserver | undefined;

  constructor() {
    super();
    this.addEventListener("in-view", () => {
      if (!this.wasInView) {
        this.initialize();
        this.wasInView = true;
      }
    });
  }

  connectedCallback(): void {
    super.connectedCallback();
  }

  protected firstUpdated(changedProperties: PropertyValues): void {
    super.firstUpdated(changedProperties);

    const div = document.createElement("div");
    div.id = "aladin-div";
    this.appendChild(div);

    this.intersectionObserver = this.setUpIntersectionObserver();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.intersectionObserver?.disconnect();
  }

  setUpIntersectionObserver() {
    const target = this.shadowRoot
      ?.querySelector("slot")
      ?.assignedNodes({ flatten: true })
      .find((n) => n.nodeName === "DIV");
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          this.dispatchEvent(new CustomEvent("in-view"));
        }
      });
    });

    if (target) observer.observe(target as HTMLElement);
    return observer;
  }

  @property()
  ra: number = 0;

  @property()
  dec: number = 0;

  @property()
  targetName: string = "N.A.";

  @property({ attribute: true })
  showCompass = false;

  @property({ attribute: true })
  showScaleBar = false;

  private init = false;
  private wasInView = false;
  private annotationLayer: any;

  initialize() {
    console.log("initializing...")
    import("aladin-lite").then((A) => {
      this.A = A.default;
      this.A.init.then(() => {
        const slot = this.shadowRoot?.querySelector("slot");
        const wrapper = slot
          ?.assignedNodes({ flatten: true })
          .find((n) => n.nodeName === "DIV");
        this.aladin = this.A.aladin(
          wrapper,
          {
            survey: "P/DSS2/color",
            fov: this.getFovAsDegreesFromForm(),
            showReticle: false,
            target: `${this.ra} ${this.dec}`,
            showGotoControl: false,
            showZoomControl: false,
            log: false,
          },
        );
        // mkistner: This is a check to see if aladin is ready. There does not seem to
        // be an internal ready callback or something like it. This approach seems to
        // work for my usecase.
        const interval = setInterval(() => {
          const viewSizePix = this.aladin.getSize();
          if (viewSizePix[0] > 10 && !this.init) {
            clearInterval(interval);
            this.init = true;
            this.onReady();
          }
        }, 100);

        this.aladin.on("positionChanged", () => {
          try {
            this.annotateChart(this.ra, this.dec);
          } catch (e) {
            console.log("There was an error during positionChanged:", e);
          }
        });

        this.aladin.on("zoomChanged", () => {
          this.annotateChart(this.ra, this.dec);
        });
      });
    });
  }

  onReady() {
    this.annotateChart(this.ra, this.dec);

    const loadingIndicator = this.shadowRoot?.querySelector<LoadingIndicatorElement>("loading-indicator-element")
    if (!loadingIndicator) return;
    loadingIndicator.hide();

  }

  getScaleBarFromForm() {
    let size = Number(
      (this.shadowRoot?.querySelector("#scale-bar-size") as HTMLInputElement)
        ?.value,
    );
    if (size < 0) {
      size = 0;
    }
    const units = (
      this.shadowRoot?.querySelector(
        "#scale-bar-units-select option:checked",
      ) as HTMLInputElement
    )?.value;
    const label = String(size) + " " + units;
    const sizeAsDegrees = this.toDegrees(size, units);
    return {
      size: size,
      units: units,
      label: label,
      sizeAsDegrees: sizeAsDegrees,
    };
  }

  getFovAsDegreesFromForm() {
    const fov = Number(
      (this.shadowRoot?.querySelector("#fov") as HTMLInputElement)?.value,
    );
    const units = (
      this.shadowRoot?.querySelector(
        "#fov-units-select option:checked",
      ) as HTMLInputElement
    )?.value;
    let fovAsDegrees;
    if (fov >= 0) {
      fovAsDegrees = this.toDegrees(fov, units);
    }
    return fovAsDegrees;
  }

  toDegrees(value: number, units: string) {
    if (units === "arcmin") {
      return value / 60;
    } else if (units === "arcsec") {
      return value / 3600;
    } else {
      return value;
    }
  }

  annotateChart(targetRa: number, targetDec: number) {
    const color = "#f72525";
    const offsetPixFromEdge = 30;
    const scaleBarTextSpacing = 7;
    const compassTextSpacing = 3;

    const fovDegrees = this.aladin.getFov()[0];
    const viewSizePix = this.aladin.getSize();
    const cosDec = Math.cos((targetDec * Math.PI) / 180);

    if (!this.annotationLayer) {
      this.annotationLayer = this.A.graphicOverlay({
        name: "chart annotations",
        color: color,
        lineWidth: 2,
      })
      this.aladin.addOverlay(this.annotationLayer);
    } else {
      this.annotationLayer.removeAll()
    }

    this.annotationLayer.add(this.A.circle(targetRa, targetDec, fovDegrees / 30));

    // mkistner: This feature does not work reliably with the most recent versions
    // of aladin.
    if (this.showScaleBar) {
      const scaleBar = this.getScaleBarFromForm();
      const scaleBarStartPix = [
        offsetPixFromEdge,
        viewSizePix[1] - offsetPixFromEdge,
      ]; // Bottom left corner
      const scaleBarStart = this.aladin.pix2world(
        scaleBarStartPix[0],
        scaleBarStartPix[1],
        this.aladin.getFrame(),
      );
      const scaleBarEnd = [
        scaleBarStart[0] - scaleBar.sizeAsDegrees / cosDec,
        scaleBarStart[1],
      ];
      let scaleBarEndPix = this.aladin.world2pix(
        scaleBarEnd[0],
        scaleBarEnd[1],
        this.aladin.getFrame(),
      );
      if (!scaleBarEndPix) {
        // mkistner: There is currently a bug in aladin-lite that will cause this
        // to fail, when using GAL frames.
        console.log(`world2pix failed for `, {
          scaleBarEnd,
          viewSizePix,
          scaleBar,
        });
      } else {
        const scaleBarLength = Math.abs(
          scaleBarEndPix[0] - scaleBarStartPix[0],
        );
        this.annotationLayer.add(
          new CustomAladinText(
            scaleBarStartPix[0] + scaleBarLength / 2,
            scaleBarStartPix[1] - scaleBarTextSpacing,
            scaleBar.label,
            { color: color },
          ),
        );
        this.annotationLayer.add(this.A.polyline([scaleBarStart, scaleBarEnd]));
      }
    }

    // mkistner: This feature does not work reliably with the most recent versions
    // of aladin.
    if (this.showCompass) {
      const compassCenterPix = [
        viewSizePix[0] - offsetPixFromEdge,
        viewSizePix[1] - offsetPixFromEdge,
      ];
      const compassArmLength = fovDegrees / 10;
      const compassCenter = this.aladin.pix2world(
        compassCenterPix[0],
        compassCenterPix[1],
        this.aladin.getFrame(),
      );
      const compassNorthArm = [
        compassCenter[0],
        compassCenter[1] + compassArmLength,
      ];
      const compassNorthArmPix = this.aladin.world2pix(
        compassNorthArm[0],
        compassNorthArm[1],
        this.aladin.getFrame(),
      );
      const compassEastArm = [
        compassCenter[0] + compassArmLength / cosDec,
        compassCenter[1],
      ];
      const compassEastArmPix = this.aladin.world2pix(
        compassEastArm[0],
        compassEastArm[1],
        this.aladin.getFrame(),
      );

      this.annotationLayer.add(
        this.A.polyline([compassNorthArm, compassCenter, compassEastArm]),
      );
      this.annotationLayer.add(
        new CustomAladinText(
          compassNorthArmPix[0],
          compassNorthArmPix[1] - compassTextSpacing,
          "N",
          { color: color },
        ),
      );
      this.annotationLayer.add(
        new CustomAladinText(
          compassEastArmPix[0] - compassTextSpacing,
          compassEastArmPix[1],
          "E",
          { color: color, align: "end", baseline: "middle" },
        ),
      );
    }
  }

  downloadImage(_e: Event) {
    const data = this.aladin.getViewDataURL();
    data.then((value: any) => {
      var a = document.createElement("a");
      document.body.appendChild(a);
      a.style = "display: none";
      var json = JSON.stringify(value),
        blob = new Blob([json], { type: "octet/stream" }),
        url = window.URL.createObjectURL(blob);
      a.href = value;
      a.download = `finderchart-${this.targetName}.png`;
      a.click();
      window.URL.revokeObjectURL(url);
    });
  }

  updateFromForm(ra: number, dec: number) {
    const fov = this.getFovAsDegreesFromForm();
    if (fov !== undefined) {
      this.aladin.setFov(fov);
      this.annotateChart(ra, dec);
    }
  }

  render() {
    return html`
      <loading-indicator-element></loading-indicator-element>
      <slot></slot>
      <div id="chart-form-div">
        <div id="chart-form" class="inline-flex gap-s align-fe p-b-s">
          <div class="input-label-wrapper">
            <label for="fov" class="input-group-text bg-transparent"
              >Field of view</label
            >
            <input
              type="number"
              class="form-control w-s h-s"
              aria-label="Field of view"
              id="fov"
              min="0"
              value="10"
              length="10"
            />
          </div>
          <div class="input-label-wrapper">
            <label for="fov-units-select">Unit</label>
            <select id="fov-units-select" class="w-m h-s">
              <option>arcsec</option>
              <option selected>arcmin</option>
              <option>deg</option>
            </select>
          </div>
          ${!this.showScaleBar
            ? ""
            : html`
                <div class="form-group mt-1 mb-1">
                  <div class="input-group">
                    <div class="input-group-prepend">
                      <label
                        class="input-group-text bg-transparent"
                        for="scale-bar-units-select"
                      >
                        Scale bar
                      </label>
                    </div>
                    <input
                      type="number"
                      class="form-control h-s"
                      aria-label="Scale bar size"
                      id="scale-bar-size"
                      min="0"
                      value="1"
                    />
                    <div class="">
                      <select
                        id="scale-bar-units-select"
                        class="form-control h-s"
                      >
                        <option>arcsec</option>
                        <option selected>arcmin</option>
                        <option>deg</option>
                      </select>
                    </div>
                  </div>
                </div>
              `}
          <button
            class="hd-button"
            @click="${() => this.updateFromForm(this.ra, this.dec)}"
          >
            Update
          </button>
        </div>
        <div class="form-group inline-flex p-b-s">
          <button
            class="hd-button"
            id="download-chart"
            download="chart.png"
            @click="${this.downloadImage}"
          >
            Save Image
          </button>
        </div>
      </div>
    `;
  }
}
