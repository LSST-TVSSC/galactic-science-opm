import { css, html, LitElement, type PropertyValues, unsafeCSS } from "lit";
import type { LoadingIndicatorElement } from "../loading-indicator-element/LoadingIndicatorElement";
import "../loading-indicator-element/loading-indicator-element";
import { placeholder } from "./placeholder";

export class FinderChartElement extends LitElement {

  static styles = css`

    :host {
      display: block;
      position: relative;
      height: 100%;
    }

    .broken_image {
      font-size: 3rem;
    }

    :host .placeholder {
      position: absolute;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1;
      width: 100%;
      height: 100%;
      background-repeat: no-repeat;
      background-size: cover;
      background-image: url(${unsafeCSS(placeholder)});
      transition: 2s opacity;
    }

    :host .placeholder.loaded {
      opacity: 0;
    }

    .broken_image_container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-items: center;
      text-align: center;
      padding: 1rem;
    }

    :host .hidden {
      display: none;
    }

  `;

  private intersectionObserver: IntersectionObserver | undefined;
  private wasInView = false;
  private imgElement: HTMLImageElement | undefined;
  private src = "";

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

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.intersectionObserver?.disconnect();
  }

  protected firstUpdated(changedProperties: PropertyValues): void {
    super.firstUpdated(changedProperties);

    const slot = this.shadowRoot?.querySelector("slot");
    const container = slot
      ?.assignedNodes({ flatten: true })
      .find((n) => n.nodeName === "DIV") as HTMLImageElement;
    const img = (container.querySelector("img"));
    if (!img) {
      this.hideSpinner();
      return;
    }

    this.imgElement = img;
    if (this.imgElement.complete) {
      this.handleImageDone();
    }
    this.imgElement.addEventListener("error", () => {
      this.handleImageBroken()
    })
    this.imgElement.addEventListener("load", () => {
      this.handleImageDone();
    })

    this.src = this.imgElement.getAttribute("src") || ""
    this.imgElement.removeAttribute("src")

    this.intersectionObserver = this.setUpIntersectionObserver();
  }

  handleImageBroken() {
    this.hideSpinner();
    this.removeLoaded();
    this.showBrokenImage();
  }

  handleImageLoaded() {
    this.addLoaded()
  }
  
  removeLoaded() {
    const placeholder = this.shadowRoot?.querySelector<HTMLDivElement>(".placeholder")
    if (!placeholder) {
      return;
    }
    placeholder.classList.remove("loaded")
  }

  addLoaded() {
    const placeholder = this.shadowRoot?.querySelector<HTMLDivElement>(".placeholder")
    if (!placeholder) {
      return;
    }
    placeholder.classList.add("loaded")
  }

  handleImageDone() {
    this.hideSpinner()
    this.handleImageLoaded()
  }

  async initialize() {

    if (!this.imgElement) return;

    this.imgElement.setAttribute("src", this.src)
  }

  hideSpinner() {
    const loadingIndicator = this.shadowRoot?.querySelector<LoadingIndicatorElement>(
      "loading-indicator-element"
    )
    if (!loadingIndicator) {
      return;
    }
    loadingIndicator.hide();
  }

  hidePlaceholder() {
    const placeholder = this.shadowRoot?.querySelector<HTMLDivElement>(".placeholder")
    if (!placeholder) {
      return;
    }
    placeholder.classList.add("hidden")
  }

  showBrokenImage() {
    const brokenImage = this.shadowRoot?.querySelector<HTMLDivElement>(".broken_image_container")
    if (!brokenImage) {
      return;
    }
    brokenImage.classList.remove("hidden")
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
      <div class="placeholder">
        <loading-indicator-element></loading-indicator-element>
        <div class="broken_image_container hidden">
          <div class="broken_image">?</div>
          <p>Finder Chart could not be loaded</p>
        </div>
      </div>
      <slot></slot>
    `;
  }

}
