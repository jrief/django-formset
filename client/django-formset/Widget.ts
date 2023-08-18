export type ErrorKey = keyof ValidityState;


export class FieldErrorMessages extends Map<ErrorKey, string>{
	constructor(fieldGroupElement: Element) {
		super();
		const element = fieldGroupElement.querySelector('meta[name="error-messages"]');
		if (!element)
			throw new Error(`${fieldGroupElement} requires one <meta name="error-messages"> tag.`);
		for (const attr of element.getAttributeNames()) {
			const clientKey = attr.replace(/([_][a-z])/g, (group) => group.toUpperCase().replace('_', ''));
			const clientValue = element.getAttribute(attr);
			if (clientValue) {
				this.set(clientKey as ErrorKey, clientValue);
			}
		}
	}
}


export abstract class Widget {
	protected readonly endpoint: string | null;
	protected readonly fieldName: string;
	protected readonly fieldGroup: Element;
	protected readonly errorMessages: FieldErrorMessages;

	constructor(element: HTMLInputElement | HTMLSelectElement) {
		const fieldGroup = element.closest('[role="group"]');
		const form = element.form;
		const formset = element.closest('django-formset');
		if (!fieldGroup || !form || !formset)
			throw new Error(`Attempt to initialize ${element} outside <django-formset>`);
		const formName = form.getAttribute('name') ?? '__default__';
		this.fieldGroup = fieldGroup;
		this.errorMessages = new FieldErrorMessages(fieldGroup);
		this.endpoint = formset.getAttribute('endpoint');
		this.fieldName = `${formName}.${element.getAttribute('name')}`;
		form.addEventListener('reset', event => this.formResetted(event));
		form.addEventListener('submitted', event => this.formSubmitted(event));
	}

	protected abstract formResetted(event: Event) : void;

	protected abstract formSubmitted(event: Event) : void;
}
