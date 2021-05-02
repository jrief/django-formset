import { html, LitElement, unsafeCSS } from 'lit';
import { property, query } from 'lit/decorators.js';

import styles from 'sass:./DjangoFormset.scss';
import getDataValue from 'lodash.get';
import template from 'lodash.template';
import { parse } from './actions';


export class Hello extends LitElement {
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
