import isString from 'lodash.isstring';
import {parse} from '../build/tag-attributes';
import isEqual from 'lodash.isequal';
import isFunction from 'lodash.isfunction';
import {toAbsPath} from './helpers';


export abstract class FormDialogBase {
	protected readonly element: HTMLDialogElement;
	protected readonly formElement: HTMLFormElement;
	private readonly dialogHeaderElement: HTMLElement|null;
	private subtreeObserver: MutationObserver|null = null;
	protected readonly isModal: boolean;
	protected readonly induceOpen: Function;
	protected readonly induceClose: Function;
	private dialogRect: DOMRect|null = null;
	private dialogOffsetX: number = 0;
	private dialogOffsetY: number = 0;

	constructor(element: HTMLDialogElement) {
		this.element = element;
		this.formElement = this.element.querySelector('form[method="dialog"]')! as HTMLFormElement;
		if (!this.formElement)
			throw new Error(`${this} requires child <form method="dialog">`);
		this.dialogHeaderElement = this.element.querySelector('.dialog-header');
		this.isModal = this.element.hasAttribute('df-modal');
		this.induceOpen = this.evalInducer('df-induce-open', (...args: any[]) => this.openDialog(...args));
		this.induceClose = this.evalInducer('df-induce-close', (...args: any[]) => this.closeDialog(...args));
	}

	protected evalInducer(attr: string, inducer: Function) : Function {
		const attrValue = this.element?.getAttribute(attr);
		if (!isString(attrValue))
			return () => {};
		try {
			const evalExpression = new Function('...args', `return ${parse(attrValue, {startRule: 'InduceExpression'})}`);
			return (...args: any[]) => {
				if (evalExpression.call(this, ...args)) {
					inducer(...args);
				}
			};
		} catch (error) {
			throw new Error(`Error while parsing <dialog ${attr}="${attrValue}">: ${error}.`);
		}
	}

	protected openDialog(button?: DjangoButton, ...args: any[]) {
		if (this.element.open)
			return;
		if (this.isModal) {
			this.element.showModal();
		} else {
			this.element.show();
			this.positionDialogBox();
			this.subtreeObserver = new MutationObserver(() => this.positionDialogBox());
			this.subtreeObserver.observe(this.element, {childList: true, subtree: true});
		}
		this.element.addEventListener('close', () => this.closeDialog(), {once: true});
	}

	protected closeDialog(button?: DjangoButton, returnValue?: string) {
		if (this.dialogHeaderElement) {
			this.dialogHeaderElement.removeEventListener('pointerdown', this.handlePointerDown);
			this.dialogHeaderElement.removeEventListener('touchstart', this.handlePointerDown);
		}
		this.subtreeObserver?.disconnect();
		this.element.close(returnValue);
	}

	private positionDialogBox() {
		const viewport = window.visualViewport;
		if (this.dialogHeaderElement && viewport) {
			this.dialogRect = this.element.getBoundingClientRect();
			this.dialogOffsetY = Math.max((viewport.height - this.dialogRect.height) / 2, 0);
			this.element.style.transform = `translate(${this.dialogOffsetX}px, ${this.dialogOffsetY}px)`;
			this.dialogHeaderElement.addEventListener('pointerdown', this.handlePointerDown);
			this.dialogHeaderElement.addEventListener('touchstart', this.handlePointerDown);
		}
	}

