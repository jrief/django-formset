import getDataValue from 'lodash.get';
import setDataValue from 'lodash.set';
import template from 'lodash.template';

import { FileUploadWidget } from './FileUploadWidget';
import { parse } from './tag-attributes';
import styles from 'sass:./DjangoFormset.scss';
import spinnerIcon from './spinner.svg';
import okayIcon from './okay.svg';
import bummerIcon from './bummer.svg';

type FieldElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
type FieldValue = string | Array<string | Object>;
type ErrorKey = keyof ValidityState;

const NON_FIELD_ERRORS = '__all__';
const COLLECTION_ERRORS = '_collection_errors_';

const style = document.createElement('style');
style.innerText = styles;
document.head.appendChild(style);


function assert(condition: any, message?: string) {
	if (!condition) {
		message = message ? `Assertion failed: ${message}` : "Assertion failed";
		throw new Error(message);
	}
}


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


class FieldErrorMessages extends Map<ErrorKey, string>{
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
	public readonly element: HTMLElement;
	private readonly pristineValue: BoundValue;
	private readonly inputElements: Array<FieldElement>;
	private readonly initialDisabled: Array<boolean>;
	public readonly errorPlaceholder: Element | null;
	private readonly errorMessages: FieldErrorMessages;
	private readonly fileUploader: FileUploadWidget | null = null;
	private readonly updateVisibility: Function;
	private readonly updateDisabled: Function;

