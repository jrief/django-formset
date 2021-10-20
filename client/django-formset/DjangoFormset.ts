import { parse } from './actions';
import getDataValue from 'lodash.get';
import setDataValue from 'lodash.set';
import template from 'lodash.template';
import zip from 'lodash.zip';

import { FileUploadWidget } from './FileUploadWidget';

type FieldElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
type FieldValue = string | Array<string | Object>;
type ErrorKey = keyof ValidityState;

const NON_FIELD_ERRORS = '__all__'


class BoundValue {
	public readonly value: FieldValue;

	constructor(value: FieldValue) {
		this.value = value;
	}

	equals(other: FieldValue) {
		if (typeof this.value === 'string') {
			return this.value === other;
		} else {
			return this.value.length === other.length && this.value.every((val, index) => val === other[index]);
		}
	}
}


class ErrorMessages extends Map<ErrorKey, string>{
	constructor(fieldGroup: FieldGroup) {
		super();
		const element = fieldGroup.element.querySelector('django-error-messages');
		if (!element)
			throw new Error(`<django-field-group> for '${fieldGroup.name}' requires one <django-error-messages> tag.`);
		for (const attr of element.getAttributeNames()) {
			const clientKey = attr.replace(/([_][a-z])/g, (group) => group.toUpperCase().replace('_', ''));
			const clientValue = element.getAttribute(attr);
			if (clientValue) {
				this.set(clientKey as ErrorKey, clientValue);
			}
		}
	}
}


class FieldGroup {
	public readonly form: DjangoForm;
	public readonly name: string = '__undefined__';
	public readonly updateVisibility: Function;
	public readonly element: HTMLElement;
	private readonly pristineValue: BoundValue;
	private readonly inputElements: Array<FieldElement>;
	private readonly initialDisabled: Array<Boolean>;
	public readonly errorPlaceholder: Element | null;
	private readonly errorMessages: ErrorMessages;
	private readonly fileUploader: FileUploadWidget | null = null;

	constructor(form: DjangoForm, element: HTMLElement) {
		this.form = form;
		this.element = element;
		this.errorPlaceholder = element.querySelector('.dj-errorlist > .dj-placeholder');
		this.errorMessages = new ErrorMessages(this);
		const requiredAny = element.classList.contains('dj-required-any');
		const inputElements = (Array.from(element.getElementsByTagName('INPUT')) as Array<HTMLInputElement>).filter(element => element.type !== 'hidden');
		for (const element of inputElements) {
			if (element.getAttribute('is') === 'django-selectize') {
				element.addEventListener('focus', () => this.touch());
				element.addEventListener('change', () => {
					this.setDirty();
					this.resetCustomError();
					this.validate()
				});
			} else switch (element.type) {
				case 'checkbox':
				case 'radio':
					element.addEventListener('input', () => {
						this.touch();
						this.inputted()
					});
					element.addEventListener('change', () => {
						requiredAny ? this.validateCheckboxSelectMultiple() : this.validate()
					});
					break;
				case 'file':
					this.fileUploader = new FileUploadWidget(this, element);
					break;
				default:
					element.addEventListener('focus', () => this.touch());
					element.addEventListener('input', () => this.inputted());
					element.addEventListener('blur', () => this.validate());
					break;
			}
		}
		const selectElements = Array.from(element.getElementsByTagName('SELECT')) as Array<HTMLSelectElement>;
		for (const element of selectElements) {
			element.addEventListener('focus', () => this.touch());
			element.addEventListener('change', () => {
				this.setDirty();
				this.resetCustomError();
				this.validate()
			});
		}
		const textAreaElements = Array.from(element.getElementsByTagName('TEXTAREA')) as Array<HTMLTextAreaElement>;
		for (const element of textAreaElements) {
			element.addEventListener('focus', () => this.touch());
			element.addEventListener('input', () => this.inputted());
			element.addEventListener('blur', () => this.validate());
		}
		this.inputElements = Array<FieldElement>(0).concat(inputElements, selectElements, textAreaElements);
		for (const element of this.inputElements) {
			if (this.name === '__undefined__') {
				this.name = element.name;
			} else {
				if (this.name !== element.name)
					throw new Error(`Name mismatch on multiple input fields on ${element.name}`);
			}
		}
		this.initialDisabled = this.inputElements.map(element => element.disabled);
		if (requiredAny) {
			this.validateCheckboxSelectMultiple();
		} else {
			this.validateBoundField();
		}
		this.pristineValue = new BoundValue(this.aggregateValue());
		this.updateVisibility = this.parseIfAttribute('show-if', true) || this.parseIfAttribute('hide-if', false) || function() {};
		this.untouch();
		this.setPristine();
	}

