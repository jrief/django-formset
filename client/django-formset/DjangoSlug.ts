import slug from 'slug';


export class DjangoSlugElement extends HTMLInputElement {
	private connectedCallback() {
		const populateFrom = this.getAttribute('populate-from');
		if (!populateFrom)
			throw new Error(`Field <input name="${this.name}" is="django-slug"> requires an attribute populate-from="..."`);
		const observedElement = this.form?.elements.namedItem(populateFrom);
		if (!(observedElement instanceof HTMLInputElement))
			throw new Error(`Field <input name="${populateFrom}"> is missing on this form.`);
		if (this.value === '') {
			observedElement.addEventListener('input', (event: Event) => {
				if (event.currentTarget instanceof HTMLInputElement) {
					this.value = slug(event.currentTarget.value);
				}
			});
		}
	}
}
