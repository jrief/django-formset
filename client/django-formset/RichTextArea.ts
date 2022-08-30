import { Editor } from '@tiptap/core';
import Document from '@tiptap/extension-document';
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import Bold from '@tiptap/extension-bold';
import Italic from '@tiptap/extension-italic';
import Underline from '@tiptap/extension-underline';
import BulletList from '@tiptap/extension-bullet-list';
import ListItem from '@tiptap/extension-list-item';
import styles from 'sass:./RichTextArea.scss';
import { StyleHelpers } from "./helpers";


class RichTextArea {
	private readonly textAreaElement: HTMLTextAreaElement;
	private readonly declaredStyles: HTMLStyleElement;
	private readonly editor: Editor;
	private readonly proseMirrorElement: HTMLElement;
	private readonly initialValue: string | object;
	private readonly required: Boolean;

	constructor(textAreaElement: HTMLTextAreaElement) {
		this.textAreaElement = textAreaElement;
		this.declaredStyles = document.createElement('style');
		this.declaredStyles.innerText = styles;
		document.head.appendChild(this.declaredStyles);
		this.editor = this.createEditor(textAreaElement);
		const proseMirrorElement = this.editor.options.element.getElementsByClassName('ProseMirror').item(0);
		if (!(proseMirrorElement instanceof HTMLElement))
			throw new Error("Failed to initialize Rich Text Area");
		this.proseMirrorElement = proseMirrorElement;
		this.initialValue = textAreaElement.value;
		this.required = textAreaElement.required;
		textAreaElement.classList.add('dj-concealed');
		this.installEventHandlers();
	}

	private createEditor(textAreaElement: HTMLTextAreaElement) : Editor {
		const divElement = document.createElement('DIV') as HTMLDivElement;
		divElement.classList.add('richtext-wrapper');
		textAreaElement.insertAdjacentElement('beforebegin', divElement);
		const editor = new Editor({
			element: divElement,
			extensions: [
				Document,
				Paragraph,
				Text,
				Bold,
				Italic,
				Underline,
				BulletList,
				ListItem.extend({
					content: 'text*',
				}),
			],
			content: '',
			autofocus: false,
			editable: !textAreaElement.disabled,
			injectCSS: false,
		});
		this.transferStyles(textAreaElement);
		this.wrapControlElements(divElement);
		return editor;
	}

	private wrapControlElements(wrapperElement: HTMLElement) {
		const buttonGroup = wrapperElement.parentElement?.querySelector('textarea[is="django-richtext"] ~ [role="group"]');
		if (!buttonGroup)
			throw new Error('<textarea is="richtext"> requires a sibling element <ANY [role="group"]>');
		wrapperElement.insertBefore(buttonGroup, null);
		buttonGroup.querySelectorAll('button[aria-label]').forEach(button => {
			button.addEventListener('click', this.controlButtonClicked);
		});
	}

	private installEventHandlers() {
		this.editor.on('focus', this.focused);
		this.editor.on('update', this.updated);
		this.editor.on('blur', this.blurred);
		this.textAreaElement.addEventListener('valid', this.validate);
	}

	private focused = () => {
		console.log('focus');
		this.textAreaElement.dispatchEvent(new Event('focus'));
	}

	private updated = () => {
		console.log('update');
		this.textAreaElement.innerText = this.editor.getText();
		this.textAreaElement.dispatchEvent(new Event('input'));
	}

	private blurred = () => {
		this.textAreaElement.dispatchEvent(new Event('blur'));
	}

	private validate = (event: Event) => {
		console.log(event);
		if (this.required && !this.editor.getText()) {
			this.proseMirrorElement.classList.remove('valid');
			this.proseMirrorElement.classList.add('invalid');
		} else {
			this.proseMirrorElement.classList.add('valid');
			this.proseMirrorElement.classList.remove('invalid');
		}
	}

	private controlButtonClicked = (event: Event) => {
		if (event.currentTarget instanceof HTMLButtonElement && typeof event.currentTarget.ariaLabel === 'string') {
			const parts = event.currentTarget.ariaLabel.split('-');
			const funcname = parts.map((p, k) => k > 0 ? p.charAt(0).toUpperCase() + p.slice(1) : p).join('');
			const func = this[funcname as keyof RichTextArea] as (() => void);
			if (typeof func !== 'function')
				throw new Error(`Unknown editor function '${funcname}'.`);
			func.apply(this);
		}
	}

	private bold() {
		this.editor.chain().focus().toggleBold().run();
	}

	private italic() {
		this.editor.chain().focus().toggleItalic().run();
	}

	private underline() {
		this.editor.chain().focus().toggleUnderline().run();
	}

	private bulletList() {
		this.editor.chain().focus().toggleBulletList().run();
	}

	private clearFormat() {
		this.editor.chain().focus().unsetBold().unsetUnderline().unsetItalic().run();
	}

	private transferStyles(textareaElement: HTMLTextAreaElement) {
		const sheet = this.declaredStyles.sheet;
		for (let index = 0; sheet && index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case '.ProseMirror':
					extraStyles = StyleHelpers.extractStyles(textareaElement, [
						'width', 'height', 'background-image', 'border', 'border-radius', 'box-shadow', 'outline',
						'font-family', 'font-size', 'font-strech', 'font-style', 'font-weight',
						'letter-spacing', 'white-space', 'line-height', 'overflow', 'padding', 'resize']);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ProseMirror.ProseMirror-focused':
					textareaElement.style.transition = 'none';
					textareaElement.focus();
					extraStyles = StyleHelpers.extractStyles(textareaElement, [
						'border', 'box-shadow', 'outline']);
					textareaElement.blur();
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					textareaElement.style.transition = '';
					break;
				default:
					break;
			}
		}
	}

	public getValue() : any {
		//return this.textAreaElement.innerText;
		return this.editor.getText();
	}
}


const RTA = Symbol('RichTextArea');

export class RichTextAreaElement extends HTMLTextAreaElement {
	private [RTA]?: RichTextArea;  // hides internal implementation

	private connectedCallback() {
		this[RTA] = new RichTextArea(this);
	}

	public get value() : any {
		return this[RTA]?.getValue();
	}

	public async getValue() {
		return this[RTA]?.getValue();
	}
}