	public aggregateValue(): FieldValue {
		if (this.inputElements.length === 1) {
			const element = this.inputElements[0];
			if (element.type === 'checkbox') {
				return (element as HTMLInputElement).checked ? element.value : '';
			}
			if (element.type === 'select-multiple') {
				const value = [];
				const select = element as HTMLSelectElement;
				for (const key in select.options) {
					if (select.options[key].selected) {
						value.push(select.options[key].value);
					}
				}
				return value;
			}
			if (element.type === 'file') {
				if (!this.fileUploader)
					throw new Error("fileUploader expected");
				return this.fileUploader.uploadedFiles;
			}
			// all other input types just return their value
			return element.value;
		} else {
			const value = [];
			for (let element of this.inputElements) {
				if (element.type === 'checkbox') {
					if ((element as HTMLInputElement).checked) {
						value.push(element.value);
					}
				} else if (element.type === 'radio') {
					if ((element as HTMLInputElement).checked)
						return element.value;
				}
			}
			return value;
		}
	}

	private parseIfAttribute(attribute: string, visible: boolean): Function {
		if (this.inputElements.length !== 1)
			return () => {};  // groups with multiple input elements are ignored
		const attrValue = this.inputElements[0].getAttribute(attribute);
		if (typeof attrValue !== 'string')
			return () => {};
		const path = attrValue.includes('.') ? attrValue : `${this.form.name}.${attrValue}`;
		if (visible) {
			return () => this.form.formset.getDataValue(path)
				? this.element.removeAttribute('hidden')
				: this.element.setAttribute('hidden', 'hidden');
		} else {
			return () => this.form.formset.getDataValue(path)
				? this.element.setAttribute('hidden', 'hidden')
				: this.element.removeAttribute('hidden');
		}
	}

	public inputted() {
		if (this.pristineValue.equals(this.aggregateValue())) {
			this.setPristine();
		} else {
			this.setDirty();
		}
		this.resetCustomError();
	}

	private resetCustomError() {
		this.form.resetCustomError();
		if (this.errorPlaceholder) {
			this.errorPlaceholder.innerHTML = '';
		}
		for (const element of this.inputElements) {
			if (element.validity.customError)
				element.setCustomValidity('');
		}
	}

	public resetToInitial() {
		this.untouch();
		this.setPristine();
		this.resetCustomError();
		if (this.fileUploader) {
			return this.fileUploader.fileRemove();
		}
	}

	public disableAllFields() {
		for (const element of this.inputElements) {
			element.disabled = true;
		}
	}

	public reenableAllFields() {
		for (const [element, disabled] of zip(this.inputElements, this.initialDisabled)) {
			if (element && typeof disabled === 'boolean') {
				element.disabled = disabled;
			}
		}
	}

	private touch() {
		this.element.classList.remove('dj-submitted');
		this.element.classList.remove('dj-untouched');
		this.element.classList.remove('dj-validated');
		this.element.classList.add('dj-touched');
	}

	private untouch() {
		this.element.classList.remove('dj-touched');
		this.element.classList.add('dj-untouched');
	}

	private setDirty() {
		this.element.classList.remove('dj-pristine');
		this.element.classList.add('dj-dirty');
	}

	private setPristine() {
		this.element.classList.remove('dj-dirty');
		this.element.classList.add('dj-pristine');
	}

	public setSubmitted() {
		this.element.classList.add('dj-submitted');
	}

	public validate() {
		let element: FieldElement | null = null;
		for (element of this.inputElements) {
			if (!element.validity.valid)
				break;
		}
		if (element && !element.validity.valid) {
			for (const [key, message] of this.errorMessages) {
				if (element.validity[key as keyof ValidityState]) {
					if (!this.form.formset.withholdMessages && this.errorPlaceholder) {
						this.errorPlaceholder.innerHTML = message;
					}
					element = null;
					break;
				}
			}
			if (!this.form.formset.withholdMessages && element instanceof HTMLInputElement) {
				this.validateInput(element);
			}
		}
		this.form.validate();
	}

