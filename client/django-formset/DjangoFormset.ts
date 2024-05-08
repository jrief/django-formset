import getDataValue from 'lodash.get';
import setDataValue from 'lodash.set';
import isEqual from 'lodash.isequal';
import isEmpty from 'lodash.isempty';
import isPlainObject from 'lodash.isplainobject';
import template from 'lodash.template';
import Sortable, {SortableEvent} from 'sortablejs';
import {FileUploadWidget} from './FileUploadWidget';
import {FormDialog} from './FormDialog';
import {parse} from './tag-attributes';
import {ErrorKey, FieldErrorMessages} from './Widget';
import styles from './DjangoFormset.scss';
import spinnerIcon from './icons/spinner.svg';
import okayIcon from './icons/okay.svg';
import bummerIcon from './icons/bummer.svg';

type FieldElement = HTMLInputElement|HTMLSelectElement|HTMLTextAreaElement;
type FieldValue = string|Array<string|Object>;

const NON_FIELD_ERRORS = '__all__';
const COLLECTION_ERRORS = '_collection_errors_';
const MARKED_FOR_REMOVAL = '_marked_for_removal_';

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
}


class FieldGroup {
	public readonly form: DjangoForm;
	public readonly name: string;
	public readonly element: HTMLElement;
	private readonly pristineValue: BoundValue;
	private readonly fieldElements: Array<FieldElement>;
	private readonly initialDisabled: Array<boolean>;
	private readonly initialRequired: Array<boolean>;
	public readonly errorPlaceholder: Element|null;
	private readonly errorMessages: FieldErrorMessages;
	private readonly fileUploader?: FileUploadWidget;
	private readonly updateVisibility: Function;
	private readonly updateDisabled: Function;
	private readonly updateRequired: Function;

	constructor(form: DjangoForm, element: HTMLElement) {
		this.form = form;
		this.element = element;
		this.errorPlaceholder = element.querySelector('.dj-errorlist > .dj-placeholder');
		this.errorMessages = new FieldErrorMessages(element);
		const requiredAny = element.classList.contains('dj-required-any');

		// <div role="group"> can contain one or more <input type="checkbox"> or <input type="radio"> elements
		const allowedInputs = (i: Element) => i instanceof HTMLInputElement && i.name && i.form === form.element && i.type !== 'hidden';
		const inputElements = Array.from(element.getElementsByTagName('INPUT')).filter(allowedInputs) as Array<HTMLInputElement>;
		for (const element of inputElements) {
			switch (element.type) {
				case 'checkbox':
				case 'radio':
					element.addEventListener('input', () => {
						this.touch();
						this.inputted();
					});
					element.addEventListener('change', () => {
						requiredAny ? this.validateCheckboxSelectMultiple() : this.validate();
					});
					break;
				case 'file':
					// @ts-ignore
					this.fileUploader = new FileUploadWidget(this, element);
					element.addEventListener('invalid', () => this.showErrorMessage(element));
					break;
				default:
					element.addEventListener('focus', () => this.touch());
					element.addEventListener('input', () => this.inputted());
					element.addEventListener('blur', () => this.validate());
					element.addEventListener('invalid', () => this.showErrorMessage(element));
					break;
			}
		}
		this.fieldElements = Array<FieldElement>(0).concat(inputElements);

		// <div role="group"> can contain at most one <select> element
		const allowedSelects = (s: Element) => s instanceof HTMLSelectElement && s.name && s.form === form.element;
		const selectElement = Array.from(element.getElementsByTagName('SELECT')).filter(allowedSelects).at(0);
		if (selectElement instanceof HTMLSelectElement) {
			selectElement.addEventListener('focus', () => this.touch());
			selectElement.addEventListener('change', () => {
				this.setDirty();
				this.clearCustomError();
				this.validate();
			});
			selectElement.addEventListener('invalid', () => this.showErrorMessage(selectElement));
			this.fieldElements.push(selectElement);
		}

		// <div role="group"> can contain at most one <textarea> element
		const allowedTextAreas = (t: Element) => t instanceof HTMLTextAreaElement && t.name && t.form === form.element;
		const textAreaElement = Array.from(element.getElementsByTagName('TEXTAREA')).filter(allowedTextAreas).at(0);
		if (textAreaElement instanceof HTMLTextAreaElement) {
			textAreaElement.addEventListener('focus', () => this.touch());
			textAreaElement.addEventListener('input', () => this.inputted());
			textAreaElement.addEventListener('blur', () => this.validate());
			textAreaElement.addEventListener('invalid', () => this.showErrorMessage(textAreaElement));
			this.fieldElements.push(textAreaElement);
		}

		this.name = this.assertUniqueName();
		this.initialDisabled = this.fieldElements.map(element => element.disabled);
		this.initialRequired = this.fieldElements.map(element => element.required);
		if (requiredAny) {
			this.validateCheckboxSelectMultiple();
		} else {
			this.validateBoundField();
		}
		this.pristineValue = new BoundValue(this.aggregateValue());
		this.updateVisibility = this.evalVisibility('df-show', true) ?? this.evalVisibility('df-hide', false) ?? function() {};
		this.updateDisabled = this.evalDisable();
		this.updateRequired = this.evalRequire();
		this.untouch();
		this.setPristine();
	}

