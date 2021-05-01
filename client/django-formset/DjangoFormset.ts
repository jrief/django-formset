import { html, css, LitElement, property } from 'lit-element';

export class DjangoFormset extends LitElement {
	static get styles() {
		return css`
			:host {
				display: block;
				padding: 30px;
				color: var(--django-formset3-text-color, #000);
			}
		`;
	}

	@property({ type: String }) title = 'Hey there';

	@property({ type: Number }) counter = 5;

	__increment() {
		this.counter += 1;
	}

	render() {
		return html`
			<h2>${this.title} Nr. ${this.counter}!</h2>
			<button @click=${this.__increment}>increment</button>
		`;
	}
}