	private validateCheckboxSelectMultiple() {
		let validity = false;
		for (const inputElement of this.inputElements) {
			if (inputElement.type !== 'checkbox')
				throw new Error("Expected input element of type 'checkbox'.");
			if ((inputElement as HTMLInputElement).checked) {
				validity = true;
			} else {
				inputElement.setCustomValidity(this.errorMessages.get('customError') ?? '');
			}
		}
		if (validity) {
			for (const inputElement of this.inputElements) {
				inputElement.setCustomValidity('');
			}
		} else if (this.pristineValue !== undefined && !this.form.formset.withholdMessages && this.errorPlaceholder) {
			this.errorPlaceholder.innerHTML = this.errorMessages.get('customError') ?? '';
		}
		this.form.validate();
		return validity;
	}

	private validateInput(inputElement: HTMLInputElement) {
		// By default, HTML input fields do not validate their bound value regarding their
		// min- and max-length. Therefore this validation must be performed by the client.
		if (inputElement.type === 'text' && inputElement.value) {
			if (inputElement.minLength > 0 && inputElement.value.length < inputElement.minLength) {
				if (this.errorPlaceholder) {
					this.errorPlaceholder.innerHTML = this.errorMessages.get('tooShort') ?? '';
				}
				return false;
			}
			if (inputElement.maxLength > 0 && inputElement.value.length > inputElement.maxLength) {
				if (this.errorPlaceholder) {
					this.errorPlaceholder.innerHTML = this.errorMessages.get('tooLong') ?? '';
				}
				return false;
			}
		}
		if (inputElement.type === 'file' && this.fileUploader) {
			if (this.fileUploader.inProgress()) {
				// seems that file upload is still in progress => field shall not be valid
				if (this.errorPlaceholder) {
					this.errorPlaceholder.innerHTML = this.errorMessages.get('typeMismatch') ?? '';
				}
				return false;
			}
		}
		return true;
	}

	private validateBoundField() {
		// By default, HTML input fields do not validate their bound value regarding their min-
		// and max-length. Therefore this validation must be performed separately.
		if (this.inputElements.length !== 1 || !(this.inputElements[0] instanceof HTMLInputElement))
			return;
		const inputElement = this.inputElements[0];
		if (!inputElement.value)
			return;
		if (inputElement.type === 'text') {
			if (inputElement.minLength > 0 && inputElement.value.length < inputElement.minLength)
				return inputElement.setCustomValidity(this.errorMessages.get('tooShort') ?? '');
			if (inputElement.maxLength > 0 && inputElement.value.length > inputElement.maxLength)
				return inputElement.setCustomValidity(this.errorMessages.get('tooLong') ?? '');
		}
	}

	public setValidationError(): boolean {
		let element: FieldElement | undefined;
		for (element of this.inputElements) {
			if (!element.validity.valid)
				break;
		}
		for (const [key, message] of this.errorMessages) {
			if (element && element.validity[key as ErrorKey]) {
				if (this.errorPlaceholder) {
					this.errorPlaceholder.innerHTML = message;
					element.setCustomValidity(message);
				}
				return false;
			}
		}
		if (element instanceof HTMLInputElement)
			return this.validateInput(element);
		return true;
	}

	public reportCustomError(message: string) {
		if (this.errorPlaceholder) {
			this.errorPlaceholder.innerHTML = message;
		}
		this.inputElements[0].setCustomValidity(message);
	}

	public reportFailedUpload() {
		if (this.errorPlaceholder) {
			this.errorPlaceholder.innerHTML = this.errorMessages.get('badInput') ?? "File upload failed";
		}
	}
}


class ButtonAction {
	constructor(func: Function, args: Array<any>) {
		this.func = func;
		this.args = args;
	}

	public readonly func: Function;
	public readonly args: Array<any>;
}


class DjangoButton {
	private readonly formset: DjangoFormset;
	private readonly element: HTMLButtonElement;
	private readonly initialClass: string;
	private readonly isAutoDisabled: boolean;
	private readonly successActions = Array<ButtonAction>(0);
	private readonly rejectActions = Array<ButtonAction>(0);
	private timeoutHandler?: number;

