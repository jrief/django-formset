import slug from 'slug';


export class DjangoSlugElement extends HTMLInputElement {
	connectedCallback() {
		const populateFrom = this.getAttribute('populate-from');
		if (!populateFrom)
			throw new Error(`Element ${this} requires an attribute populate-from="...".`);
		const observedElement = this.form?.elements.namedItem(populateFrom);
		if (!(observedElement instanceof HTMLInputElement))
			throw new Error(`Element <input name="${populateFrom}"> is missing on this form.`);
		if (this.value === '') {
			observedElement.addEventListener('input', this.setSlug);
		}
	}

	disconnectedCallback() {
		const populateFrom = this.getAttribute('populate-from') as string;
		const observedElement = this.form?.elements.namedItem(populateFrom) as HTMLInputElement;
		observedElement.removeEventListener('input', this.setSlug);
	}

	private setSlug = (event: Event) => {
		const observedElement = event.currentTarget as HTMLInputElement;
		const slugValue = slug(observedElement.value);
		if (this.value !== slugValue) {
			if (this.maxLength > 0) {
				this.value = slugValue.substring(0, this.maxLength);
			} else {
				this.value = slugValue;
			}
			this.dispatchEvent(new Event('input'));
		}
	};
}