	constructor(form: DjangoForm, element: HTMLElement) {
		this.form = form;
		this.element = element;
		this.errorPlaceholder = element.querySelector('.dj-errorlist > .dj-placeholder');
		this.errorMessages = new FieldErrorMessages(this);
		const requiredAny = element.classList.contains('dj-required-any');
		const inputElements = (Array.from(element.getElementsByTagName('INPUT')) as Array<HTMLInputElement>).filter(e => e.name && e.type !== 'hidden');
		for (const element of inputElements) {
			switch (element.type) {
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
		const selectElements = (Array.from(element.getElementsByTagName('SELECT')) as Array<HTMLSelectElement>).filter(e => e.name);
		for (const element of selectElements) {
			element.addEventListener('focus', () => this.touch());
			element.addEventListener('change', () => {
				this.setDirty();
				this.clearCustomError();
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
		this.updateVisibility = this.evalVisibility('show-if', true) ?? this.evalVisibility('hide-if', false) ?? function() {};
		this.updateDisabled = this.evalDisable();
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

	public updateOperability() {
		this.updateVisibility();
		this.updateDisabled();
	}

	private evalVisibility(attribute: string, visible: boolean): Function | null {
		const attrValue = this.inputElements[0]?.getAttribute(attribute);
		if (typeof attrValue !== 'string')
			return null;
		try {
			const evalExpression = new Function('return ' + parse(attrValue, {startRule: 'Expression'}));
			return () => {
				const isHidden = visible != Boolean(evalExpression.call(this));
				if (this.element.hasAttribute('hidden') !== isHidden) {
					this.inputElements.forEach((elem, index) => elem.disabled = isHidden || this.initialDisabled[index]);
					this.element.toggleAttribute('hidden', isHidden);
				}
			};
		} catch (error) {
			throw new Error(`Error while parsing <... show-if/hide-if="${attrValue}">: ${error}.`);
		}
	}

	private evalDisable(): Function {
		const attrValue = this.inputElements[0]?.getAttribute('disable-if');
		if (typeof attrValue !== 'string')
			return () => {};
		try {
			const evalExpression = new Function('return ' + parse(attrValue, {startRule: 'Expression'}));
			return () => {
				const disable = evalExpression.call(this);
				this.inputElements.forEach((elem, index) => elem.disabled = disable || this.initialDisabled[index]);
			}
		} catch (error) {
			throw new Error(`Error while parsing <... disable-if="${attrValue}">: ${error}.`);
		}
	}

	getDataValue(path: Array<string>) {
		return this.form.getDataValue(path);
	}

	public inputted() {
		if (this.pristineValue.equals(this.aggregateValue())) {
			this.setPristine();
		} else {
			this.setDirty();
		}
		this.clearCustomError();
	}

	private clearCustomError() {
		this.form.clearCustomErrors();
		if (this.errorPlaceholder) {
			this.errorPlaceholder.innerHTML = '';
		}
		for (const element of this.inputElements) {
			if (element.validity.customError)
				element.setCustomValidity('');
		}
	}

	public resetToInitial() {
		if (this.fileUploader) {
			this.fileUploader.resetToInitial();
		}
		this.untouch();
		this.setPristine();
		this.clearCustomError();
	}

	public disableAllFields() {
		this.inputElements.forEach(elem => elem.disabled = true);
	}

	public reenableAllFields() {
		this.inputElements.forEach((elem, index) => elem.disabled = this.initialDisabled[index]);
	}

	public touch() {
		this.element.classList.remove('dj-untouched');
		this.element.classList.remove('dj-validated');
		this.element.classList.add('dj-touched');
	}

	private untouch() {
		this.element.classList.remove('dj-touched');
		this.element.classList.add('dj-untouched');
	}

	private setDirty() {
		this.element.classList.remove('dj-submitted');
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
					if (this.form.formset.showFeedbackMessages && this.errorPlaceholder) {
						this.errorPlaceholder.innerHTML = message;
					}
					element = null;
					break;
				}
			}
			if (this.form.formset.showFeedbackMessages && element instanceof HTMLInputElement) {
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
		} else if (this.pristineValue !== undefined && this.errorPlaceholder && this.form.formset.showFeedbackMessages) {
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
	private readonly decoratorElement: HTMLElement | null;
	private readonly spinnerElement: HTMLElement;
	private readonly okayElement: HTMLElement;
	private readonly bummerElement: HTMLElement;
	private originalDecorator?: Node;
	private timeoutHandler?: number;

	constructor(formset: DjangoFormset, element: HTMLButtonElement) {
		this.formset = formset;
		this.element = element;
		this.initialClass = element.getAttribute('class') ?? '';
		this.isAutoDisabled = !!JSON.parse((element.getAttribute('auto-disable') ?? 'false').toLowerCase());
		this.decoratorElement = element.querySelector('.dj-button-decorator');
		this.originalDecorator = this.decoratorElement?.cloneNode(true);
		this.spinnerElement = document.createElement('i');
		this.spinnerElement.classList.add('dj-icon', 'dj-spinner');
		this.spinnerElement.innerHTML = spinnerIcon;
		this.okayElement = document.createElement('i');
		this.okayElement.classList.add('dj-icon', 'dj-okay');
		this.okayElement.innerHTML = okayIcon;
		this.bummerElement = document.createElement('i');
		this.bummerElement.classList.add('dj-icon', 'dj-bummer');
		this.bummerElement.innerHTML = bummerIcon;
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

	// @ts-ignore
	private reload() {
		return (response: Response) => {
			location.reload();
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
					if (body.success_url) {
						location.href = body.success_url;
					} else if (typeof fallbackUrl === 'string') {
						location.href = fallbackUrl;
					} else {
						console.warn("Neither a success-, nor a fallback-URL is given to proceed.");
					}
				});
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

	/**
	 * Replace the button's decorator against a spinner icon.
	 */
	// @ts-ignore
	private spinner() {
		return (response: Response) => {
			this.decoratorElement?.replaceChildren(this.spinnerElement);
			return Promise.resolve(response);
		};
	}

	/**
	 * Replace the button's decorator against an okay animation.
	 */
	// @ts-ignore
	private okay(ms: number | undefined) {
		return this.decorate(this.okayElement, ms);
	}

	/**
	 * Replace the button's decorator against a bummer animation.
	 */
	// @ts-ignore
	private bummer(ms: number | undefined) {
		return this.decorate(this.bummerElement, ms);
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
	 * Clear all errors in the current django-formset.
 	 */
	// @ts-ignore
	private clearErrors() {
		return (response: Response) => {
			this.formset.clearErrors();
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

	// @ts-ignore
	private restore() {
		return () => {
			this.element.disabled = false;
			this.element.setAttribute('class', this.initialClass);
			if (this.originalDecorator) {
				this.decoratorElement?.replaceChildren(...this.originalDecorator.cloneNode(true).childNodes);
			}
		}
	}

	private decorate(decorator: HTMLElement, ms: number | undefined) {
		return (response: Response) => {
			this.decoratorElement?.replaceChildren(decorator);
			if (typeof ms !== 'number')
				return Promise.resolve(response);
			return new Promise(resolve => this.timeoutHandler = window.setTimeout(() => {
				this.timeoutHandler = undefined;
				resolve(response);
			}, ms));
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
			const ast = parse(actionsQueue, {startRule: 'Actions'});
			createActions(this.successActions, ast.successChain);
			createActions(this.rejectActions, ast.rejectChain);
		} catch (error) {
			throw new Error(`Error while parsing <button click="${actionsQueue}">: ${error}.`);
		}
	}

	public abortAction() {
		if (this.timeoutHandler) {
			clearTimeout(this.timeoutHandler);
			this.timeoutHandler = undefined;
		}
	}
}


class DjangoFieldset {
	public readonly form: DjangoForm;
	private readonly element: HTMLFieldSetElement;
	private readonly updateVisibility: Function;
	private readonly updateDisabled: Function;

	constructor(form: DjangoForm, element: HTMLFieldSetElement) {
		this.form = form;
		this.element = element;
		this.updateVisibility = this.evalVisibility('show-if', true) ?? this.evalVisibility('hide-if', false) ?? function() {};
		this.updateDisabled = this.evalDisable();
	}

	private evalVisibility(attribute: string, visible: boolean): Function | null {
		const attrValue = this.element.getAttribute(attribute);
		if (typeof attrValue !== 'string')
			return null;
		try {
			const evalExpression = new Function('return ' + parse(attrValue, {startRule: 'Expression'}));
			return () => {
				const isHidden = visible != Boolean(evalExpression.call(this));
				if (this.element.hasAttribute('hidden') !== isHidden) {
					this.element.toggleAttribute('hidden', isHidden);
				}
			}
		} catch (error) {
			throw new Error(`Error while parsing <fieldset show-if/hide-if="${attrValue}">: ${error}.`);
		}
	}

	private evalDisable(): Function {
		const attrValue = this.element.getAttribute('disable-if');
		if (typeof attrValue !== 'string')
			return () => {};
		try {
			const evalExpression = new Function('return ' + parse(attrValue, {startRule: 'Expression'}));
			return () => this.element.disabled = evalExpression.call(this);
		} catch (error) {
			throw new Error(`Error while parsing <fieldset disable-if="${attrValue}">: ${error}.`);
		}
	}

	private getDataValue(path: Array<string>) {
		return this.form.getDataValue(path);
	}

	updateOperability() {
		this.updateVisibility();
		this.updateDisabled();
	}
}


class DjangoForm {
	public readonly formId: string | null;
	public readonly name: string | null;
	public readonly path: Array<string>;
	public readonly formset: DjangoFormset;
	public readonly element: HTMLFormElement;
	public readonly fieldset: DjangoFieldset | null;
	private readonly errorList: Element | null = null;
	private readonly errorPlaceholder: Element | null = null;
	public readonly fieldGroups = Array<FieldGroup>(0);
	public readonly hiddenInputFields = Array<HTMLInputElement>(0);
	public markedForRemoval = false;

	constructor(formset: DjangoFormset, element: HTMLFormElement) {
		this.formId = element.getAttribute('id');
		this.name = element.getAttribute('name');
		this.path = this.name?.split('.') ?? [];
		this.formset = formset;
		this.element = element;
		const fieldsetElement = element.querySelector('fieldset');
		this.fieldset = fieldsetElement ? new DjangoFieldset(this, fieldsetElement) : null;
		const placeholder = element.querySelector('.dj-form-errors > .dj-errorlist > .dj-placeholder');
		if (placeholder) {
			this.errorList = placeholder.parentElement;
			this.errorPlaceholder = this.errorList!.removeChild(placeholder);
		}
	}

	aggregateValues(): Map<string, FieldValue> {
		const data = new Map<string, FieldValue>();
		for (const fieldGroup of this.fieldGroups) {
			data.set(fieldGroup.name, fieldGroup.aggregateValue());
		}
		// hidden fields are not handled by a django-field-group
		for (const element of this.hiddenInputFields.filter(e => e.type === 'hidden')) {
			data.set(element.name, element.value);
		}
		return data;
	}

	getDataValue(path: Array<string>) {
		const absPath = [];
		if (path[0] === '') {
			// path is relative, so concatenate it to the form's path
			absPath.push(...this.path);
			const relPath = path.filter(part => part !== '');
			const delta = path.length - relPath.length;
			absPath.splice(absPath.length - delta + 1);
			absPath.push(...relPath);
		} else {
			absPath.push(...path);
		}
		return this.formset.getDataValue(absPath);
	}

	updateOperability() {
		this.fieldset?.updateOperability();
		for (const fieldGroup of this.fieldGroups) {
			fieldGroup.updateOperability();
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

	clearCustomErrors() {
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

	toggleForRemoval(remove: boolean) {
		this.markedForRemoval = remove;
		for (const fieldGroup of this.fieldGroups) {
			if (remove) {
				fieldGroup.resetToInitial();
				fieldGroup.disableAllFields();
			} else {
				fieldGroup.reenableAllFields();
			}
		}
	}

	reportCustomErrors(errors: Map<string, Array<string>>) {
		this.clearCustomErrors();
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
	protected readonly formset: DjangoFormset;
	protected readonly element: Element;
	protected readonly parent?: DjangoFormCollection;
	protected readonly removeButton: HTMLButtonElement | null = null;
	protected forms = Array<DjangoForm>(0);
	public formCollectionTemplate?: DjangoFormCollectionTemplate;
	public readonly children = Array<DjangoFormCollection>(0);
	public markedForRemoval = false;

	constructor(formset: DjangoFormset, element: Element, parent?: DjangoFormCollection, justAdded?: boolean) {
		this.formset = formset;
		this.element = element;
		this.parent = parent;
		this.findFormCollections();
		this.removeButton = element.querySelector(':scope > button.remove-collection');
	}

	private findFormCollections() {
		// find all immediate elements <django-form-collection> of this DjangoFormCollection
		for (const childElement of this.element.querySelectorAll(':scope > django-form-collection')) {
			this.children.push(childElement.hasAttribute('sibling-position')
				? new DjangoFormCollectionSibling(this.formset, childElement, this)
				: new DjangoFormCollection(this.formset, childElement, this)
			);
		}
		for (const sibling of this.children) {
			sibling.updateRemoveButtonAttrs();
		}
		this.formCollectionTemplate = DjangoFormCollectionTemplate.findFormCollectionTemplate(this.formset, this.element, this);
	}

	public assignForms(forms: Array<DjangoForm>) {
		this.forms = forms.filter(form => form.element.parentElement?.isEqualNode(this.element));
		for (const formCollection of this.children) {
			formCollection.assignForms(forms);
		}
	}

	public updateRemoveButtonAttrs() {
		assert(this.removeButton === null, "Remove Button not removed");
	}

	protected toggleForRemoval(remove: boolean) {
		this.markedForRemoval = remove;
		for (const form of this.forms) {
			form.toggleForRemoval(remove);
		}
		for (const formCollection of this.children) {
			formCollection.toggleForRemoval(remove);
		}
		if (this.formCollectionTemplate) {
			this.formCollectionTemplate.markedForRemoval = remove;
			this.formCollectionTemplate.updateAddButtonAttrs();
		}
		if (this.removeButton) {
			this.removeButton.disabled = remove;
		}
		this.element.classList.toggle('dj-marked-for-removal', this.markedForRemoval);
	}

	public resetToInitial() {
		this.toggleForRemoval(false);
		for (const collection of this.children) {
			collection.resetToInitial();
		}
	}
}


class DjangoFormCollectionSibling extends DjangoFormCollection {
	public readonly position: number;
	private readonly minSiblings: number = 0;
	public readonly maxSiblings: number | null = null;
	private justAdded = false;

	constructor(formset: DjangoFormset, element: Element, parent?: DjangoFormCollection, justAdded?: boolean) {
		super(formset, element, parent);
		this.justAdded = justAdded ?? false;
		const position = element.getAttribute('sibling-position');
		if (!position)
			throw new Error("Missing argument 'sibling-position' in <django-form-collection>")
		this.position = parseInt(position);
		const minSiblings = element.getAttribute('min-siblings');
		if (!minSiblings)
			throw new Error("Missing argument 'min-siblings' in <django-form-collection>")
		this.minSiblings = parseInt(minSiblings);
		const maxSiblings = element.getAttribute('max-siblings');
		if (maxSiblings)
			this.maxSiblings = parseInt(maxSiblings);
		this.removeButton?.addEventListener('click', () => this.removeCollection());
	}

	private removeCollection() {
		if (this.justAdded) {
			this.element.remove();
			this.toggleForRemoval(true);
		} else {
			this.toggleForRemoval(!this.markedForRemoval);
		}
		const siblings = this.parent?.children ?? this.formset.formCollections;
		for (const sibling of siblings) {
			sibling.updateRemoveButtonAttrs();
		}
		const formCollectionTemplate = this.parent?.formCollectionTemplate ?? this.formset.formCollectionTemplate;
		formCollectionTemplate?.updateAddButtonAttrs();
	}

	updateRemoveButtonAttrs() {
		if (!this.removeButton)
			return;
		const siblings = this.parent?.children ?? this.formset.formCollections;
		const numActiveSiblings = siblings.filter(s => !s.markedForRemoval).length;
		if (this.markedForRemoval) {
			if (this.maxSiblings) {
				this.removeButton.disabled = numActiveSiblings >= this.maxSiblings;
			} else {
				this.removeButton.disabled = false;
			}
		} else {
			this.removeButton.disabled = numActiveSiblings <= this.minSiblings;
		}
	}

	public resetToInitial() {
		if (this.justAdded) {
			this.removeCollection();
		} else {
			super.resetToInitial();
		}
	}
}


class DjangoFormCollectionTemplate {
	private readonly formset: DjangoFormset;
	private readonly element: HTMLTemplateElement;
	private readonly parent?: DjangoFormCollection;
	private readonly renderEmptyCollection: Function;
	private readonly addButton?: HTMLButtonElement;
	private readonly baseContext = new Map<string, string>();
	public markedForRemoval = false;

	constructor(formset: DjangoFormset, element: HTMLTemplateElement, parent?: DjangoFormCollection) {
		this.formset = formset;
		this.element = element;
		this.parent = parent;
		const matches = element.innerHTML.matchAll(/\$\{([^} ]+)\}/g);
		for (const match of matches) {
			this.baseContext.set(match[1], match[0]);
		}
		this.renderEmptyCollection = template(element.innerHTML);
		if (element.nextElementSibling?.matches('button.add-collection')) {
			this.addButton = element.nextElementSibling as HTMLButtonElement;
			this.addButton.addEventListener('click', event => this.appendFormCollectionSibling());
		}
	}

	private appendFormCollectionSibling() {
		const context = Object.fromEntries(this.baseContext);
		context['position'] = (this.getHighestPosition() + 1).toString();
		// this context rewriting is necessary to render nested templates properly.
		// the hard-coded limit of 10 nested levels should be more than anybody ever will need
		context['position_1'] = '${position}'
		for (let k = 1; k < 10; ++k) {
			context[`position_${k + 1}`] = `$\{position_${k}\}`;
		}
		const renderedHTML = this.renderEmptyCollection(context);
		this.element.insertAdjacentHTML('beforebegin', renderedHTML);
		const newCollectionElement = this.element.previousElementSibling;
		if (!newCollectionElement)
			throw new Error("Unable to insert empty <django-form-collection> element.");
		const siblings = this.parent?.children ?? this.formset.formCollections;
		siblings.push(new DjangoFormCollectionSibling(this.formset, newCollectionElement, this.parent, true));
		this.formset.findForms(newCollectionElement);
		this.formset.assignFieldsToForms(newCollectionElement);
		this.formset.assignFormsToCollections();
		this.formset.validate();
		for (const sibling of siblings) {
			sibling.updateRemoveButtonAttrs();
		}
		this.updateAddButtonAttrs();
	}

	private getHighestPosition() : number {
		// look for the highest position number inside interconnected DjangoFormCollectionSiblings
		let position = -1;
		const children = this.parent ? this.parent.children : this.formset.formCollections;
		for (const sibling of children.filter(s => s instanceof DjangoFormCollectionSibling)) {
			position = Math.max(position, (sibling as DjangoFormCollectionSibling).position);
		}
		return position;
	}

	public updateAddButtonAttrs() {
		if (!this.addButton)
			return;
		if (this.markedForRemoval) {
			this.addButton.disabled = true;
			return;
		}
		const siblings = this.parent?.children ?? this.formset.formCollections;
		if (siblings.length === 0)
			return;
		assert(siblings[0] instanceof DjangoFormCollectionSibling, "Expected an instance of DjangoFormCollectionSibling");
		const maxSiblings = (siblings[0] as DjangoFormCollectionSibling).maxSiblings;
		const numActiveSiblings = siblings.filter(s => !s.markedForRemoval).length;
		this.addButton.disabled = maxSiblings === null ? false : numActiveSiblings >= maxSiblings;
	}

	static findFormCollectionTemplate(formset: DjangoFormset, element: Element, formCollection?: DjangoFormCollection) : DjangoFormCollectionTemplate | undefined {
		const templateElement = element.querySelector(':scope > template.empty-collection');
		if (templateElement) {
			const formCollectionTemplate = new DjangoFormCollectionTemplate(formset, templateElement as HTMLTemplateElement, formCollection);
			formCollectionTemplate.updateAddButtonAttrs();
			const prefix = templateElement.getAttribute('prefix');
			formset.emptyCollectionPathes.push(prefix ? prefix.split('.') : []);
			return formCollectionTemplate;
		}
	}
}


export class DjangoFormset {
	private readonly element: DjangoFormsetElement;
	private readonly buttons = Array<DjangoButton>(0);
	private readonly forms = Array<DjangoForm>(0);
	public readonly formCollections = Array<DjangoFormCollection>(0);
	public readonly collectionErrorsList = new Map<string, HTMLUListElement>();
	public readonly emptyCollectionPathes = Array<Array<string>>(0);
	public formCollectionTemplate?: DjangoFormCollectionTemplate;
	public readonly showFeedbackMessages: boolean;
	private readonly abortController = new AbortController;
	private data = {};

	constructor(formset: DjangoFormsetElement) {
		this.element = formset;
		this.showFeedbackMessages = this.parseWithholdFeedback();
	}

	connectedCallback() {
		this.findButtons();
		this.findForms();
		this.findFormCollections();
		this.findCollectionErrorsList();
		this.assignFieldsToForms();
		this.assignFormsToCollections();
		window.setTimeout(() => this.validate(), 0);
	}

	get endpoint(): string {
		return this.element.getAttribute('endpoint') ?? '';
	}

	get forceSubmission(): Boolean {
		return this.element.hasAttribute('force-submission');
	}

	private parseWithholdFeedback(): boolean {
		let showFeedbackMessages = true;
		const withholdFeedback = this.element.getAttribute('withhold-feedback')?.split(' ') ?? [];
		const feedbackClasses = new Set(['dj-feedback-errors', 'dj-feedback-warnings', 'dj-feedback-success']);
		for (const wf of withholdFeedback) {
			switch (wf.toLowerCase()) {
				case 'messages':
					showFeedbackMessages = false;
					break;
				case 'errors':
					feedbackClasses.delete('dj-feedback-errors');
					break;
				case 'warnings':
					feedbackClasses.delete('dj-feedback-warnings');
					break;
				case 'success':
					feedbackClasses.delete('dj-feedback-success');
					break;
				default:
					throw new Error(`Unknown value in <django-formset withhold-feedback="${wf}">.`);
			}
		}
		feedbackClasses.forEach(feedbackClass => this.element.classList.add(feedbackClass));
		return showFeedbackMessages;
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
		if (this.forms.length > 1) {
			for (const form of this.forms) {
				if (!form.name)
					throw new Error('Multiple <form>-elements in a <django-formset> require a unique name each.');
				if (form.name in formNames)
					throw new Error(`Detected more than one <form name="${form.name}"> in <django-formset>.`);
				formNames.push(form.name);
			}
		}
	}

	private findFormCollections() {
		// find all immediate elements <django-form-collection sibling-position="..."> belonging to the current <django-formset>
		for (const element of this.element.querySelectorAll(':scope > django-form-collection')) {
			this.formCollections.push(element.hasAttribute('sibling-position')
				? new DjangoFormCollectionSibling(this, element)
				: new DjangoFormCollection(this, element)
			);
		}
		for (const collection of this.formCollections) {
			collection.updateRemoveButtonAttrs();
		}
		this.formCollectionTemplate = DjangoFormCollectionTemplate.findFormCollectionTemplate(this, this.element);
	}

	private findCollectionErrorsList() {
		// find all elements <div class="dj-collection-errors"> belonging to the current <django-formset>
		for (const element of this.element.getElementsByClassName('dj-collection-errors')) {
			const prefix = element.getAttribute('prefix') ?? '';
			const ulElement = element.querySelector('ul.dj-errorlist') as HTMLUListElement;
			this.collectionErrorsList.set(prefix, ulElement);
		}
	}

	private findButtons() {
		this.buttons.length = 0;
		for (const element of this.element.getElementsByTagName('BUTTON')) {
			if (element.hasAttribute('click')) {
				this.buttons.push(new DjangoButton(this, element as HTMLButtonElement));
			}
		}
	}

	public assignFormsToCollections() {
		for (const collection of this.formCollections) {
			collection.assignForms(this.forms);
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
			const path = ['formset_data']
			if (form.name) {
				path.push(...form.name.split('.'));
			}
			setDataValue(this.data, path, Object.fromEntries(form.aggregateValues()));
		}
		for (const form of this.forms) {
			if (!form.markedForRemoval) {
				form.updateOperability();
			}
		}
	}

	public validate() {
		let isValid = true;
		for (const form of this.forms) {
			isValid = (form.markedForRemoval || form.checkValidity()) && isValid;
		}
		for (const button of this.buttons) {
			button.autoDisable(isValid);
		}
		this.aggregateValues();
		return isValid;
	}

	private buildBody(extraData?: Object) : Object {
		let dataValue: any;
		// Build `body`-Object recursively.
		// Deliberately ignore type-checking, because `body` must be build as POJO to be JSON serializable.
		function extendBody(entry: any, relPath: Array<string>) {
			if (relPath.length === 1) {
				// the leaf object
				if (Array.isArray(entry)) {
					entry.push(dataValue);
				} else {
					entry[relPath[0]] = dataValue;
				}
				return;
			}
			if (isNaN(parseInt(relPath[1]))) {
				const innerObject = entry[relPath[0]] ?? {};
				extendBody(innerObject, relPath.slice(1));
				if (Array.isArray(entry)) {
					const index = parseInt(relPath[0]);
					if (isNaN(index))
						throw new Error("Array without matching index.");
					entry[index] = {...entry[index], ...innerObject};
				} else {
					entry[relPath[0]] = innerObject;
				}
			} else {
				if (Array.isArray(entry))
					throw new Error("Invalid form structure: Contains nested arrays.");
				const innerArray = entry[relPath[0]] ?? [];
				if (!Array.isArray(innerArray))
					throw new Error("Invalid form structure: Inner array is missing.");
				extendBody(innerArray, relPath.slice(1));
				entry[relPath[0]] = innerArray;
			}
		}

		// Build a nested data structure (body) reflecting the shape of collections and forms
		const body = {};

		// Extend body with empty arrays from Form Collections with siblings
		for (const path of this.emptyCollectionPathes) {
			const absPath = ['formset_data', ...path];
			dataValue = getDataValue(body, absPath) ?? [];
			extendBody(body, absPath);
		}

		// Iterate over all forms and fill the data structure with content
		for (const form of this.forms) {
			if (!form.name)  // only a single form doesn't have a name
				return Object.assign({}, this.data, {_extra: extraData});

			if (!form.markedForRemoval) {
				const absPath = ['formset_data', ...form.path];
				dataValue = getDataValue(this.data, absPath);
				extendBody(body, absPath);
			}
		}

		// Extend data structure with extra data, for instance from buttons
		return Object.assign({}, body, {_extra: extraData});
	}

	async submit(extraData?: Object): Promise<Response | undefined> {
		let formsAreValid = true;
		this.setSubmitted();
		if (!this.forceSubmission) {
			for (const form of this.forms) {
				formsAreValid = (form.markedForRemoval || form.isValid()) && formsAreValid;
			}
		}
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
			const response = await fetch(this.endpoint, {
				method: 'POST',
				headers: headers,
				body: JSON.stringify(this.buildBody(extraData)),
				signal: this.abortController.signal,
			});
			switch (response.status) {
				case 200:
					this.clearErrors();
					for (const form of this.forms) {
						form.element.dispatchEvent(new Event('submitted'));
					}
					return response;
				case 422:
					this.clearErrors();
					const body = await response.json();
					this.reportErrors(body);
					return response;
				default:
					console.warn(`Unknown response status: ${response.status}`);
					break;
			}
		} else {
			this.clearErrors();
			for (const form of this.forms) {
				form.reportValidity();
			}
		}
	}

	private reportErrors(body: any) {
		for (const form of this.forms) {
			const errors = form.name ? getDataValue(body, form.name.split('.'), null) : body;
			if (errors) {
				form.reportCustomErrors(new Map(Object.entries(errors)));
				form.reportValidity();
			} else {
				form.clearCustomErrors();
			}
		}
		for (const [prefix, ulElement] of this.collectionErrorsList) {
			let path = prefix ? prefix.split('.') : [];
			path = [...path, '0', COLLECTION_ERRORS];
			for (const errorText of getDataValue(body, path, [])) {
				const placeholder = document.createElement('li');
				placeholder.classList.add('dj-placeholder');
				placeholder.innerText = errorText;
				ulElement.appendChild(placeholder);
			}
		}
	}

	public resetToInitial() {
		for (const collection of this.formCollections) {
			collection.resetToInitial();
		}
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

	public getDataValue(path: Array<string>) : string | null {
		const absPath = ['formset_data'];
		absPath.push(...path);
		return getDataValue(this.data, absPath, null);
	}

	findFirstErrorReport() : Element | null {
		for (const form of this.forms) {
			const errorReportElement = form.findFirstErrorReport();
			if (errorReportElement)
				return errorReportElement;
		}
		return null;
	}

	clearErrors() {
		for (const form of this.forms) {
			form.clearCustomErrors();
		}
		for (const ulElement of this.collectionErrorsList.values()) {
			while (ulElement.firstElementChild) {
				ulElement.removeChild(ulElement.firstElementChild);
			}
		}
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
		this[FS].connectedCallback();
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