	constructor(formset: DjangoFormset, element: HTMLButtonElement) {
		this.formset = formset;
		this.element = element;
		this.initialClass = element.getAttribute('class') ?? '';
		this.isAutoDisabled = !!JSON.parse((element.getAttribute('auto-disable') ?? 'false').toLowerCase());
		this.parseActionsQueue(element.getAttribute('click'));
		element.addEventListener('click', () => this.clicked());
	}

	/**
	 * Event handler to be called when someone clicks on the button.
	 */
	// @ts-ignore
	private clicked() {
		let promise: Promise<Response> | undefined;
		for (const [index, action] of this.successActions.entries()) {
			if (!promise) {
				promise = action.func.apply(this, action.args)();
			} else {
				promise = promise.then(action.func.apply(this, action.args));
			}
		}
		if (promise) {
			for (const [index, action] of this.rejectActions.entries()) {
				if (index === 0) {
					promise = promise.catch(action.func.apply(this, action.args));
				} else {
					promise = promise.then(action.func.apply(this, action.args));
				}
			}
			promise.finally(this.restore.apply(this));
		}
	}

	public autoDisable(formValidity: Boolean) {
		if (this.isAutoDisabled) {
			this.element.disabled = !formValidity;
		}
	}

	/**
	 * Disable the button for further submission.
	 */
	// @ts-ignore
	private disable() {
		return (response: Response) => {
			this.element.disabled = true;
			return Promise.resolve(response);
		};
	}

	/**
	 * Re-enable the button for further submission.
	 */
	// @ts-ignore
	enable() {
		return (response: Response) => {
			this.element.disabled = false;
			return Promise.resolve(response);
		};
	}

	/**
	 * Validate form content and submit to the endpoint given in element `<django-formset>`.
	 */
	// @ts-ignore
	submit(data: Object | undefined) {
		return () => {
			return new Promise((resolve, reject) => {
				this.formset.submit(data).then(response =>
					response instanceof Response && response.status === 200 ? resolve(response) : reject(response)
				);
			});
		};
	}

	/**
	 * Reset form content to their initial values.
	 */
	// @ts-ignore
	reset() {
		return (response: Response) => {
			this.formset.resetToInitial();
			return Promise.resolve(response);
		};
	}

	/**
	 * Proceed to a given URL, if the response object returns status code 200.
	 * If the response object contains an element `success_url`, proceed to that URL,
	 * otherwise proceed to the given fallback URL.
	 *
	 * @param fallbackUrl: The URL to proceed to, for valid response objects without
	 * given success URL.
	 */
	// @ts-ignore
	private proceed(fallbackUrl: string | undefined) {
		return (response: Response) => {
			if (response instanceof Response && response.status === 200) {
				response.json().then(body => {
					if ('success_url' in body) {
						window.location.href = body.success_url;
					}
				});
				if (typeof fallbackUrl === 'string') {
					window.location.href = fallbackUrl;
				}
			}
			return Promise.resolve(response);
		}
	}

	/**
	 * Delay execution of the next task.
	 *
	 * @param ms: Time to wait in milliseconds.
	 */
	// @ts-ignore
	private delay(ms: number) {
		return (response: Response) => new Promise(resolve => this.timeoutHandler = window.setTimeout(() => {
			this.timeoutHandler = undefined;
			resolve(response);
		}, ms));
	}

	public abortAction() {
		if (this.timeoutHandler) {
			clearTimeout(this.timeoutHandler);
			this.timeoutHandler = undefined;
		}
	}

	/**
	 * Add a CSS class to the button element.
	 *
	 * @param cssClass: The CSS class.
	 */
	// @ts-ignore
	private addClass(cssClass: string) {
		return (response: Response) => {
			this.element.classList.add(cssClass);
			return Promise.resolve(response);
		};
	}

	/**
	 * Remove a CSS class from the button element.
	 *
	 * @param cssClass: The CSS class.
	 */
	// @ts-ignore
	private removeClass(cssClass: string) {
		return (response: Response) => {
			this.element.classList.remove(cssClass);
			return Promise.resolve(response);
		};
	}

	/**
	 * Add a CSS class to the button element or remove it if it is already set.
	 *
	 * @param cssClass: The CSS class.
	 */
	// @ts-ignore
	private toggleClass(cssClass: string) {
		return (response: Response) => {
			this.element.classList.toggle(cssClass);
			return Promise.resolve(response);
		};
	}