	private handlePointerDown = (event: PointerEvent|TouchEvent) => {
		const viewport = window.visualViewport!;
		const dialogRect = this.dialogRect!;
		const dialogHeaderElement = this.dialogHeaderElement!;
		let offsetX: number;
		let offsetY: number;

		const moveDialog = (pointerX: number, pointerY: number) => {
			this.dialogOffsetX = Math.max(pointerX - offsetX, -dialogRect.left);
			this.dialogOffsetY = Math.max(pointerY - offsetY, -dialogRect.top);
			this.dialogOffsetX = Math.min(this.dialogOffsetX, viewport.width - dialogRect.right);
			this.dialogOffsetY = Math.min(this.dialogOffsetY, viewport.height - dialogRect.bottom);
			this.element.style.transform = `translate(${this.dialogOffsetX}px, ${this.dialogOffsetY}px)`;
		};
		const handlePointerMove = (pointerMoveEvt: PointerEvent) => {
			moveDialog(pointerMoveEvt.clientX, pointerMoveEvt.clientY);
		};
		const handleTouchMove = (touchMoveEvt: TouchEvent) => {
			touchMoveEvt.preventDefault();
			moveDialog(touchMoveEvt.touches[0].clientX, touchMoveEvt.touches[0].clientY);
		};
		const handlePointerUp = (pointerUpEvt: PointerEvent) => {
			dialogHeaderElement.releasePointerCapture(pointerUpEvt.pointerId);
			dialogHeaderElement.removeEventListener('pointermove', handlePointerMove);
		};
		const handleTouchEnd = (touchEndEvt: TouchEvent) => {
			dialogHeaderElement.removeEventListener('touchmove', handleTouchMove);
		};

		if (event instanceof PointerEvent) {
			offsetX = event.clientX - this.dialogOffsetX;
			offsetY = event.clientY - this.dialogOffsetY;
			dialogHeaderElement.setPointerCapture(event.pointerId);
			dialogHeaderElement.addEventListener('pointermove', handlePointerMove);
			dialogHeaderElement.addEventListener('pointerup', handlePointerUp, {once: true});
		} else {
			offsetX = event.touches[0].clientX - this.dialogOffsetX;
			offsetY = event.touches[0].clientY - this.dialogOffsetY;
			dialogHeaderElement.addEventListener('touchmove', handleTouchMove);
			dialogHeaderElement.addEventListener('touchend', handleTouchEnd, {once: true});
		}
	};

	// Hook to be overridden by subclasses.
	// It shall return the aggregated data of the form dialog.
	protected getDataValue(path: Array<string>) : string|null {
		return null;
	}

	// Hook to be overridden by subclasses.
	// `path` – against which path shall the button be compared.
	// `activator` – function to determine whether the button is active.
	// `button` – the button to be checked.
	// It shall return true if the activation button is considered to be pressed.
	protected isButtonActive(path: string[], activator: Function, button?: DjangoButton, ...args: any[]): boolean {
		return false;
	}

	public isOpen() {
		return this.element.open;
	}

	updateOperability(...args: any[]) {
		this.induceOpen(...args);
		this.induceClose(...args);
	}

	// force to open this dialog, if it contains the given formElement.
	forceVisibility(formElement: HTMLFormElement) {
		if (this.formElement === formElement) {
			this.openDialog();
		}
	}
}


class FormDialog extends FormDialogBase implements Inducible {
	private form?: DjangoForm;
	private formIsValid: Function = () => false;

	constructor(element: HTMLDialogElement) {
		super(element);
		const formElement = element.querySelector('form[method="dialog"]');
		if (!formElement)
			throw new Error(`${element} requires child <form method="dialog">`);
		formElement.addEventListener('django-formset-connected', this.registerInducer, {once: true});
	}

	private registerInducer = (event: Event) => {
		if (!(event instanceof CustomEvent))
			return;
		this.form = event.detail.form as DjangoForm;
		this.formIsValid = this.form.isValid;
		this.form.isValid = this.isDialogValid.bind(this);  // override DjangoForm's isValid() method
		this.form.formset.registerInducer(this);
	};

	private isDialogValid() {
		if (!this.element.open)
			return true;  // closed dialogs are considered as valid because they are unable to report errors
		return this.formIsValid();
	}

	protected openDialog(button?: DjangoButton, ...args: any[]) {
		if (this.element.open)
			return;
		if (!this.form)
			throw new Error(`${this}.form has never been registered`);
		this.form.setPristine();
		this.form.untouch();
		if (button?.element instanceof HTMLButtonElement && isFunction(args[0])) {
			args[0].call(button, this.form.path);
		}
		super.openDialog(button, ...args);
 	}

	protected closeDialog(button?: DjangoButton, returnValue?: string) {
		if (!(button?.element instanceof HTMLButtonElement) || !isString(returnValue))
			return;
		switch (returnValue) {
			case 'apply':
				if (this.formIsValid()) {
					this.element.close('apply');
				}
				break;
			case 'close':
				this.element.blur();
				this.element.close('close');
				break;
			case 'reset':
				this.form?.resetToInitial();
				break;
			case 'clear':
				this.form?.resetToInitial();
				this.element.blur();
				this.element.close('clear');
				break;
			default:
				break;
		}
	}

	protected getDataValue(path: Path) : string|null {
		return this.form!.getDataValue(path);
	}

	protected isButtonActive(path: string[], activator: Function, button?: DjangoButton, ...args: any[]): boolean {
		return button && isEqual(toAbsPath(this.form!.path, path), button.path) && activator(...args);
	}
}


export class FormDialogElement extends HTMLDialogElement {
	readonly #formdialog: FormDialog;

	constructor() {
		super();
		this.#formdialog = new FormDialog(this);
	}
}
