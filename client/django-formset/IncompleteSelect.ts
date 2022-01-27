
export abstract class IncompleteSelect {
	private readonly endpoint?: string;
	private readonly fieldName?: string;
	protected isIncomplete: boolean;
	protected readonly fieldGroup: Element;

	constructor(element: HTMLElement) {
		const fieldGroup = element.closest('django-field-group');
		const form = element.closest('form');
		const formset = element.closest('django-formset');
		if (!fieldGroup || !form || !formset)
			throw new Error("Attempt to initialize <django-selectize> outside <django-formset>");
		this.fieldGroup = fieldGroup;
		this.isIncomplete = element.hasAttribute('incomplete');
		if (this.isIncomplete) {
			// select fields marked as "uncomplete" will fetch additional data from their backend
			const formName = form.getAttribute('name') ?? '__default__';
			this.endpoint = formset.getAttribute('endpoint') ?? '';
			this.fieldName = `${formName}.${element.getAttribute('name')}`;
		}
		form.addEventListener('reset', (event: Event) => this.formResetted(event));
		form.addEventListener('submit', (event: Event) => this.formSubmitted(event));
	}

	abstract formResetted(event: Event) : void;

	abstract formSubmitted(event: Event) : void;

	protected get CSRFToken(): string | undefined {
		const value = `; ${document.cookie}`;
		const parts = value.split('; csrftoken=');

		if (parts.length === 2) {
			return parts[1].split(';').shift();
		}
	}

	protected async loadOptions(query: string, successCallback: Function) {
		const headers = new Headers();
		headers.append('Accept', 'application/json');
		const csrfToken = this.CSRFToken;
		if (csrfToken) {
			headers.append('X-CSRFToken', csrfToken);
		}
		const url = `${this.endpoint}?field=${this.fieldName}&${query}`;
		const response = await fetch(url, {
			method: 'GET',
			headers: headers,
		});
		if (response.status === 200) {
			const data = await response.json();
			if (typeof data.incomplete === 'boolean') {
				this.isIncomplete = data.incomplete;
			}
			successCallback(data.items);
		} else {
			console.error(`Failed to fetch from ${url}`);
		}
	}
}
