import { html, css, LitElement } from "lit";
import { property } from "lit/decorators.js";

export class LoadingIndicatorElement extends LitElement {
  @property({ type: Object })

  static styles = css`
    :host {
      display: block;
    }
    .loader {
      --color-1: #fff;
      --color-2: #ff3d00;
      --size: 1px;

      width: calc(48 * var(--size));
      height: calc(48 * var(--size));
      border: calc(5 * var(--size)) solid var(--color-1);
      border-bottom-color: var(--color-2);
      border-radius: 50%;
      display: inline-block;
      box-sizing: border-box;
      animation: rotation 1s linear infinite;
    }

    @keyframes rotation {
      0% {
        transform: rotate(0deg);
      }
      100% {
        transform: rotate(360deg);
      }
    }

    .hidden {
      display: none;
    }

  `;
  private isReadyPromise: Promise<any>;
  private isReadyPromiseResolver: (...args: any) => void = () => {};
  constructor() {
    super();
    this.isReadyPromise = new Promise<void>((resolve) => {
      this.isReadyPromiseResolver = resolve;
    });
  }

  connectedCallback(): void {
    super.connectedCallback();
    this.isReadyPromiseResolver();
  }

  async wait() {
    return this.isReadyPromise;
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
  }

  async hide() {
    await this.wait();

    const el = this.shadowRoot?.querySelector("#loading-indicator")
    if (!el) {
      return;
    }
    el.classList.add("hidden")
  }

  show() {
    const el = this.shadowRoot?.querySelector("#loading-indicator")
    if (!el) return;
    el.classList.remove("hidden")
  }

  render() {
    return html`
      <span id="loading-indicator" class="loader"></span>
    `;
  }
}

