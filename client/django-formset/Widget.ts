export type ErrorKey = keyof ValidityState;


export class FieldErrorPlaceholder {
	private readonly messages: Map<ErrorKey, string> = new Map();
	private readonly fieldElement: FieldElement;
	private groupClassList: DOMTokenList;
	private readonly placeholder: Element;
	private readonly showFeedback: boolean;

	constructor(fieldElement: FieldElement) {
		this.fieldElement = fieldElement;
		const groupElement = fieldElement.closest('[role="group"]');
		const alertElement = Array.from(
			groupElement?.querySelectorAll('[role="alert"]') ?? []
		).find(alert => alert.closest('[role="group"]') === groupElement) ?? null;
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
		this.groupClassList = groupElement?.classList ?? new DOMTokenList();
		const placeholder = alertElement?.querySelector('.dj-errorlist > .dj-placeholder');
		if (!placeholder)
			throw new Error(`${fieldElement} requires a sibling element with role="alert" and an error placeholder`);
		this.placeholder = placeholder;
		this.showFeedback = fieldElement.closest('django-formset')?.getAttribute('withhold-feedback')?.split(' ').map(m => m.toLowerCase()).includes('messages') ? false : true;
	}

	private get showMessage() : boolean {
		return this.showFeedback && (this.groupClassList.contains('dj-submitted') || this.groupClassList.contains('dj-touched'));
	}

	public get showsError() : boolean {
		return this.placeholder.innerHTML.length !== 0;
	}

	public reportValidationError(): boolean {
		if (!this.fieldElement.validity.valid) {
			if (this.showMessage) {
				for (let [key, message] of this.messages.entries()) {
					if (key === 'tooShort' && (this.fieldElement.type === 'text' || this.fieldElement instanceof HTMLTextAreaElement)) {
						if (this.fieldElement.minLength > 0 && this.fieldElement.value.length < this.fieldElement.minLength) {
							this.placeholder.innerHTML = message ?? gettext("Entered text is too short.");
							break;
						}
					} else if (key === 'tooLong' && (this.fieldElement.type === 'text' || this.fieldElement instanceof HTMLTextAreaElement)) {
						if (this.fieldElement.maxLength > 0 && this.fieldElement.value.length > this.fieldElement.maxLength) {
							this.placeholder.innerHTML = message ?? gettext("Entered text is too long.");
							break;
						}
					} else if (this.fieldElement.validity[key as keyof ValidityState]) {
						this.placeholder.innerHTML = message;
						break;
					}
				}
			} else {
				this.placeholder.innerHTML = '';
			}
			return false;
		}
		this.placeholder.innerHTML = '';
		this.fieldElement.setCustomValidity('');
		return true;
	}

	public reportCustomError(message: string) {
		message = this.messages.get('customError') ?? message;
		this.fieldElement.setCustomValidity(message);
		if (this.showMessage) {
			this.placeholder.innerHTML = message;
		}
		return false;
	}

	public clearError() {
		this.placeholder.innerHTML = '';
		this.fieldElement.setCustomValidity('');
	}

	public getMessage(key: ErrorKey) : string|undefined {
		return this.messages.get(key);
	}
}


export abstract class Widget {
	public readonly endpoint: string | null;
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
