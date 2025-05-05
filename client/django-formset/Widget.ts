export type ErrorKey = keyof ValidityState;


export class FieldErrorPlaceholder {
	private readonly messages: Map<ErrorKey, string> = new Map();
	private readonly fieldElement: FieldElement;
	private readonly placeholder: Element;

	constructor(fieldElement: FieldElement) {
		this.fieldElement = fieldElement;
		let placeholder: Element|null|undefined = null;
		const groupElement = fieldElement.closest('[role="group"]');
		const alertElement = groupElement?.querySelector(':scope > [role="alert"]');
		const metaElement = alertElement?.querySelector('meta[name="error-messages"]');
		if (metaElement) {
			for (const attr of metaElement.getAttributeNames()) {
				const clientKey = attr.replace(/([_][a-z])/g, group => group.toUpperCase().replace('_', ''));
				const clientValue = metaElement.getAttribute(attr);
				if (clientValue) {
					this.messages.set(clientKey as ErrorKey, clientValue);
				}
			}
		}
		placeholder = alertElement?.querySelector('.dj-errorlist > .dj-placeholder');
		if (!placeholder)
			throw new Error(`${fieldElement} requires a sibling element with role="alert" and an error placeholder`);
		this.placeholder = placeholder;
	}

	public get showsError() : boolean {
		return this.placeholder.innerHTML.length !== 0;
	}

	public reportError(message?: string): boolean {
		if (message) {
			message = this.messages.get('customError') ?? message;
			this.placeholder.innerHTML = message;
			this.fieldElement.setCustomValidity(message);
			return false;
		}
		for (const [key, message] of this.messages.entries()) {
			if (this.fieldElement.validity[key as keyof ValidityState]) {
				this.placeholder.innerHTML = message;
				return false;
			}
		}
		if (this.fieldElement instanceof HTMLInputElement && this.fieldElement.type === 'text' || this.fieldElement instanceof HTMLTextAreaElement) {
			// browsers do not check for minLength and maxLength on bound fields
			if (this.fieldElement.minLength > 0 && this.fieldElement.value.length < this.fieldElement.minLength) {
				this.placeholder.innerHTML = this.messages.get('tooShort') ?? gettext("Entered text is too short");
				return false;
			}
			if (this.fieldElement.maxLength > 0 && this.fieldElement.value.length < this.fieldElement.maxLength) {
				this.placeholder.innerHTML = this.messages.get('tooLong') ?? gettext("Entered text is too long");
				return false;
			}
		}
		this.placeholder.innerHTML = '';
		this.fieldElement.setCustomValidity('');
		return true;
	}

	public clearError() {
		this.placeholder.innerHTML = '';
		this.fieldElement.setCustomValidity('');
	}
}


export abstract class Widget {
	protected readonly endpoint: string | null;
	protected readonly fieldName: string;
	protected readonly fieldGroup: Element;
	protected readonly errorPlaceholder: FieldErrorPlaceholder;

	constructor(element: HTMLInputElement|HTMLSelectElement) {
		const fieldGroup = element.closest('[role="group"]');
		const form = element.form;
		const formset = element.closest('django-formset');
		if (!fieldGroup || !form || !formset)
			throw new Error(`Attempt to initialize ${element} outside <django-formset>`);
		const formName = form.getAttribute('name') ?? '__default__';
		this.fieldGroup = fieldGroup;
		this.errorPlaceholder = new FieldErrorPlaceholder(element);
		this.endpoint = formset.getAttribute('endpoint');
		this.fieldName = `${formName}.${element.getAttribute('name')}`;
		form.addEventListener('reset', event => this.formResetted(event));
		form.addEventListener('submitted', event => this.formSubmitted(event));
	}

	protected abstract formResetted(event: Event) : void;

	protected abstract formSubmitted(event: Event) : void;
}