	/**
	 * Emit an event to the DOM.
	 *
	 * @param event: The named event.
	 */
	// @ts-ignore
	private emit(namedEvent: string, detail: Object | undefined) {
		return (response: Response) => {
			const options = {bubbles: true, cancelable: true};
			if (detail !== undefined) {
				Object.assign(options, {detail: detail});
				this.element.dispatchEvent(new CustomEvent(namedEvent, options));
			} else {
				this.element.dispatchEvent(new Event(namedEvent, options));
			}
			return Promise.resolve(response);
		};
	}

	/**
	 * For debugging purpose only: Intercept, log and forward the response object to the next handler.
 	 */
	// @ts-ignore
	private intercept() {
		return (response: Response) => {
			console.info(response);
			return Promise.resolve(response);
		}
	}

	/**
	 * Scroll to first element reporting an error.
 	 */
	// @ts-ignore
	private scrollToError() {
		return (response: Response) => {
			const errorReportElement = this.formset.findFirstErrorReport();
			if (errorReportElement) {
				errorReportElement.scrollIntoView({behavior: 'smooth'});
			}
			return Promise.resolve(response);
		}
	}

	/**
	 * Dummy action to be called in case of empty actionsQueue.
 	 */
	private noop() {
		return (response: Response) => {
			return Promise.resolve(response);
		}
	}

	private restore() {
		return () => {
			this.element.setAttribute('class', this.initialClass);
			this.element.disabled = false;
		}
	}

	private parseActionsQueue(actionsQueue: string | null) {
		if (!actionsQueue)
			return;

		let self = this;
		function createActions(actions: Array<ButtonAction>, chain: Array<any>) {
			for (let action of chain) {
				const func = self[action.funcname as keyof DjangoButton];
				if (typeof func !== 'function')
					throw new Error(`Unknown function '${action.funcname}'.`);
				actions.push(new ButtonAction(func, action.args));
			}
			if (actions.length === 0) {
				// the actionsQueue must resolve at least once
				actions.push(new ButtonAction(self.noop, []));
			}
		}

		try {
			const ast = parse(actionsQueue);
			createActions(this.successActions, ast.successChain);
			createActions(this.rejectActions, ast.rejectChain);
		} catch (error) {
			throw new Error(`Error while parsing <button click="...">: ${error}.`);
		}
	}
}


class DjangoForm {
	public readonly formId: string | null;
	public readonly name: string;
	public readonly formset: DjangoFormset;
	public readonly element: HTMLFormElement;
	private readonly errorList: Element | null;
	private readonly errorPlaceholder: Element | null;
	public readonly fieldGroups = Array<FieldGroup>(0);
	public readonly hiddenInputFields = Array<HTMLInputElement>(0);
	private markedForRemoval = false;

	constructor(formset: DjangoFormset, element: HTMLFormElement) {
		this.formId = element.getAttribute('id');
		this.name = element.getAttribute('name') ?? '__default__';
		this.formset = formset;
		this.element = element;
		const formError = element.querySelector('.dj-form-errors');
		const placeholder = formError ? formError.querySelector('.dj-errorlist > .dj-placeholder') : null;
		if (placeholder) {
			this.errorList = placeholder.parentElement;
			this.errorPlaceholder = this.errorList ? this.errorList.removeChild(placeholder) : null;
		} else {
			this.errorList = this.errorPlaceholder = null;
		}
	}

	aggregateValues(): Map<string, FieldValue> {
		const data = new Map<string, FieldValue>();
		for (const fieldGroup of this.fieldGroups) {
			data.set(fieldGroup.name, fieldGroup.aggregateValue());
		}
		// hidden fields are not handled by a django-field-group
		for (const element of this.hiddenInputFields) {
			if (element.type === 'hidden') {
				data.set(element.name, element.value);
			}
		}
		return data;
	}

	updateVisibility() {
		for (const fieldGroup of this.fieldGroups) {
			fieldGroup.updateVisibility();
		}
	}

	setSubmitted() {
		for (const fieldGroup of this.fieldGroups) {
			fieldGroup.setSubmitted();
		}
	}

	validate() {
		this.formset.validate();
	}

	isValid() {
		let isValid = true;
		for (const fieldGroup of this.fieldGroups) {
			isValid = fieldGroup.setValidationError() && isValid;
		}
		return isValid;
	}

	checkValidity() {
		return this.element.checkValidity();
	}

	reportValidity() {
		this.element.reportValidity();
	}

