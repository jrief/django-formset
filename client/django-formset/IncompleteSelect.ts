
export abstract class IncompleteSelect {
	private readonly endpoint?: string;
	private readonly fieldName?: string;
	protected isIncomplete: boolean;
	protected readonly fieldGroup: Element;
	protected filterByValues = new Map<string, string>();

	constructor(element: HTMLSelectElement) {
		const fieldGroup = element.closest('django-field-group');
		const form = element.form;
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
		form.addEventListener('reset', event => this.formResetted(event));
		form.addEventListener('submitted', event => this.formSubmitted(event));
	}

	protected setupFilters(element: HTMLSelectElement) {
		const filters = element.getAttribute('filter-by')?.split(',') ?? [];
		filters.forEach(filterBy => {
			const observedElement = element.form?.elements.namedItem(filterBy);
			if (observedElement instanceof HTMLInputElement || observedElement instanceof HTMLSelectElement) {
				this.filterByValues.set(filterBy, observedElement.value);
				if (Array.from(this.filterByValues.values()).some(val => val)) {
					this.reloadOptions();
				}
				observedElement.addEventListener('change', (event: Event) => {
					const changedElement = event.currentTarget;
					if (changedElement instanceof HTMLInputElement || changedElement instanceof HTMLSelectElement) {
						this.filterByValues.set(filterBy, changedElement.value);
						this.reloadOptions();
					}
				});
			}
		});
	}

	protected abstract formResetted(event: Event) : void;

	protected abstract formSubmitted(event: Event) : void;

	protected abstract reloadOptions() : void;

	protected touch = () => {
		this.fieldGroup.classList.remove('dj-untouched', 'dj-validated');
		this.fieldGroup.classList.add('dj-touched');
	}

	protected buildFetchQuery(searchStr?: string) {
		const parts = [];
		if (searchStr) {
			parts.push(`search=${encodeURIComponent(searchStr)}`);
		}
		for (const [key, value] of this.filterByValues) {
			parts.push(`filter-${key}=${encodeURIComponent(value)}`);
		}
		return parts.join('&');
	}

	protected async loadOptions(query: string, successCallback: Function) {
		const headers = new Headers();
		headers.append('Accept', 'application/json');
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
			successCallback(data.options);
		} else {
			console.error(`Failed to fetch from ${url} (status=${response.status})`);
		}
	}
}
