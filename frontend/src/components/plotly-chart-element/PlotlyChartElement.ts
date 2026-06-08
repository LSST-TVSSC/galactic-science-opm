import { html, css, LitElement, type PropertyValues } from "lit";
import { property } from "lit/decorators.js";

export class PlotlyChartElement extends LitElement {
  @property({ type: Object })
  config: Record<string, any> | undefined = undefined;

  private intersectionObserver: IntersectionObserver | undefined;

  static styles = css`
    :host {
      display: block;
    }
  `;

  private wasInView = false;

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
    this.appendChild(div);

    const slot = this.shadowRoot?.querySelector("slot");
    const script = slot
      ?.assignedNodes({ flatten: true })
      .find((n) => n.nodeName === "SCRIPT");
    if (!script) {
      console.log("no script found. how to handle?");
      return;
    }
    const config = JSON.parse(script.textContent || '{"empty": true}');
    if (config.empty) {
      console.log("script was empty. how to handle?");
      return;
    }
    this.config = config;

    this.intersectionObserver = this.setUpIntersectionObserver();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.intersectionObserver?.disconnect();
  }

  async initialize() {
    // mkistner: aladin overrides `self` due to a bug in their code.
    // I have to reset it or plotly won't work anymore.
    window.self = window;

    if (!this.config) {
      console.log("how to handle this?");
      return;
    }
    import("plotly.js-dist-min").then(async (p) => {
      if (!this.config) {
        console.log("how to handle this?");
        return;
      }
      const plotly = p.default;
      const slot = this.shadowRoot?.querySelector("slot");
      const wrapper = slot
        ?.assignedNodes({ flatten: true })
        .find((n) => n.nodeName === "DIV");
      plotly.newPlot(wrapper, {
        data: this.config.data,
        layout: this.config.layout,
      });
    });
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

  render() {
    return html`<slot></slot>`;
  }
}