	resetCustomError() {
		while (this.errorList && this.errorList.lastChild) {
			this.errorList.removeChild(this.errorList.lastChild);
		}
	}

	resetToInitial() {
		this.element.reset();
		for (const fieldGroup of this.fieldGroups) {
			fieldGroup.resetToInitial();
		}
	}

	markForRemoval(removeForm: boolean) {
		this.markedForRemoval = removeForm;
		for (const fieldGroup of this.fieldGroups) {
			if (removeForm) {
				fieldGroup.disableAllFields();
			} else {
				fieldGroup.reenableAllFields();
			}
		}
	}

	reportCustomErrors(errors: Map<string, Array<string>>) {
		this.resetCustomError();
		const nonFieldErrors = errors.get(NON_FIELD_ERRORS);
		if (this.errorList && nonFieldErrors instanceof Array && this.errorPlaceholder) {
			for (const message of nonFieldErrors) {
				const item = this.errorPlaceholder.cloneNode() as Element;
				item.innerHTML = message;
				this.errorList.appendChild(item);
			}
		}
		for (const fieldGroup of this.fieldGroups) {
			const fieldErrors = errors.get(fieldGroup.name);
			if (fieldErrors instanceof Array && fieldErrors.length > 0) {
				fieldGroup.reportCustomError(fieldErrors[0]);
			}
		}
	}

	findFirstErrorReport() : Element | null {
		if (this.errorList?.textContent)
			return this.element;  // report a non-field error
		for (const fieldGroup of this.fieldGroups) {
			if (fieldGroup.errorPlaceholder?.textContent)
				return fieldGroup.element;
		}
		return null;
	}
}


class DjangoFormCollection {
	private readonly name: string | null;
	private readonly formset: DjangoFormset;
	private readonly element: Element;
	public readonly counter: number | null;
	private readonly children = Array<DjangoFormCollection>(0);
	private prevSibling: DjangoFormCollection | null = null;
	private nextSibling: DjangoFormCollection | null = null;
	private forms = Array<DjangoForm>(0);
	private readonly emptyCollectionTemplate: Function = () => {};
	private readonly addButton: HTMLButtonElement | null = null;
	private readonly removeButton: HTMLButtonElement | null = null;
	private markedForRemoval = false;

	constructor(formset: DjangoFormset, element: Element, prevSibling?: DjangoFormCollection) {
		this.formset = formset;
		this.element = element;
		const counter = element.getAttribute('counter');
		this.counter = counter ? parseInt(counter) : null;
		this.name = element.getAttribute('name');
		if (prevSibling) {
			prevSibling.nextSibling = this;
			this.prevSibling = prevSibling;
		}
		this.findFormCollections();
		console.log(`Initializing ${this.name}`);
		this.removeButton = element.querySelector(':scope > button.remove-collection');
		this.removeButton?.addEventListener('click', () => this.removeCollection());
		if (element.nextElementSibling?.matches('template.empty-collection')) {
			const emptyCollectionTemplate = element.nextElementSibling as HTMLTemplateElement;
			this.emptyCollectionTemplate = template(emptyCollectionTemplate.innerHTML);
			if (emptyCollectionTemplate.nextElementSibling?.matches('button.add-collection')) {
				this.addButton = emptyCollectionTemplate.nextElementSibling as HTMLButtonElement;
				this.addButton.addEventListener('click', event => this.addCollection());
			}
		}
	}

	private findFormCollections() {
		let prevSibling;
		for (const childElement of Array.from(this.element.getElementsByTagName('django-form-collection'))) {
			if (childElement.parentElement?.isEqualNode(this.element)) {
				prevSibling = new DjangoFormCollection(this.formset, childElement, prevSibling);
				this.children.push(prevSibling);
			}
		}
	}

	private addCollection() {
		console.log("Add collection");
		let counter = 0;
		let lastCollection: DjangoFormCollection | null = null;
		for (let last: DjangoFormCollection | null = this; last; last = last.nextSibling) {
			counter = Math.max(counter, last?.counter ?? 0);
			lastCollection = last;
		}
		const context = {
			counter: ++counter,
			content_type: '${content_type}',
			download_url: '${download_url}',
			thumbnail_url: '${thumbnail_url}',
			name: '${name}',
			size: '${size}'
		};
		if (lastCollection) {
			const renderedHTML = this.emptyCollectionTemplate(context);
			lastCollection.element.insertAdjacentHTML('afterend', renderedHTML);
			const newCollectionElement = lastCollection.element.nextElementSibling;
			if (newCollectionElement) {
				this.formset.findForms(newCollectionElement);
				this.formset.findFormCollections(newCollectionElement);
				this.formset.assignFieldsToForms(newCollectionElement);
				this.formset.assignFormsToCollections();
				this.formset.validate();
			}
		}
	}