	public aggregateValue(): FieldValue {
		if (this.fieldElements.length === 1) {
			const element = this.fieldElements[0];
			if (element.type === 'checkbox') {
				return (element as HTMLInputElement).checked ? element.value : '';
			}
			if (element.type === 'select-multiple') {
				const select = element as HTMLSelectElement;
				return Array.from(select.selectedOptions).map(o => o.value);
			}
			if (element.type === 'file') {
				return this.fileUploader!.uploadedFiles;
			}
			if (element instanceof HTMLInputElement) {
				if (window.customElements.get('django-datefield') && element.getAttribute('is') === 'django-datefield'
				 || window.customElements.get('django-datecalendar') && element.getAttribute('is') === 'django-datecalendar'
				 || window.customElements.get('django-datepicker') && element.getAttribute('is') === 'django-datepicker')
					return element.valueAsDate?.toISOString().slice(0, 10) ?? '';
				if (window.customElements.get('django-datetimefield') && element.getAttribute('is') === 'django-datetimefield'
				 || window.customElements.get('django-datetimecalendar') && element.getAttribute('is') === 'django-datetimecalendar'
				 || window.customElements.get('django-datetimepicker') && element.getAttribute('is') === 'django-datetimepicker')
					return element.valueAsDate?.toISOString().replace('T', ' '). slice(0, 16) ?? '';
				if (window.customElements.get('django-daterangefield') && element.getAttribute('is') === 'django-daterangefield'
				 || window.customElements.get('django-daterangecalendar') && element.getAttribute('is') === 'django-daterangecalendar'
				 || window.customElements.get('django-daterangepicker') && element.getAttribute('is') === 'django-daterangepicker')
					return element.value ? element.value.split(';').map(v => v.slice(0, 10)) : ['', ''];
				if (window.customElements.get('django-datetimerangefield') && element.getAttribute('is') === 'django-datetimerangefield'
				 || window.customElements.get('django-datetimerangecalendar') && element.getAttribute('is') === 'django-datetimerangecalendar'
				 || window.customElements.get('django-datetimerangepicker') && element.getAttribute('is') === 'django-datetimerangepicker')
					return element.value ? element.value.split(';').map(v => v.slice(0, 16)) : ['', ''];
			}
			// all other input types just return their value
			return element.value;
		} else {
			const value = [];
			for (let element of this.fieldElements) {
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

	public setFieldValue(value: FieldValue) {
		if (this.fieldElements.length === 1) {
			const element = this.fieldElements[0];
			if (element.type === 'checkbox') {
				(element as HTMLInputElement).checked = value === element.value;
			} else if (element.type === 'select-multiple') {
				const select = element as HTMLSelectElement;
				const selectedOptions = Array.from(select.options).filter(o => (value as Array<string>).includes(o.value));
				for (const option of selectedOptions) {
					option.selected = true;
				}
			} else if (element.type !== 'file') {
				element.value = value as string;
			}
		} else {
			const values = value as Array<string>;
			for (let element of this.fieldElements) {
				if (element.type === 'checkbox') {
					(element as HTMLInputElement).checked = values.includes(element.value);
				}
			}
		}
		this.validate();
	}

	public updateOperability(action?: string) {
		this.updateVisibility();
		this.updateDisabled();
		this.updateRequired();
		this.fieldElements.filter(
			fieldElement => typeof (fieldElement as any).updateOperability === 'function'
		).forEach(
			fieldElement => (fieldElement as any).updateOperability(action)
		);
	}

	public disableRequiredConstraint() {
		this.fieldElements.forEach(fieldElement => fieldElement.required = false);
	}

	public restoreRequiredConstraint() {
		this.fieldElements.forEach((fieldElement, index) => fieldElement.required = this.initialRequired[index]);
	}

	private assertUniqueName() : string {
		let name = '__undefined__';
		for (const element of this.fieldElements) {
			if (name === '__undefined__') {
				name = element.name;
			} else {
				if (name !== element.name)
					throw new Error(`Duplicate name '${name}' on multiple input fields on '${element.name}'`);
			}
		}
		return name;
	}

	private evalVisibility(attribute: string, visible: boolean): Function|null {
		function isTruthy(expression: any) : boolean {
			// since empty arrays evaluate to true, implement separately to examine for existance
			// when using the file upload widget. Check https://262.ecma-international.org/5.1/#sec-11.9.3
			// for details.
			return Array.isArray(expression) ? expression.length !== 0 : Boolean(expression);
		}

		const attrValue = this.fieldElements[0]?.getAttribute(attribute);
		if (typeof attrValue !== 'string')
			return null;
		try {
			const evalExpression = new Function(`return ${parse(attrValue, {startRule: 'OperabilityExpression'})};`);
			return () => {
				const isHidden = visible != isTruthy(evalExpression.call(this));
				if (this.element.hasAttribute('hidden') !== isHidden) {
					this.fieldElements.forEach((elem, index) => elem.disabled = isHidden || this.initialDisabled[index]);
					this.element.toggleAttribute('hidden', isHidden);
				}
			};
		} catch (error) {
			throw new Error(`Error while parsing <... df-show/hide="${attrValue}">: ${error}.`);
		}
	}

	private evalDisable(): Function {
		const attrValue = this.fieldElements[0]?.getAttribute('df-disable');
		if (typeof attrValue !== 'string')
			return () => {};
		try {
			const evalExpression = new Function('return ' + parse(attrValue, {startRule: 'OperabilityExpression'}));
			return () => {
				const disable = evalExpression.call(this);
				this.fieldElements.forEach((elem, index) => elem.disabled = disable || this.initialDisabled[index]);
			}
		} catch (error) {
			throw new Error(`Error while parsing <... df-disable="${attrValue}">: ${error}.`);
		}
	}

	private evalRequire(): Function {
		const attrValue = this.fieldElements[0]?.getAttribute('df-require');
		if (typeof attrValue !== 'string')
			return () => {};
		try {
			const evalExpression = new Function('return ' + parse(attrValue, {startRule: 'OperabilityExpression'}));
			return () => {
				const require = evalExpression.call(this);
				this.fieldElements.forEach((elem, index) => elem.required = require && this.initialRequired[index]);
				this.form.checkValidity();
			}
		} catch (error) {
			throw new Error(`Error while parsing <... df-require="${attrValue}">: ${error}.`);
		}
	}

	private getDataValue(path: Array<string>) {
		return this.form.getDataValue(path);
	}

	public inputted() {
		if (isEqual(this.pristineValue, this.aggregateValue())) {
			this.setPristine();
		} else {
			this.setDirty();
		}
		this.clearCustomError();
		this.form.restoreRequiredConstraints();
	}

	private clearCustomError() {
		this.form.clearCustomErrors();
		if (this.errorPlaceholder) {
			this.errorPlaceholder.innerHTML = '';
		}
		for (const element of this.fieldElements) {
			if (element.validity.customError)
				element.setCustomValidity('');
		}
	}

	public resetToInitial() {
		this.fileUploader?.resetToInitial();
		this.untouch();
		this.setPristine();
		this.clearCustomError();
	}

	public disableAllFields() {
		this.fieldElements.forEach(elem => elem.disabled = true);
	}

	public reenableAllFields() {
		this.fieldElements.forEach((elem, index) => elem.disabled = this.initialDisabled[index]);
	}

	public touch() {
		this.element.classList.remove('dj-untouched', 'dj-validated');
		this.element.classList.add('dj-touched');
	}

	public untouch() {
		this.element.classList.remove('dj-submitted', 'dj-touched');
		this.element.classList.add('dj-untouched');
		if (this.errorPlaceholder) {
			this.errorPlaceholder.innerHTML = '';
		}
	}

	private setDirty() {
		this.element.classList.remove('dj-submitted', 'dj-pristine');
		this.element.classList.add('dj-dirty');
	}

	public setPristine() {
		this.element.classList.remove('dj-dirty');
		this.element.classList.add('dj-pristine');
	}

	public get isPristine() {
		return this.element.classList.contains('dj-pristine');
	}

	public get isTouched() {
		return this.element.classList.contains('dj-touched');
	}

	public setSubmitted() {
		this.element.classList.add('dj-submitted');
	}

	private showErrorMessage(element: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) {
		const submitted = this.element.classList.contains('dj-submitted');
		if (!(this.isTouched || submitted) || !this.form.formset.showFeedbackMessages || !this.errorPlaceholder)
			return;
		for (const [key, message] of this.errorMessages) {
			if (element.validity[key as keyof ValidityState]) {
				this.errorPlaceholder.innerHTML = message;
			}
		}
	}

	public validate() {
		let element: FieldElement|null = null;
		for (element of this.fieldElements) {
			if (element instanceof HTMLInputElement && element.hasAttribute('is')) {
				// input fields converted to web components may additionally validate themselves
				element.checkValidity();
			}
			if (!element.validity.valid)
				break;
		}
		if (element && !element.validity.valid) {
			element.dispatchEvent(new Event('invalid', {bubbles: true}));
			if (element instanceof HTMLInputElement && element.type === 'file') {
				this.validateFileInput(element, this.form.formset.showFeedbackMessages);
			}
		}
		this.form.validate();
	}

	private validateCheckboxSelectMultiple() {
		let validity = false;
		for (const inputElement of this.fieldElements) {
			if (inputElement.type !== 'checkbox')
				throw new Error("Expected input element of type 'checkbox'.");
			if ((inputElement as HTMLInputElement).checked) {
				validity = true;
			} else {
				inputElement.setCustomValidity(this.errorMessages.get('customError') ?? '');
			}
		}
		if (validity) {
			for (const inputElement of this.fieldElements) {
				inputElement.setCustomValidity('');
			}
		} else if (this.pristineValue !== undefined && this.errorPlaceholder && this.form.formset.showFeedbackMessages) {
			this.errorPlaceholder.innerHTML = this.errorMessages.get('customError') ?? '';
		}
		this.form.validate();
		return validity;
	}

	private validateFileInput(inputElement: HTMLInputElement, showFeedbackMessages: boolean): boolean {
		if (this.fileUploader!.inProgress()) {
			// seems that file upload is still in progress => field shall not be valid
			if (this.errorPlaceholder && showFeedbackMessages) {
				this.errorPlaceholder.innerHTML = this.errorMessages.get('typeMismatch') ?? '';
			}
			return false;
		}
		return true;
	}

	private validateBoundField() {
		// By default, HTML input fields do not validate their bound value regarding their min-
		// and max-length. Therefore, this validation must be performed separately.
		if (this.fieldElements.length !== 1 || !(this.fieldElements[0] instanceof HTMLInputElement))
			return;
		const inputElement = this.fieldElements[0];
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
		let element: FieldElement|null = null;
		for (element of this.fieldElements) {
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
		if (element instanceof HTMLInputElement && element.type === 'file')
			return this.validateFileInput(element, true);
		return true;
	}

	public reportCustomError(message: string) {
		if (this.errorPlaceholder) {
			this.errorPlaceholder.innerHTML = message;
		}
		this.fieldElements[0].setCustomValidity(message);
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

	readonly func: Function;
	readonly args: Array<any>;
}


class ActionChain {
	constructor(successChain: Array<ButtonAction>, rejectChain: Array<ButtonAction>) {
		this.successChain = successChain;
		this.rejectChain = rejectChain;
	}

	readonly successChain: Array<ButtonAction>;
	readonly rejectChain: Array<ButtonAction>;
}


class TernaryAction {
	constructor(condition: Function, fulfilled: TernaryAction|ActionChain, otherwise: TernaryAction|ActionChain) {
		this.condition = condition;
		this.fulfilled = fulfilled;
		this.otherwise = otherwise;
	}

	readonly condition: Function;
	readonly fulfilled: TernaryAction|ActionChain;
	readonly otherwise: TernaryAction|ActionChain;
}


class DjangoButton {
	private readonly formset: DjangoFormset;
	public readonly element: HTMLButtonElement;
	private readonly initialClass: string;
	private readonly isAutoDisabled: boolean;
	private clickHandler: Function = () => {};
	private readonly decoratorElement: HTMLElement|null;
	private readonly spinnerElement: HTMLElement;
	private readonly okayElement: HTMLElement;
	private readonly bummerElement: HTMLElement;
	public readonly path = Array<string>();
	private readonly updateVisibility: Function;
	private readonly updateDisabled: Function;
	private originalDecorator?: Node;
	private timeoutHandler?: number;

	constructor(formset: DjangoFormset, element: HTMLButtonElement, path: Array<string>) {
		this.formset = formset;
		this.element = element;
		this.initialClass = element.getAttribute('class') ?? '';
		this.isAutoDisabled = element.hasAttribute('auto-disable');
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
		this.path = path;
		this.parseActionsQueue(element.getAttribute('df-click'));
		this.updateVisibility = this.evalVisibility('df-show', true) ?? this.evalVisibility('df-hide', false) ?? function() {};
		this.updateDisabled = this.evalDisable();
		element.addEventListener('click', this.clicked);
	}

	private evalVisibility(attribute: string, visible: boolean): Function|null {
		const attrValue = this.element.getAttribute(attribute);
		if (attrValue === null)
			return null;
		try {
			const evalExpression = new Function(`return ${parse(attrValue, {startRule: 'OperabilityExpression'})}`);
			return () => {
				const isHidden = visible != Boolean(evalExpression.call(this));
				if (this.element.hasAttribute('hidden') !== isHidden) {
					this.element.toggleAttribute('hidden', isHidden);
				}
			}
		} catch (error) {
			throw new Error(`Error while parsing <button df-show/hide="${attrValue}">: ${error}.`);
		}
	}

	private evalDisable(): Function {
		const attrValue = this.element.getAttribute('df-disable');
		if (typeof attrValue !== 'string')
			return () => {};
		try {
			const evalExpression = new Function(`return ${parse(attrValue, {startRule: 'OperabilityExpression'})}`);
			return () => this.element.disabled = evalExpression.call(this);
		} catch (error) {
			throw new Error(`Error while parsing <button df-disable="${attrValue}">: ${error}.`);
		}
	}

	/**
	 * Event handler to be called when someone clicks on the button.
	 */
	// @ts-ignore
	private clicked = () => {
		this.clickHandler();
	};

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
	private enable() {
		return (response: Response) => {
			this.element.disabled = false;
			return Promise.resolve(response);
		};
	}

	/**
	 * Validate form content and submit to the endpoint given in element `<django-formset>`.
	 */
	// @ts-ignore
	submit(data?: Object) {
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
	private reload(includeQuery?: Boolean) {
		return (response: Response) => {
			includeQuery ? location.reload() : location.replace(window.location.pathname);
			// since the current page usually is reloaded before this promise resolves, add a delay
			// to prevent the restore handler from being called before the page is reloaded.
			return new Promise(resolve => window.setTimeout(() => resolve(response), 3000));
		};
	}

	/**
	 * Proceed to a given URL, if the response object returns status code 200.
	 * If the response object contains attribute `success_url`, proceed to that URL,
	 * otherwise proceed to the given fallback URL.
	 *
	 * @param proceedUrl (optional): If set, proceed to that URL regardless of the
	 * response status.
	 */
	// @ts-ignore
	private proceed(proceedUrl?: string) {
		return async (response: Response) => {
			if (typeof proceedUrl === 'string' && proceedUrl.length > 0) {
				location.href = proceedUrl;
			} else if (response instanceof Response && response.status === 200) {
				const body = await response.clone().json();
				if (body.success_url) {
					location.href = body.success_url;
				} else {
					console.warn("Neither a success-, nor a proceed-URL are given.");
				}
			}
			// since the new URL is usually loaded before this promise resolves, add a delay
			// to prevent the restore handler from being called before the new page is loaded.
			return new Promise(resolve => window.setTimeout(() => resolve(response), 3000));
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
	private okay(ms?: number) {
		return this.decorate(this.okayElement, ms);
	}

	/**
	 * Replace the button's decorator against a bummer animation.
	 */
	// @ts-ignore
	private bummer(ms?: number) {
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
	private emit(namedEvent: string, detail?: Object) {
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
	 * @param selector: If selector points onto a valid element in the DOM, the server response is inserted.
 	 */
	// @ts-ignore
	private intercept(selector?: string) {
		return async (response: Response) => {
			const body = {
				request: this.formset.buildBody(),
				response: await response.clone().json(),
			};
			const element = selector ? document.querySelector(selector) : null;
			if (element) {
				element.innerHTML = JSON.stringify(body, null,'  ');
			} else {
				console.info(body);
			}
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
	 * Confirm a user response. If it is accepted proceed, otherwise reject.
 	 */
	// @ts-ignore
	private confirm(message: string) {
		if (typeof message !== 'string')
			throw new Error("The confirm() action requires a message.")
		return (response: Response) => {
			if (window.confirm(message)) {
				return Promise.resolve(response);
			} else {
				return Promise.reject({});
			}
		}
	}

	/**
	 * Show an alert message with the response text for other types of errors, such as permission denied.
	 * This can be useful information to the end user in case the Django endpoint can not process a request.
 	 */
	// @ts-ignore
	private alertOnError() {
		return (response: Response) => {
			if (response.status !== 422) {
				window.alert(response.statusText);
			}
			return Promise.resolve(response);
		}
	}

	/**
	 * Action to activate a button so that it can be used
 	 */
	private activate(action?: string) {
		return (response: Response) => {
			this.formset.updateOperability(action);
			return Promise.resolve(response);
		}
	}

	/**
	 * Transfer value from one element to another one.
 	 */
	private setFieldValue(target: Array<string>, source: FieldValue) {
		return (response: Response) => {
			this.formset.setFieldValue(target, source);
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
	/*
	 * Called after all actions have been executed.
	 */
	private restore() {
		window.setTimeout(() => this.restoreToInitial());
	}

	private decorate(decorator: HTMLElement, ms?: number) {
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

	private setClickHandler(actions: TernaryAction|ActionChain) {
		const inner = (action: any) : any => {
			return action instanceof ButtonAction ? action.func.apply(this, action.args.map(inner)) : action;
		};

		const successHandler = (actions: Array<ButtonAction>) => {
			let promise: Promise<Response>|undefined;
			for (const action of actions.values()) {
				const next = action.func.apply(this, action.args.map(inner));
				promise = promise?.then(next) ?? next();
			}
			return promise;
		};

		const rejectHandler = (actions: Array<ButtonAction>, response: Response) => {
			let promise: Promise<Response>|undefined;
			for (const action of actions.values()) {
				const next = action.func.apply(this, action.args.map(inner));
				promise = promise?.then(next) ?? next(response);
			}
			return promise;
		};

		const actionHandler = (actions: ActionChain) => {
			successHandler(actions.successChain)?.then(() => {
				this.restore.apply(this);
			})?.catch((response: Response) => {
				rejectHandler(actions.rejectChain, response)?.finally(() => {
					this.restore.apply(this)
				});
			});
		};

		const ternaryHandler = (ternary: TernaryAction) => {
			if (ternary.condition.call(this)) {
				if (ternary.fulfilled instanceof ActionChain) {
					actionHandler(ternary.fulfilled);
				} else {
					ternaryHandler(ternary.fulfilled);
				}
			} else {
				if (ternary.otherwise instanceof ActionChain) {
					actionHandler(ternary.otherwise);
				} else {
					ternaryHandler(ternary.otherwise);
				}
			}
		};

		this.clickHandler = () => {
			if (actions instanceof ActionChain) {
				actionHandler(actions);
			} else {
				ternaryHandler(actions);
			}
		};
	}

	private parseActionsQueue(actionsQueue: string|null) {
		if (!actionsQueue)
			return;

		const innerAction = (action: any) => {
			if (isPlainObject(action)) {
				const func = this[action.funcname as keyof DjangoButton];
				if (typeof func !== 'function')
					throw new Error(`Unknown function '${action.funcname}'.`);
				return new ButtonAction(func, action.args.map(innerAction));
			}
			return action;
		};

		const createActions = (chain: Array<any>) => {
			const actions = chain.map(innerAction);
			if (actions.length === 0) {
				// each action queue must resolve at least once
				actions.push(new ButtonAction(this.noop, []));
			}
			return actions;
		};

		const createTernaries = (ternary: any) : TernaryAction|ActionChain => {
			if (ternary.condition === true)
				return new ActionChain(
					createActions(ternary.fulfilled.successChain),
					createActions(ternary.fulfilled.rejectChain)
				);

			return new TernaryAction(
				Function(ternary.condition),
				createTernaries(ternary.fulfilled),
				createTernaries(ternary.otherwise),
			);
		};

		try {
			const ast = parse(actionsQueue, {startRule: 'Ternary'});
			const actions = createTernaries(ast);
			this.setClickHandler(actions);
		} catch (error) {
			throw new Error(`Error while parsing <button df-click="${actionsQueue}">: ${error}.`);
		}
	}

	public restoreToInitial() {
		this.element.disabled = false;
		this.element.setAttribute('class', this.initialClass);
		if (this.originalDecorator) {
			this.decoratorElement?.replaceChildren(...this.originalDecorator.cloneNode(true).childNodes);
		}
	}

	private getDataValue(path: Array<string>) {
		return this.formset.getDataValue(path);
	}

	public updateOperability(action?: string) {
		this.updateVisibility();
		this.updateDisabled();
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
		this.updateVisibility = this.evalVisibility('df-show', true) ?? this.evalVisibility('df-hide', false) ?? function() {};
		this.updateDisabled = this.evalDisable();
	}

	private evalVisibility(attribute: string, visible: boolean): Function|null {
		const attrValue = this.element.getAttribute(attribute);
		if (attrValue === null)
			return null;
		try {
			const evalExpression = new Function(`return ${parse(attrValue, {startRule: 'OperabilityExpression'})}`);
			return () => {
				const isHidden = visible != Boolean(evalExpression.call(this));
				if (this.element.hasAttribute('hidden') !== isHidden) {
					this.element.toggleAttribute('hidden', isHidden);
				}
			}
		} catch (error) {
			throw new Error(`Error while parsing <fieldset df-show/hide="${attrValue}">: ${error}.`);
		}
	}

	private evalDisable(): Function {
		const attrValue = this.element.getAttribute('df-disable');
		if (typeof attrValue !== 'string')
			return () => {};
		try {
			const evalExpression = new Function(`return ${parse(attrValue, {startRule: 'OperabilityExpression'})}`);
			return () => this.element.disabled = evalExpression.call(this);
		} catch (error) {
			throw new Error(`Error while parsing <fieldset df-disable="${attrValue}">: ${error}.`);
		}
	}

	private getDataValue(path: Array<string>) : string|undefined {
		return this.form.getDataValue(path);
	}

	public updateOperability(action?: string) {
		this.updateVisibility();
		this.updateDisabled();
	}
}


class PerpetualFormDialog extends FormDialog {
	private readonly form: DjangoForm;

	constructor(form: DjangoForm, element: HTMLDialogElement) {
		super(element);
		this.form = form;
	}

	protected openDialog() {
		if (this.element.open)
			return;
		this.form.setPristine();
		this.form.untouch();
		super.openDialog();
 	}

	protected closeDialog(action: string) {
		switch (action) {
			case 'apply':
				if (this.form.isValid()) {
					this.element.close(action);
				}
				break;
			case 'cancel':
				this.element.close(action);
				break;
			case 'reset':
				this.form.resetToInitial();
				break;
			default:
				break;
		}
	}

	protected getDataValue(path: Array<string>) : string|undefined {
		return this.form.getDataValue(path);
	}

	protected isButtonActive(path: Array<string>, action: string): boolean {
		const absPath = path[0] !== '' ? path : (() => {
			// path is relative, so concatenate it to the form's path
			const absPath = [...this.form.path];
			const relPath = path.filter(part => part !== '');
			const delta = path.length - relPath.length;
			absPath.splice(absPath.length - delta + 1);
			absPath.push(...relPath);
			return absPath;
		})();
		const button = this.form.formset.buttons.find(button => isEqual(button.path, absPath));
		return action === 'active' && button?.element === document.activeElement;
	}
}


class DjangoForm {
	public readonly formset: DjangoFormset;
	public readonly element: HTMLFormElement;
	public readonly path: Array<string>;
	public readonly fieldset: DjangoFieldset|null;
	private readonly errorList: Element|null = null;
	private readonly errorPlaceholder: Element|null = null;
	public readonly fieldGroups = Array<FieldGroup>(0);
	public readonly hiddenInputFields = Array<HTMLInputElement>(0);
	public readonly parentDialog: PerpetualFormDialog|null = null;
	public readonly isTransient: boolean;
	public markedForRemoval = false;

	constructor(formset: DjangoFormset, element: HTMLFormElement) {
		this.formset = formset;
		this.element = element;
		this.path = this.name?.split('.') ?? [];
		const next = element.nextSibling;
		this.fieldset = next instanceof HTMLFieldSetElement && next.form === element ? new DjangoFieldset(this, next) : null;
		const placeholder = element.nextElementSibling?.querySelector('.dj-form-errors > .dj-errorlist > .dj-placeholder');
		if (placeholder) {
			this.errorList = placeholder.parentElement;
			this.errorPlaceholder = this.errorList!.removeChild(placeholder);
		}
		this.isTransient = Boolean(this.element.getAttribute('df-transient'));
		if (!this.isTransient) {
			const dialog = element.closest('dialog');
			this.parentDialog = dialog ? new PerpetualFormDialog(this, dialog) : null;
		}
		this.element.addEventListener('submit', this.handleSubmit);
		this.element.addEventListener('reset', this.handleReset);
	}

	aggregateValues(): Map<string, FieldValue> {
		const data = new Map<string, FieldValue>();
		for (const fieldGroup of this.fieldGroups) {
			data.set(fieldGroup.name, fieldGroup.aggregateValue());
		}
		// hidden fields are not handled by a <div role="group">
		for (const element of this.hiddenInputFields.filter(e => e.type === 'hidden')) {
			data.set(element.name, element.value);
		}
		return data;
	}

	public get name() : string|null {
		return this.element.getAttribute('name');
	}

	public get formId() : string|null {
		return this.element.getAttribute('id');
	}

	public getAbsPath() : Array<string> {
		return ['formset_data', ...this.path];
	}

	public getDataValue(path: Array<string>) {
		if (path[0] !== '')
			return this.formset.getDataValue(path);

		// path is relative, so concatenate it to the form's path
		const absPath = [...this.path];
		const relPath = path.filter(part => part !== '');
		const delta = path.length - relPath.length;
		absPath.splice(absPath.length - delta + 1);
		absPath.push(...relPath);
		return this.formset.getDataValue(absPath);
	}

	public setFieldValue(fieldName: string, value: any) {
		const fieldGroup = this.fieldGroups.find(group => group.name === fieldName);
		if (fieldGroup) {
			fieldGroup.setFieldValue(value);
		} else if (this.element.elements.namedItem(fieldName)) {
			(this.element.elements.namedItem(fieldName) as HTMLInputElement).value = value;
			this.formset.validate();
		} else {
			console.warn(`Field group '${fieldName}' not found.`);
		}
	}

	public updateOperability(action?: string) {
		this.fieldset?.updateOperability(action);
		this.fieldGroups.forEach(fieldGroup => fieldGroup.updateOperability(action));
		this.parentDialog?.updateOperability(action);
	}

	setSubmitted() {
		this.fieldGroups.forEach(fieldGroup => fieldGroup.setSubmitted());
	}

	validate() {
		this.formset.validate();
	}

	isValid() {
		if (this.element.noValidate)
			return true;
		let isValid = true;
		for (const fieldGroup of this.fieldGroups) {
			isValid = fieldGroup.setValidationError() && isValid;
		}
		return isValid;
	}

	checkValidity() {
		if (this.element.noValidate || this.isTransient)
			return true;
		return this.element.checkValidity();
	}

	reportValidity() {
		if (this.element.noValidate || this.isTransient)
			return;
		this.element.reportValidity();
	}

	clearCustomErrors() {
		while (this.errorList && this.errorList.lastChild) {
			this.errorList.removeChild(this.errorList.lastChild);
		}
	}

	resetToInitial() {
		this.element.reset();
	}

	private handleSubmit = (event: Event) => {
		if (event.target instanceof HTMLFormElement && event.target.method === 'dialog') {
			this.setSubmitted();
			return;
		}
		event.preventDefault();
	};

	private handleReset = () => {
		for (const fieldGroup of this.fieldGroups) {
			fieldGroup.resetToInitial();
		}
	};

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

	public findFirstErrorReport() : Element|null {
		if (this.errorList?.textContent)
			return this.element;  // report a non-field error
		for (const fieldGroup of this.fieldGroups) {
			if (fieldGroup.errorPlaceholder?.textContent)
				return fieldGroup.element;
		}
		return null;
	}

	public untouch() {
		this.fieldGroups.forEach(group => group.untouch());
	}

	public setPristine() {
		this.fieldGroups.forEach(group => group.setPristine());
	}

	public get isPristine() : boolean {
		return this.fieldGroups.every(group => group.isPristine);
	}

	public disableRequiredConstraints() {
		this.fieldGroups.forEach(fieldGroup => fieldGroup.disableRequiredConstraint());
	}

	public restoreRequiredConstraints() {
		this.fieldGroups.forEach(fieldGroup => fieldGroup.restoreRequiredConstraint());
	}
}


class DjangoFormCollection {
	protected readonly formset: DjangoFormset;
	protected readonly element: HTMLElement;
	protected readonly parent?: DjangoFormCollection;
	protected forms = Array<DjangoForm>(0);
	public formCollectionTemplate?: DjangoFormCollectionTemplate;
	public readonly children = Array<DjangoFormCollection>(0);
	public markedForRemoval = false;

	constructor(formset: DjangoFormset, element: HTMLElement, parent?: DjangoFormCollection) {
		this.formset = formset;
		this.element = element;
		this.parent = parent;
		this.findFormCollections();
	}

	private findFormCollections() {
		// find all immediate elements <django-form-collection ...> belonging to the current <django-form-collection>
		for (const childElement of DjangoFormCollection.getChildCollections(this.element)) {
			this.children.push(new DjangoFormCollection(this.formset, childElement, this));
		}
		for (const [siblingId, childElement] of DjangoFormCollection.getChildSiblingsCollections(this.element).entries()) {
			this.children.push(new DjangoFormCollectionSibling(this.formset, childElement, siblingId, this));
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

	public updateRemoveButtonAttrs() {}

	protected disconnect() {
		this.forms.forEach(form => this.formset.removeForm(form));
		this.children.forEach(child => child.disconnect());
		this.formCollectionTemplate?.disconnect();
		this.element.remove();
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
		this.element.classList.toggle('dj-marked-for-removal', this.markedForRemoval);
	}

	protected resetToInitial() : boolean {
		this.toggleForRemoval(false);
		DjangoFormCollection.resetCollectionsToInitial(this.children);
		if (this.formCollectionTemplate) {
			const prefix = this.formCollectionTemplate.prefix;
			const pathIndex = prefix === '0' ? 0 : prefix.split('.').length;
			this.children.forEach((sibling, position) => sibling.repositionForms(pathIndex, position));
			this.formCollectionTemplate.updateAddButtonAttrs();
		}
		return false;
	}

	public repositionSiblings() {}

	public repositionForms(pathIndex: number, pathPart: number) {
		this.forms.forEach(form => {
			form.path[pathIndex] = String(pathPart);
			form.element.setAttribute('name', form.path.join('.'));
		});
		this.children.forEach(child => child.repositionForms(pathIndex, pathPart));
	}

	public markAsFreshAndEmpty(justAdded?: boolean) {
		this.children.forEach(child => child.markAsFreshAndEmpty(justAdded));
		if (justAdded) {
			this.forms.forEach(form => form.disableRequiredConstraints());
		}
	}

	public restoreRequiredConstraint() {
		this.forms.forEach(form => form.restoreRequiredConstraints());
		this.children.forEach(child => child.restoreRequiredConstraint());
	}

	public get isFreshAndEmpty() : boolean {
		return this.forms.every(form => form.isPristine) && this.children.every(child => child.isFreshAndEmpty);
	}

	public removeFreshAndEmpty() {
		const children = Array.from(this.children).reverse();
		children.forEach(child => child.removeFreshAndEmpty());
	}

	static getChildCollections(element: Element) : NodeListOf<HTMLElement> | [] {
		// traverse tree to find first occurrence of a <django-form-collection> and if so, return it with its siblings
		const wrapper = element.querySelector('django-form-collection')?.parentElement;
		return wrapper ? wrapper.querySelectorAll(':scope > django-form-collection:not([sibling-position])') : [];
	}

	static getChildSiblingsCollections(element: Element) : NodeListOf<HTMLElement> | [] {
		// traverse tree to find first occurrence of a <django-form-collection> and if so, return it with its siblings
		const wrapper = element.querySelector('django-form-collection')?.parentElement;
		return wrapper ? wrapper.querySelectorAll(':scope > django-form-collection[sibling-position]') : [];
	}

	static resetCollectionsToInitial(formCollections: Array<DjangoFormCollection>) {
		const removeCollections = Array<DjangoFormCollection>(0);
		for (const collection of formCollections) {
			if (collection.resetToInitial()) {
				removeCollections.push(collection);
			}
		}
		removeCollections.forEach(collection => formCollections.splice(formCollections.indexOf(collection), 1));
		formCollections.sort((l, r) => {
			return l instanceof DjangoFormCollectionSibling && r instanceof DjangoFormCollectionSibling ? l.initialPosition - r.initialPosition : 0;
		});

		// undo DOM sorting previously changed by SortableJS
		let prevElement: HTMLElement|null = null;
		for (const collection of formCollections) {
			if (collection instanceof DjangoFormCollectionSibling) {
				if (collection.initialPosition === 0) {
					collection.element.parentElement?.insertAdjacentElement('afterbegin', collection.element);
				} else {
					prevElement?.insertAdjacentElement('afterend', collection.element);
				}
				prevElement = collection.element;
			}
		}
		formCollections.forEach(collection => collection.repositionSiblings());
	}
}


class DjangoFormCollectionSibling extends DjangoFormCollection {
	public position: number;
	public readonly initialPosition: number;
	public readonly siblingId: number = 0;
	private readonly minSiblings: number = 0;
	public readonly maxSiblings: number|null = null;
	private readonly removeButton: HTMLButtonElement;
	private justAdded = false;

	constructor(formset: DjangoFormset, element: HTMLElement, siblingId: number, parent?: DjangoFormCollection) {
		super(formset, element, parent);
		const position = element.getAttribute('sibling-position');
		if (!position)
			throw new Error("Missing argument 'sibling-position' in <django-form-collection>")
		this.position = this.initialPosition = parseInt(position);
		this.siblingId = siblingId;
		const minSiblings = element.getAttribute('min-siblings');
		if (!minSiblings)
			throw new Error("Missing argument 'min-siblings' in <django-form-collection>")
		this.minSiblings = parseInt(minSiblings);
		const maxSiblings = element.getAttribute('max-siblings');
		if (maxSiblings) {
			this.maxSiblings = parseInt(maxSiblings);
		}
		const removeButton = element.querySelector(':scope > button.remove-collection');
		if (!removeButton)
			throw new Error('<django-form-collection> with siblings requires child element <button class="remove-collection">');
		this.removeButton = removeButton as HTMLButtonElement;
		this.removeButton.addEventListener('click', this.removeCollection);
	}

	private removeCollection = () => {
		const siblings = this.parent?.children ?? this.formset.formCollections;
		if (this.justAdded) {
			this.disconnect();
			siblings.splice(siblings.indexOf(this), 1);
			this.repositionSiblings();
		} else {
			this.toggleForRemoval(!this.markedForRemoval);
			this.removeButton.disabled = !this.markedForRemoval;
		}
		siblings.forEach(sibling => sibling.updateRemoveButtonAttrs());
		const formCollectionTemplate = this.parent?.formCollectionTemplate ?? this.formset.formCollectionTemplate;
		formCollectionTemplate!.updateAddButtonAttrs();
	}

	protected disconnect() {
		this.removeButton!.removeEventListener('click', this.removeCollection);
		super.disconnect();
	}

	public repositionSiblings() {
		const siblings = this.parent?.children ?? this.formset.formCollections;
		siblings.forEach((sibling, position) => {
			if (sibling instanceof DjangoFormCollectionSibling) {
				sibling.position = position;
				sibling.element.setAttribute('sibling-position', String(position));
			}
		});
	}

	public updateRemoveButtonAttrs() {
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

	public markAsFreshAndEmpty(justAdded?: boolean) {
		this.justAdded = justAdded || this.element.hasAttribute('fresh-and-empty');
		super.markAsFreshAndEmpty(this.justAdded);
	}

	public get isFreshAndEmpty() : boolean {
		return this.justAdded && super.isFreshAndEmpty;
	}

	public removeFreshAndEmpty() {
		if (!this.removeButton.disabled && this.isFreshAndEmpty) {
			this.removeCollection();
		} else {
			super.removeFreshAndEmpty();
		}
	}

	protected resetToInitial() : boolean {
		if (this.justAdded && !this.element.hasAttribute('fresh-and-empty')) {
			this.disconnect();
			return true;
		} else {
			super.resetToInitial();
			return false;
		}
	}
}


class DjangoFormCollectionTemplate {
	private readonly formset: DjangoFormset;
	private readonly element: HTMLTemplateElement;
	private readonly parent?: DjangoFormCollection;
	private readonly renderEmptyCollection: Function;
	private readonly addButton?: HTMLButtonElement;
	private readonly maxSiblings: number|null = null;
	private readonly baseContext = new Map<string, string>();
	public readonly prefix: string;
	public markedForRemoval = false;

	constructor(formset: DjangoFormset, element: HTMLTemplateElement, parent?: DjangoFormCollection) {
		this.formset = formset;
		this.element = element;
		this.parent = parent;
		const matches = element.innerHTML.matchAll(/\$\{([^} ]+)\}/g);
		for (const match of matches) {
			this.baseContext.set(match[1], match[0]);
		}
		const prefix = element.getAttribute('prefix');
		if (!prefix)
			throw new Error('<template class="empty-collection" ...> requires attribute "prefix"');
		this.prefix = prefix;
		formset.pushTemplatePrefix(this.prefix);
		this.renderEmptyCollection = template(element.innerHTML);
		if (element.nextElementSibling?.matches('button.add-collection')) {
			this.addButton = element.nextElementSibling as HTMLButtonElement;
			this.addButton.addEventListener('click', this.appendFormCollectionSibling);
		}
		const innerCollection = this.element.content.querySelector('django-form-collection');
		const maxSiblings = innerCollection?.getAttribute('max-siblings');
		if (maxSiblings) {
			this.maxSiblings = parseInt(maxSiblings);
		}
		if (element.hasAttribute('sortable')) {
			new Sortable(element.parentElement!, {
				animation: 150,
				handle: 'django-form-collection[sibling-position]:not(.dj-marked-for-removal) > .collection-drag-handle',
				draggable: 'django-form-collection[sibling-position]',
				selectedClass: 'selected',
				ghostClass: 'dj-ghost-collection',
				onEnd: this.resortSiblings,
			});
		}
	}

	private resortSiblings = (event: SortableEvent) => {
		const oldIndex = event.oldDraggableIndex ?? NaN;
		const newIndex = event.newDraggableIndex ?? NaN;
		if (!isFinite(oldIndex) || !isFinite(newIndex) || oldIndex === newIndex)
			return;
		const siblings = this.parent?.children ?? this.formset.formCollections;
		if (siblings.at(oldIndex) instanceof DjangoFormCollectionSibling) {
			const extracted = siblings.splice(oldIndex, 1);
			siblings.splice(newIndex, 0, ...extracted);
			extracted.at(0)!.repositionSiblings();
			const pathIndex = this.prefix === '0' ? 0 : this.prefix.split('.').length;
			siblings.forEach((sibling, position) => sibling.repositionForms(pathIndex, position));
			this.formset.validate();
		}
	}

	private appendFormCollectionSibling = () => {
		const context = Object.fromEntries(this.baseContext);
		const [position, siblingId] = this.getNextPositionAndSiblingId();
		context['position'] = position.toString();
		context['siblingId'] = siblingId.toString();
		// this context rewriting is necessary to render nested templates properly.
		// the hard-coded limit of 10 nested levels should be more than anybody ever will need.
		context['position_1'] = '${position}';
		context['siblingId_1'] = '${siblingId}';
		for (let k = 1; k < 10; ++k) {
			context[`position_${k + 1}`] = `$\{position_${k}\}`;
			context[`siblingId_${k + 1}`] = `$\{siblingId_${k}\}`;
		}
		const renderedHTML = this.renderEmptyCollection(context);
		this.element.insertAdjacentHTML('beforebegin', renderedHTML);
		const newCollectionElement = this.element.previousElementSibling;
		if (!(newCollectionElement instanceof HTMLElement))
			throw new Error("Unable to insert empty <django-form-collection> element.");
		const siblings = this.parent?.children ?? this.formset.formCollections;
		const newCollectionSibling = new DjangoFormCollectionSibling(this.formset, newCollectionElement, siblingId, this.parent);
		siblings.push(newCollectionSibling);
		this.formset.findForms(newCollectionElement);
		this.formset.assignFieldsToForms(newCollectionElement);
		this.formset.assignFormsToCollections();
		this.formset.findCollectionErrorsList();
		newCollectionSibling.markAsFreshAndEmpty(true);
		this.formset.validate();
		siblings.forEach(sibling => sibling.updateRemoveButtonAttrs());
		this.updateAddButtonAttrs();
	}

	private getNextPositionAndSiblingId() {
		// look for the highest position number inside interconnected DjangoFormCollectionSiblings
		let position = -1, siblingId = -1;
		const children = this.parent ? this.parent.children : this.formset.formCollections;
		for (const sibling of children.filter(s => s instanceof DjangoFormCollectionSibling)) {
			position = Math.max(position, (sibling as DjangoFormCollectionSibling).position);
			siblingId = Math.max(siblingId, (sibling as DjangoFormCollectionSibling).siblingId);
		}
		return [position + 1, siblingId + 1];
	}

	public disconnect() {
		this.formset.popTemplatePrefix(this.prefix);
		this.addButton?.removeEventListener('click', this.appendFormCollectionSibling);
	}

	public updateAddButtonAttrs() {
		if (!this.addButton)
			return;
		if (this.markedForRemoval) {
			this.addButton.disabled = true;
			return;
		}
		const siblings = this.parent?.children ?? this.formset.formCollections;
		const numActiveSiblings = siblings.filter(s => !s.markedForRemoval).length;
		this.addButton.disabled = this.maxSiblings === null ? false : numActiveSiblings >= this.maxSiblings;
	}

	static findFormCollectionTemplate(formset: DjangoFormset, element: Element, formCollection?: DjangoFormCollection) : DjangoFormCollectionTemplate|undefined {
		const templateElement = element.querySelector(':scope > .collection-siblings > template.empty-collection') as HTMLTemplateElement;
		if (templateElement) {
			const formCollectionTemplate = new DjangoFormCollectionTemplate(formset, templateElement as HTMLTemplateElement, formCollection);
			formCollectionTemplate.updateAddButtonAttrs();
			return formCollectionTemplate;
		}
	}
}


export class DjangoFormset {
	private readonly element: DjangoFormsetElement;
	public readonly buttons = Array<DjangoButton>(0);
	private readonly forms = Array<DjangoForm>(0);
	private readonly CSRFToken: string|null;
	public readonly formCollections = Array<DjangoFormCollection>(0);
	public readonly collectionErrorsList = new Map<string, HTMLUListElement>();
	public formCollectionTemplate?: DjangoFormCollectionTemplate;
	public readonly showFeedbackMessages: boolean;
	private readonly abortController = new AbortController;
	private readonly emptyCollectionPrefixes = Array<string>(0);
	private data = {};

	constructor(formset: DjangoFormsetElement) {
		this.element = formset;
		this.showFeedbackMessages = this.parseWithholdFeedback();
		this.CSRFToken = this.element.getAttribute('csrf-token');
	}

	connectedCallback() {
		this.findForms();
		this.findFormCollections();
		this.findCollectionErrorsList();
		this.assignFieldsToForms();
		this.assignFormsToCollections();
		this.findDetachedButtons();
		this.formCollections.forEach(collection => collection.markAsFreshAndEmpty());
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

	public pushTemplatePrefix(prefix: string) {
		this.emptyCollectionPrefixes.push(prefix);
	}

	public popTemplatePrefix(prefix: string) {
		const index = this.emptyCollectionPrefixes.indexOf(prefix);
		if (index >= 0) {
			this.emptyCollectionPrefixes.splice(index, 1);
		}
	}

	public assignFieldsToForms(parentElement?: Element) {
		parentElement = parentElement ?? this.element;
		for (const fieldElement of parentElement.querySelectorAll('INPUT, SELECT, TEXTAREA, BUTTON')) {
			const formId = fieldElement.getAttribute('form');
			if (!formId)
				continue;
			const djangoForms = this.forms.filter(form => form.formId && form.formId === formId);
			if (djangoForms.length < 1)
				continue;
			if (djangoForms.length > 1)
				throw new Error(`More than one form has id="${formId}"`);
			const djangoForm = djangoForms[0];
			if (fieldElement instanceof HTMLInputElement && fieldElement.type === 'hidden') {
				if (!djangoForm.hiddenInputFields.includes(fieldElement)) {
					djangoForm.hiddenInputFields.push(fieldElement);
				}
			} else if (fieldElement instanceof HTMLButtonElement) {
				if (fieldElement.hasAttribute('df-click') && fieldElement.form === djangoForm.element) {
					const button = new DjangoButton(djangoForm.formset, fieldElement, [...djangoForm.path, fieldElement.name]);
					this.buttons.push(button);
				}
			} else {
				const fieldGroupElement = fieldElement.closest('[role="group"]');
				if (fieldGroupElement && !djangoForm.fieldGroups.find(fg => fg.element === fieldGroupElement)) {
					djangoForm.fieldGroups.push(new FieldGroup(djangoForm, fieldGroupElement as HTMLElement));
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
		const forms = this.forms.filter(form => !form.isTransient);
		if (forms.length === 1)
			return;
		const formNames = Array<string>();
		forms.forEach(form => {
			if (!form.name)
				throw new Error("Multiple <form>-elements in a <django-formset> require a unique name each.");
			if (form.name in formNames)
				throw new Error(`Duplicate name "${form.name}" used in multiple forms of same <django-formset>.`);
			formNames.push(form.name);
		});
	}

	private findFormCollections() {
		// find all immediate elements <django-form-collection ...> belonging to the current <django-formset>
		for (const element of DjangoFormCollection.getChildCollections(this.element)) {
			this.formCollections.push(new DjangoFormCollection(this, element));
		}
		for (const [siblingId, element] of DjangoFormCollection.getChildSiblingsCollections(this.element).entries()) {
			this.formCollections.push(new DjangoFormCollectionSibling(this, element, siblingId));
		}
		this.formCollections.forEach(collection => collection.updateRemoveButtonAttrs());
		this.formCollectionTemplate = DjangoFormCollectionTemplate.findFormCollectionTemplate(this, this.element);
	}

	public findCollectionErrorsList() {
		// find all elements <any class="dj-collection-errors"> belonging to the current <django-formset>
		this.collectionErrorsList.clear();
		for (const element of this.element.getElementsByClassName('dj-collection-errors')) {
			const prefix = element.getAttribute('prefix') ?? '';
			const ulElement = element.querySelector('ul.dj-errorlist') as HTMLUListElement;
			this.collectionErrorsList.set(prefix, ulElement);
		}
	}

	private findDetachedButtons() {
		for (const element of this.element.getElementsByTagName('BUTTON')) {
			if (element.hasAttribute('df-click')) {
				const buttonElement = element as HTMLButtonElement;
				if (!this.buttons.find(button => button.element === buttonElement)) {
					const path = buttonElement.name ? [buttonElement.name] : [];
					this.buttons.push(new DjangoButton(this, buttonElement, path));
				}
			}
		}
	}

	public assignFormsToCollections() {
		this.formCollections.forEach(collection => collection.assignForms(this.forms));
	}

	public removeForm(form: DjangoForm) {
		this.forms.splice(this.forms.indexOf(form), 1);
	}

	private removeFreshCollections() {
		const formCollections = Array.from(this.formCollections).reverse();
		formCollections.forEach(collection => collection.removeFreshAndEmpty());
	}

	private aggregateValues() {
		this.data = {};
		for (const form of this.forms) {
			setDataValue(this.data, form.getAbsPath(), Object.fromEntries(form.aggregateValues()));
		}
		this.updateOperability();
	}

	public updateOperability(action?: string) {
		for (const form of this.forms) {
			if (form.markedForRemoval)
				continue;
			form.updateOperability(action);
		}
		for (const button of this.buttons) {
			button.updateOperability(action);
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

	public buildBody(extraData?: Object) : Object {
		let dataValue: any;
		// Build `body`-Object recursively.
		// Deliberately ignore type-checking, because `body` must be built as POJO to be JSON serializable.
		function extendBody(entry: any, relPath: Array<string>) {
			if (relPath.length === 1) {
				// the leaf object
				if (Array.isArray(entry)) {
					if (dataValue && !entry.includes(dataValue)) {
						entry.push(dataValue);
					}
				} else {
					entry[relPath[0]] = dataValue ?? [];
				}
				return;
			}
			if (isNaN(parseInt(relPath[1]))) {
				const innerObject = entry[relPath[0]] ?? {};
				extendBody(innerObject, relPath.slice(1));
				const index = parseInt(relPath[0]);
				if (isNaN(index)) {
					entry[relPath[0]] = innerObject;
				} else {
					entry[index] = {...entry[index], ...innerObject};
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

		// 1. extend body with empty arrays from Form Collections with siblings
		for (const prefix of this.emptyCollectionPrefixes) {
			const absPath = ['formset_data', ...prefix.split('.')];
			dataValue = getDataValue(body, absPath);
			extendBody(body, absPath);
		}

		// 2. iterate over all forms and fill the data structure with content
		for (const form of this.forms) {
			if (!form.name) {
				// it's a single form, which doesn't have a name
				const formsetData = Object.fromEntries(form.aggregateValues());
				return Object.assign({}, {'formset_data': formsetData}, {_extra: extraData});
			}
			if (form.isTransient)
				continue;
			const absPath = form.getAbsPath();
			dataValue = getDataValue(this.data, absPath);
			if (form.markedForRemoval) {
				dataValue[MARKED_FOR_REMOVAL] = true;
			}
			extendBody(body, absPath);
		}

		// 3. extend data structure with extra data, for instance from buttons
		return Object.assign({}, body, {_extra: extraData});
	}

	async submit(extraData?: Object) : Promise<Response|undefined> {
		let formsAreValid = true;
		this.setSubmitted();
		if (!this.forceSubmission) {
			for (const form of this.forms) {
				if (form.markedForRemoval || form.isTransient)
					continue;
				formsAreValid = form.isValid() && formsAreValid;
			}
		}
		if (formsAreValid) {
			if (!this.endpoint)
				throw new Error("<django-formset> requires attribute 'endpoint=\"server endpoint\"' for submission");
			this.removeFreshCollections();
			const body = this.buildBody(extraData);
			try {
				const headers = new Headers();
				headers.append('Accept', 'application/json');
				headers.append('Content-Type', 'application/json');
				if (this.CSRFToken) {
					headers.append('X-CSRFToken', this.CSRFToken);
				}
				const response = await fetch(this.endpoint, {
					method: 'POST',
					headers: headers,
					body: JSON.stringify(body),
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
						const body = await response.clone().json();
						this.reportErrors(body);
						return response;
					default:
						console.warn(`Unknown response status: ${response.status}`);
						this.clearErrors();
						this.buttons.forEach(button => button.restoreToInitial());
						return response;
				}
			} catch (error) {
				this.clearErrors();
				this.buttons.forEach(button => button.restoreToInitial());
				alert(error);
			}
		} else {
			this.clearErrors();
			for (const form of this.forms) {
				form.reportValidity();
			}
		}
	}

	private reportErrors(body: any) {
		console.info("Response from server:", body);
		for (const form of this.forms) {
			const errors = form.name ? getDataValue(body, form.name.split('.'), null) : body;
			if (!isEmpty(errors)) {
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
		DjangoFormCollection.resetCollectionsToInitial(this.formCollections);
		this.formCollectionTemplate?.updateAddButtonAttrs();
		this.forms.forEach(form => form.resetToInitial());
		this.validate();
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

	public getDataValue(path: Array<string>) : string|undefined {
		const absPath = ['formset_data', ...path];
		return getDataValue(this.data, absPath);
	}

	public setFieldValue(path: Array<string>, value: FieldValue) {
		const formPath = path.slice(0, -1);
		const destForm = this.forms.find(form => isEqual(form.path, formPath));
		if (destForm && path.length > 0) {
			destForm.setFieldValue(path.slice(-1)[0], value);
		}
	}

	public findFirstErrorReport() : Element|null {
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
		return ['endpoint', 'withhold-feedback', 'force-submission'];
	}

	connectedCallback() {
		this[FS].connectedCallback();
	}

	public async submit(data?: Object) : Promise<Response|undefined> {
		return this[FS].submit(data);
	}

	public async abort() {
		return this[FS].abort();
	}

	public async reset() {
		return this[FS].resetToInitial();
	}
}
