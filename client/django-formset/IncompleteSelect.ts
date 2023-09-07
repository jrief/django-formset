import { Widget } from './helpers';


export abstract class IncompleteSelect extends Widget {
	protected isIncomplete: boolean;
	protected getValue = () => [] as string|string[];
	private filterByValues = new Map<string, string | string[]>();

	constructor(element: HTMLSelectElement) {
		super(element);
		this.isIncomplete = element.hasAttribute('incomplete');
	}

	protected async setupFilters(element: HTMLSelectElement) {
		const filters = element.getAttribute('filter-by')?.split(',') ?? [];
		filters.forEach(filterBy => {
			const observedElement = element.form?.elements.namedItem(filterBy);
			if (observedElement instanceof HTMLInputElement) {
				this.filterByValues.set(filterBy, observedElement.value);
				observedElement.addEventListener('change', async (event: Event) => {
					const changedElement = event.currentTarget;
					if (changedElement instanceof HTMLInputElement) {
						this.filterByValues.set(filterBy, changedElement.value);
						await this.reloadOptions(true);
					}
				});
			} else if (observedElement instanceof HTMLSelectElement) {
				this.filterByValues.set(filterBy, Array.from(observedElement.selectedOptions).map(o => o.value));
				observedElement.addEventListener('change', async (event: Event) => {
					const changedElement = event.currentTarget;
					if (changedElement instanceof HTMLSelectElement) {
						this.filterByValues.set(filterBy, Array.from(observedElement.selectedOptions).map(o => o.value));
						await this.reloadOptions(true);
					}
				});
			}
		});
		if (Array.from(this.filterByValues.values()).some(val => (val as Array<string>).some(s => s))) {
			await this.reloadOptions();
		}
	}

	protected abstract formResetted(event: Event) : void;

	protected abstract formSubmitted(event: Event) : void;

	protected abstract reloadOptions(silent?: boolean) : Promise<void>;

	protected touch = () => {
		this.fieldGroup.classList.remove('dj-untouched', 'dj-validated');
		this.fieldGroup.classList.add('dj-touched');
	}

	protected buildFetchQuery(offset: number, searchStr?: string) : URLSearchParams {
		const query = new URLSearchParams();
		query.set('offset', String(offset));
		if (searchStr) {
			query.set('search', encodeURIComponent(searchStr));
		}
		for (const [key, value] of this.filterByValues) {
			if (typeof value === 'string') {
				query.set(`filter-${key}`, encodeURIComponent(value));
			} else if (Array.isArray(value)) {
				if (value.length === 0) {
					query.append(`filter-${key}`, '');
				} else {
					value.forEach(val => query.append(`filter-${key}`, encodeURIComponent(val)));
				}
			}
		}
		return query;
	}

	protected async loadOptions(query: URLSearchParams, successCallback: Function) {
		const headers = new Headers();
		headers.append('Accept', 'application/json');
		query.set('field', this.fieldName!);
		const response = await fetch(`${this.endpoint}?${query.toString()}`, {
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
			console.error(`Failed to fetch from ${this.endpoint} (status=${response.status})`);
		}
	}
}
