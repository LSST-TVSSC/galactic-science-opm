import { html, css, LitElement, type PropertyValues } from "lit";
import { property } from "lit/decorators.js";

import "../loading-indicator-element/loading-indicator-element"
import type { LoadingIndicatorElement } from "../loading-indicator-element/LoadingIndicatorElement";

export class PlotlyChartElement extends LitElement {
  @property({ type: Object })
  config: Record<string, any> | undefined = undefined;

  @property({ type: String })
  errorMessage: string = "";

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
      this.hideSpinner();
      this.errorMessage = this.generateDefaultErrorMessage();
      return;
    }
    const config = JSON.parse(script.textContent || '{"empty": true}');
    if (config.empty) {
      this.hideSpinner();
      this.errorMessage = this.generateDefaultErrorMessage();
      return;
    }
    this.config = config;

    this.intersectionObserver = this.setUpIntersectionObserver();
  }

  generateDefaultErrorMessage() {
    return "There was a problem loading the plot data.";
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
      this.hideSpinner();
      this.errorMessage = this.generateDefaultErrorMessage()
      return;
    }
    import("plotly.js-dist-min").then(async (p) => {
      if (!this.config) {
        this.hideSpinner();
        this.errorMessage = this.generateDefaultErrorMessage();
        return;
      }
      const plotly = p.default;
      const slot = this.shadowRoot?.querySelector("slot");
      const layout = {...this.config.layout, autosize: true}

      // mkistner: moves legend to bottom of the screen, so SED plot is not 
      // mkistner: squished by it.
      // mkistner: should probably be configurable at some point
      if (!layout.legend) layout.legend = {};
      layout.legend = {
        ...layout.legend,
        ...{
          orientation: 'h',
          x: 0.5,
          xanchor: 'center',
          y: -0.2,
          yanchor: 'top'
        }
      };

      const wrapper = slot
        ?.assignedNodes({ flatten: true })
        .find((n) => n.nodeName === "DIV");
      plotly.newPlot(wrapper, {
        data: this.config.data,
        layout,
        config: {
          responsive: true 
        }
      });
      (wrapper as any)?.on('plotly_afterplot', () => {
        this.hideSpinner();
      });

    });
  }

  hideSpinner() {
    const loadingIndicator = this.shadowRoot?.querySelector<LoadingIndicatorElement>("loading-indicator-element")
    if (!loadingIndicator) {
      return;
    }
    loadingIndicator.hide();
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
    return html`
      <loading-indicator-element></loading-indicator-element>
      <div>${this.errorMessage}</div>
      <slot></slot>
    `;
  }
}