	private removeCollection() {
		console.log(`remove collection ${this.name}`);
		this.markForRemoval(!this.markedForRemoval);
		if (this.removeButton) {
			this.removeButton.disabled = false;
		}
	}

	private markForRemoval(removeCollection: boolean) {
		this.markedForRemoval = removeCollection;
		if (this.removeButton) {
			this.removeButton.disabled = removeCollection;
		}
		for (const form of this.forms) {
			form.markForRemoval(removeCollection);
		}
		for (const formCollection of this.children) {
			formCollection.markForRemoval(removeCollection);
		}
		this.element.classList.toggle('dj-marked-for-removal', removeCollection);
	}

	public assignForms(forms: Array<DjangoForm>) {
		this.forms = forms.filter(form => form.element.parentElement?.isEqualNode(this.element));
		for (const formCollection of this.children) {
			formCollection.assignForms(forms);
		}
	}
}


export class DjangoFormset {
	private readonly element: DjangoFormsetElement;
	private readonly buttons = Array<DjangoButton>(0);
	private readonly forms = Array<DjangoForm>(0);
	private readonly formCollections = Array<DjangoFormCollection>(0);
	private readonly abortController = new AbortController;
	private data = {};

	constructor(formset: DjangoFormsetElement) {
		this.element = formset;
	}

	public get endpoint(): string {
		return this.element.getAttribute('endpoint') ?? '';
	}

	public get withholdMessages(): Boolean {
		return Boolean(JSON.parse(this.element.getAttribute('withhold-messages') ?? 'false'));
	}

	public get forceSubmission(): Boolean {
		return Boolean(JSON.parse(this.element.getAttribute('force-submission') ?? 'false'));
	}

	public assignFieldsToForms(parentElement?: Element) {
		parentElement = parentElement ?? this.element;
		for (const element of parentElement.querySelectorAll('INPUT, SELECT, TEXTAREA')) {
			const formId = element.getAttribute('form');
			let djangoForm: DjangoForm;
			if (formId) {
				const djangoForms = this.forms.filter(form => form.formId && form.formId === formId);
				if (djangoForms.length > 1)
					throw new Error(`More than one form has id="${formId}"`);
				if (djangoForms.length !== 1)
					continue;
				djangoForm = djangoForms[0];
			} else {
				const formElement = element.closest('form');
				if (!formElement)
					continue;
				const djangoForms = this.forms.filter(form => form.element === formElement);
				if (djangoForms.length !== 1)
					continue;
				djangoForm = djangoForms[0];
			}
			const fieldGroupElement = element.closest('django-field-group');
			if (fieldGroupElement) {
				if (djangoForm.fieldGroups.filter(fg => fg.element === fieldGroupElement).length === 0) {
					djangoForm.fieldGroups.push(new FieldGroup(djangoForm, fieldGroupElement as HTMLElement));
				}
			} else if (element.nodeName === 'INPUT' && (element as HTMLInputElement).type === 'hidden') {
				const hiddenInputElement = element as HTMLInputElement;
				if (!djangoForm.hiddenInputFields.includes(hiddenInputElement)) {
					djangoForm.hiddenInputFields.push(hiddenInputElement);
				}
			}
		}
	}

	public findForms(parentElement?: Element) {
		parentElement = parentElement ?? this.element;
		for (const element of parentElement.getElementsByTagName('FORM')) {
			const form = new DjangoForm(this, element as HTMLFormElement);
			this.forms.push(form);
		}
		this.checkForUniqueness();
	}

	private checkForUniqueness() {
		const formNames = Array<string>(0);
		for (const form of this.forms) {
			if (form.name in formNames)
				throw new Error(`Detected more than one <form name="${form.name}"> in <django-formset>`);
			formNames.push(form.name);
		}
	}

