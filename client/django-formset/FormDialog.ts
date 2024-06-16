import isString from 'lodash.isstring';
import {StyleHelpers} from 'django-formset/helpers';
import {parse} from 'build/tag-attributes';
import styles from './DjangoFormset.scss';


export abstract class FormDialog {
	protected readonly element: HTMLDialogElement;
	protected readonly formElement: HTMLFormElement;
	private readonly dialogHeaderElement: HTMLElement | null;
	protected readonly isModal: boolean;
	protected readonly induceOpen: Function;
	protected readonly induceClose: Function;
	private readonly baseSelector = 'dialog[is="django-dialog-form"]';
	private dialogRect: DOMRect | null = null;
	private dialogOffsetX: number = 0;
	private dialogOffsetY: number = 0;

	constructor(element: HTMLDialogElement) {
		this.element = element;
		this.formElement = this.element.querySelector('form[method="dialog"]')!;
		if (!this.formElement)
			throw new Error(`${this} requires child <form method="dialog">`);
		this.dialogHeaderElement = this.element.querySelector('.dialog-header');
		if (!StyleHelpers.stylesAreInstalled(this.baseSelector)) {
			this.transferStyles();
		}
		this.isModal = this.element.hasAttribute('df-modal');
		this.induceOpen = this.evalInducer('df-induce-open', (...args: any[]) => this.openDialog(...args));
		this.induceClose = this.evalInducer('df-induce-close', (...args: any[]) => this.closeDialog(...args));
	}

	protected evalInducer(attr: string, inducer: Function) : Function {
		const attrValue = this.element?.getAttribute(attr);
		if (!isString(attrValue))
			return () => {};
		try {
			const evalExpression = new Function(`return ${parse(attrValue, {startRule: 'InduceExpression'})}`);
			return (...args: any[]) => {
				if (evalExpression.call(this)) {
					inducer(...args);
				}
			};
		} catch (error) {
			throw new Error(`Error while parsing <dialog ${attr}="${attrValue}">: ${error}.`);
		}
	}

	protected openDialog(...args: any[]) {
		const viewport = window.visualViewport;
		if (this.element.open || !viewport)
			return;
		if (this.isModal) {
			this.element.showModal();
		} else {
			this.element.show();
			if (this.dialogHeaderElement && !this.dialogRect) {
				this.dialogRect = this.element.getBoundingClientRect();
				this.dialogOffsetY = Math.max((viewport.height - this.dialogRect.height) / 2, 0);
				this.element.style.transform = `translate(${this.dialogOffsetX}px, ${this.dialogOffsetY}px)`;
				this.dialogHeaderElement.addEventListener('pointerdown', this.handlePointerDown);
				this.dialogHeaderElement.addEventListener('touchstart', this.handlePointerDown);
			}
		}
		this.element.addEventListener('close', () => this.closeDialog(), {once: true});
	}

	protected closeDialog(returnValue?: string) {
		this.element.close(returnValue);
	}

	private handlePointerDown = (event: PointerEvent | TouchEvent) => {
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
			touchMoveEvt.preventDefault()
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

	private transferStyles() {
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		if (!declaredStyles.sheet)
			throw new Error("Could not create <style> element");
	}

	// Hook to be overridden by subclasses.
	// It shall return the aggregated data of the form dialog.
	protected getDataValue(path: Array<string>) : string|undefined {
		return undefined;
	}

	// Hook to be overridden by subclasses.
	// path is where in the formset the button is located.
	// It shall return true if the activation button is considered to be pressed.
	protected isButtonActive(path: Array<string>, action: string): boolean {
		return false;
	}

	public isOpen() {
		return this.element.open;
	}

	public updateOperability(...args: any[]) {
		this.induceOpen(...args);
		this.induceClose(...args);
	}
}
