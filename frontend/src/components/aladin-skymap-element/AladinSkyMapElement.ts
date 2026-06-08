import { html, css, LitElement, type PropertyValues } from "lit";
import { property } from "lit/decorators.js";

export class AladinSkymapElement extends LitElement {
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

    * {
      box-sizing: border-box;
    }

    #aladin-div {
      flex: auto;
      width: 100%;
      height: 100%;
    }
  `;

  private aladin: any;
  private A: any;
  private intersectionObserver: IntersectionObserver | undefined;
  private wasInView = false;

  @property()
  fov: number = 360;

  @property()
  projection: "MOL" = "MOL";

  @property({ type: Array })
  targets: Array<any> = [];

  @property({ type: Array })
  surveys: Array<Record<string, string>> = [];

  @property({ type: Object })
  moon: Record<string, number> = {
    ra: 0,
    dec: 0,
    illumination: 0,
  };

  @property({ type: Object })
  sun: Record<string, number> = {
    ra: 0,
    dec: 0,
  };

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
    this.intersectionObserver = this.setUpIntersectionObserver();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.intersectionObserver?.disconnect();
  }

  private init = false;

  initialize() {
    import("aladin-lite").then((A) => {
      this.A = A.default;
      this.A.init.then(() => {
        this.aladin = this.A.aladin(
          this.shadowRoot?.querySelector("#aladin-div"),
          {
            survey: "P/DSS2/color",
            fov: this.fov,
            projection: this.projection,
            showReticle: false,
            showCooGrid: true,
            showCooGridControl: true,
            log: false,
          },
        );
        const interval = setInterval(() => {
          const viewSizePix = this.aladin.getSize();
          if (viewSizePix[0] > 10 && !this.init) {
            this.init = true;
            clearInterval(interval);
            this.onReady();
          }
        }, 100);
      });
    });
  }

  setUpIntersectionObserver() {
    const target = this.shadowRoot?.querySelector("#aladin-div");
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          this.dispatchEvent(new CustomEvent("in-view"));
        }
      });
    });

    if (target) observer.observe(target);
    return observer;
  }

  onReady() {
    this.aladin.setCooGrid({ color: "grey", labelSize: 10 });

    if (this.moon) this.addMoon();
    if (this.sun) this.addSun();
    if (this.surveys.length > 0) this.addSurveys();
    if (this.targets.length > 0) this.addTargets();
  }

  addMoon() {
    // extract Moon information from the context
    const moonRaDeg = this.moon.ra;
    const moonDecDeg = this.moon.dec;
    const moonIllumination = Number(this.moon.illumination.toFixed(3));

    // get a unicode representation of the Moon based on illumination fraction
    let unicodeMoon: string;
    if (moonIllumination <= 0.125) {
      unicodeMoon = "\uD83C\uDF11";
    } else if (moonIllumination <= 0.375) {
      unicodeMoon = "\uD83C\uDF12";
    } else if (moonIllumination <= 0.625) {
      unicodeMoon = "\uD83C\uDF13";
    } else if (moonIllumination <= 0.875) {
      unicodeMoon = "\uD83C\uDF14";
    } else if (moonIllumination <= 1.0) {
      unicodeMoon = "\uD83C\uDF15";
    }

    // Create a text based symbol for the moon centered on the source coordinates
    var drawMoon = function (source: any, canvasCtx: CanvasRenderingContext2D) {
      canvasCtx.globalAlpha = 1;
      canvasCtx.font = "25px Arial";
      canvasCtx.fillStyle = "#eee";
      canvasCtx.textBaseline = "middle";
      canvasCtx.textAlign = "center";
      canvasCtx.fillText(unicodeMoon, source.x, source.y);
    };

    // create a catalog for the moon
    const moonImage = this.A.catalog({
      shape: drawMoon,
      color: "gray",
      name: "Moon",
    });

    const popupMoonDescription = `
            <div>Illumination: ${moonIllumination}</div>
            <div>RA: ${moonRaDeg.toFixed(4)}</div>
            <div>Dec: ${moonDecDeg.toFixed(4)}</div>
        `;

    moonImage.addSources([
      this.A.marker(moonRaDeg, moonDecDeg, {
        popupTitle: "Moon (Geocentric)",
        popupDesc: popupMoonDescription,
      }),
    ]);

    this.aladin.addCatalog(moonImage);
  }

  addSun() {
    // now add the sun in its own catalog
    const sunCatalog = this.A.catalog({
      name: "Sun",
      shape: "circle",
      color: "yellow",
      sourceSize: 30,
    }); // fontSize from Moon canvas plus 5 to match sizes

    const sunRaDeg = this.sun.ra;
    const sunDecDeg = this.sun.dec;

    const popupSunDescription = `
            <div>RA: ${sunRaDeg.toFixed(4)}</div>
            <div>Dec: ${sunDecDeg.toFixed(4)}</div>
        `;

    sunCatalog.addSources([
      this.A.marker(sunRaDeg, sunDecDeg, {
        popupTitle: "Sun (Geocentric)",
        popupDesc: popupSunDescription,
      }),
    ]);

    this.aladin.addCatalog(sunCatalog);
  }

  addSurveys() {
    for (const { name, url, color } of this.surveys) {
      const surveyDefinition = this.A.MOCFromURL(url, {
        lineWidth: 2,
        opacity: 0.3,
        color,
        name,
      });
      this.aladin.addMOC(surveyDefinition);
    }
  }

  addTargets() {
    for (const target of this.targets) {
      var targetCatalog = this.A.catalog({
        name: target.name,
        color: "blue",
        sourceSize: 16,
      });
      this.aladin.addCatalog(targetCatalog);
      const popupInfo = ["RA: ".concat(target.ra, "<br>", "Dec: ", target.dec)];
      targetCatalog.addSources([
        this.A.marker(target.ra, target.dec, {
          popupTitle: target.name,
          popupDesc: popupInfo,
        }),
      ]);
    }
  }

  render() {
    return html` <div id="aladin-div"></div> `;
  }
}