	public findFormCollections(parentElement?: Element) {
		parentElement = parentElement ?? this.element;
		for (const element of parentElement.getElementsByTagName('django-form-collection')) {
			if (element.parentElement?.isEqualNode(this.element)) {
				this.formCollections.push(new DjangoFormCollection(this, element));
			}
		}
	}

	public findButtons() {
		this.buttons.length = 0;
		for (const element of Array.from(this.element.getElementsByTagName('BUTTON'))) {
			if (element.hasAttribute('click')) {
				this.buttons.push(new DjangoButton(this, element as HTMLButtonElement));
			}
		}
	}

	public assignFormsToCollections() {
		for (const formCollection of this.formCollections) {
			formCollection.assignForms(this.forms);
		}
	}

	public get CSRFToken(): string | undefined {
		const value = `; ${document.cookie}`;
		const parts = value.split('; csrftoken=');

		if (parts.length === 2) {
			return parts[1].split(';').shift();
		}
	}

	private aggregateValues() {
		this.data = {};
		for (const form of this.forms) {
			const path = ['payload']
			path.push(...form.name.split('.'));
			setDataValue(this.data, path, Object.fromEntries(form.aggregateValues()));
		}
		for (const form of this.forms) {
			form.updateVisibility();
		}
	}

	public validate() {
		let isValid = true;
		for (const form of this.forms) {
			isValid = form.checkValidity() && isValid;
		}
		for (const button of this.buttons) {
			button.autoDisable(isValid);
		}
		this.aggregateValues();
		return isValid;
	}

	public async submit(extraData: Object | undefined): Promise<Response | undefined> {
		let formsAreValid = true;
		if (!this.forceSubmission) {
			for (const form of this.forms) {
				formsAreValid = form.isValid() && formsAreValid;
			}
		}
		this.setSubmitted();
		if (formsAreValid) {
			if (!this.endpoint)
				throw new Error("<django-formset> requires attribute 'endpoint=\"server endpoint\"' for submission");
			const headers = new Headers();
			headers.append('Accept', 'application/json');
			headers.append('Content-Type', 'application/json');
			const csrfToken = this.CSRFToken;
			if (csrfToken) {
				headers.append('X-CSRFToken', csrfToken);
			}
			const payload = Object.assign({}, this.data, {_extra: extraData});
			const response = await fetch(this.endpoint, {
				method: 'POST',
				headers: headers,
				body: JSON.stringify(payload),
				signal: this.abortController.signal,
			});
			if (response.status === 422) {
				const body = await response.json();
				for (const form of this.forms) {
					const errors = getDataValue(body, form.name.split('.'), null);
					if (errors) {
						form.reportCustomErrors(new Map(Object.entries(errors)));
						form.reportValidity();
					} else {
						form.resetCustomError();
					}
				}
			}
			return response;
		} else {
			for (const form of this.forms) {
				form.reportValidity();
			}
		}
	}

	public resetToInitial() {
		for (const form of this.forms) {
			form.resetToInitial();
		}
	}

	/**
	 * Abort the current actions.
	 */
	public abort() {
		for (const button of this.buttons) {
			button.abortAction();
		}
		this.abortController.abort();
	}

	private setSubmitted() {
		for (const form of this.forms) {
			form.setSubmitted();
		}
	}

	public getDataValue(path: string) : string | null{
		return getDataValue(this.data, path.split('.'), null);
	}

	findFirstErrorReport() : Element | null {
		for (const form of this.forms) {
			const errorReportElement = form.findFirstErrorReport();
			if (errorReportElement)
				return errorReportElement;
		}
		return null;
	}
}


const FS = Symbol('DjangoFormset');

export class DjangoFormsetElement extends HTMLElement {
	private readonly [FS]: DjangoFormset;  // hides internal implementation

	constructor() {
		super();
		this[FS] = new DjangoFormset(this);
	}

	private static get observedAttributes() {
		return ['endpoint', 'withhold-messages', 'force-submission'];
	}

	private connectedCallback() {
		this[FS].findButtons();
		this[FS].findForms();
		this[FS].findFormCollections();
		this[FS].assignFieldsToForms();
		this[FS].assignFormsToCollections();
		window.setTimeout(() => this[FS].validate(), 0);
	}

	public async submit(data: Object | undefined): Promise<Response | undefined> {
		return this[FS].submit(data);
	}

	public async abort() {
		return this[FS].abort();
	}

	public async reset() {
		return this[FS].resetToInitial();
	}
}
