import styles from 'sass:./DjangoSelectize.scss';
import TomSelect from 'tom-select/src/tom-select';
import TomSettings from 'tom-select/src/types/settings';
import { TomInput } from 'tom-select/src/types';
import template from 'lodash.template';

const style = document.createElement('style');
style.textContent = styles;


class DjangoSelectize {
	private readonly endpoint?: string;
	private readonly fieldName?: string;
	private readonly tomSelect?: TomSelect;
	private readonly shadowRoot?: ShadowRoot;

	constructor(tomInput: TomInput) {
		const group = tomInput.closest('django-field-group');
		const form = tomInput.closest('form');
		const formset = tomInput.closest('django-formset');
		if (!group || !form || !formset)
			return;
		// @ts-ignore
		const config: TomSettings = {
			create: false,
			valueField: 'id',
			labelField: 'label',
			searchField: 'label',
			//optionClass: 'django-option',
			render: this.setupRender(tomInput),
		};
		if (!tomInput.getAttribute('multiple')) {
			config.maxItems = 1;
		}
		if (tomInput.hasAttribute('uncomplete')) {
			// select fields marked as "uncomplete" will fetch additional data from their backend
			const formName = form.getAttribute('name') || '__default__';
			this.endpoint = formset.getAttribute('endpoint') || '';
			this.fieldName = `${formName}.${tomInput.getAttribute('name')}`;
			config.load = (query: string, callback: Function) => this.loadOptions(query, callback);
		}
		this.tomSelect = new TomSelect(tomInput, config);
		const styles = this.extractStyles(tomInput);
		this.shadowRoot = this.wrapInShadowRoot(this.tomSelect.wrapper);
	}

	private wrapInShadowRoot(wrapper: HTMLElement) : ShadowRoot | undefined {
		const controlInput = wrapper.querySelector('.ts-input');
		const dropdown = wrapper.querySelector('.ts-dropdown');
		if (!controlInput || !dropdown)
			return;
		wrapper.removeChild(controlInput);
		wrapper.removeChild(dropdown);
		const shadowRoot = wrapper.attachShadow({mode: 'open', delegatesFocus: true});
		shadowRoot.appendChild(style);
		shadowRoot.appendChild(controlInput);
		shadowRoot.appendChild(dropdown);
		return shadowRoot;
	}

	private extractStyles(tomInput: TomInput) {
		const styles = getComputedStyle(tomInput);
		console.log(styles);
	}

	private setupRender(tomInput: TomInput): object {
		const renderes = new Map<string, Function>();
		const templates = tomInput.parentElement ? tomInput.parentElement.getElementsByTagName('template') : [];
		for (const tmpl of templates) {
			if (tmpl.classList.contains('selectize-no-results')) {
				const render = template(tmpl.innerHTML);
				renderes.set('no_results', (data: any, escape: Function) => render(data));
			}
		}
		return Object.fromEntries(renderes);
	}

	private async loadOptions(query: string, callback: Function) {
		const headers = new Headers();
		headers.append('Accept', 'application/json');
		const csrfToken = this.CSRFToken;
		if (csrfToken) {
			headers.append('X-CSRFToken', csrfToken);
		}
		const url = `${this.endpoint}?field=${this.fieldName}&query=${encodeURIComponent(query)}`;
		const response = await fetch(url, {
			method: 'GET',
			headers: headers,
		});
		if (response.status === 200) {
			response.json().then(data => {
				callback(data.items);
			});
		} else {
			console.error(`Failed to fetch from ${url}`);
		}
	}

	private get CSRFToken(): string | undefined {
		const value = `; ${document.cookie}`;
		const parts = value.split('; csrftoken=');

		if (parts.length === 2) {
			return parts[1].split(';').shift();
		}
	}
}

const DS = Symbol('DjangoSelectize');

export class DjangoSelectizeElement extends HTMLSelectElement {
	private [DS]: DjangoSelectize;  // hides internal implementation

	private connectedCallback() {
		this[DS] = new DjangoSelectize(this as unknown as TomInput);
	}
}
