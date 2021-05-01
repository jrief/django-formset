import { html, LitElement, property, unsafeCSS } from 'lit-element';
import styles from 'sass:./DjangoFormset.scss';

export class DjangoFormset extends LitElement {
	static styles = unsafeCSS(styles);

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
