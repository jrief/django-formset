import TomSelect from 'tom-select/src/tom-select';
import TomSettings from 'tom-select/src/types/settings';
import {TomInput} from 'tom-select/src/types';

class DjangoSelectize {
	private readonly endpoint?: string;
	private readonly fieldName?: string;
	private readonly tomSelect?: TomSelect;

	constructor(tomInput: TomInput) {
		const form = tomInput.closest('form');
		const formset = tomInput.closest('django-formset');
		if (!form || !formset)
			return;
		// @ts-ignore
		const config: TomSettings = {
			create: false,
			valueField: 'id',
			labelField: 'label',
			searchField: 'label',
		};
		if (!tomInput.getAttribute('multiple')) {
			config.maxItems = 1;
		}
		if (tomInput.hasAttribute('uncomplete')) {
			this.endpoint = formset.getAttribute('endpoint') || '';
			const formName = form.getAttribute('name') || '__default__';
			this.fieldName = `${formName}.${tomInput.getAttribute('name')}`;
			config.load = (query: string, callback: Function) => this.loadOptions(query, callback);
		}
		this.tomSelect = new TomSelect(tomInput, config);
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
