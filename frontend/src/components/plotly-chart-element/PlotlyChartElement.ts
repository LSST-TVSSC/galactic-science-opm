import { html, css, LitElement, type PropertyValues } from "lit";
import { property } from "lit/decorators.js";

import "../loading-indicator-element/loading-indicator-element"
import type { LoadingIndicatorElement } from "../loading-indicator-element/LoadingIndicatorElement";

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
      // mkistner: Does this need further handling?
      this.hideSpinner();
      return;
    }
    const config = JSON.parse(script.textContent || '{"empty": true}');
    if (config.empty) {
      // mkistner: Does this need further handling?
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
      // mkistner: Does this need further handling?
      return;
    }
    import("plotly.js-dist-min").then(async (p) => {
      if (!this.config) {
        // mkistner: Does this need further handling?
        this.hideSpinner();
        return;
      }
      const plotly = p.default;
      const slot = this.shadowRoot?.querySelector("slot");
      const wrapper = slot
        ?.assignedNodes({ flatten: true })
        .find((n) => n.nodeName === "DIV");
      plotly.newPlot(wrapper, {
        data: this.config.data,
        layout: {...this.config.layout, autosize: true},
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
      <slot></slot>
    `;
  }
}
