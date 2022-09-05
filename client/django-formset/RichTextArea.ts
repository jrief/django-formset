import { Editor } from '@tiptap/core';
import Document from '@tiptap/extension-document';
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import Bold from '@tiptap/extension-bold';
import Italic from '@tiptap/extension-italic';
import Underline from '@tiptap/extension-underline';
import BulletList from '@tiptap/extension-bullet-list';
import ListItem from '@tiptap/extension-list-item';
import Link from '@tiptap/extension-link';
import styles from 'sass:./RichTextArea.scss';
import { StyleHelpers } from "./helpers";


class RichTextArea {
	private readonly textAreaElement: HTMLTextAreaElement;
	private readonly wrapperElement: HTMLElement;
	private readonly buttonGroupElement: HTMLElement | null;
	private readonly declaredStyles: HTMLStyleElement;
	private readonly editor: Editor;
	private readonly initialValue: string | object;
	private readonly required: Boolean;

	constructor(wrapperElement: HTMLElement, textAreaElement: HTMLTextAreaElement) {
		this.wrapperElement = wrapperElement;
		this.textAreaElement = textAreaElement;
		this.buttonGroupElement = wrapperElement.querySelector('[role="group"]');
		this.declaredStyles = document.createElement('style');
		this.declaredStyles.innerText = styles;
		document.head.appendChild(this.declaredStyles);
		this.editor = this.createEditor(wrapperElement);
		this.transferStyles();
		//wrapperElement.style.width = 'fit-content';
		this.initialValue = textAreaElement.value;
		this.required = textAreaElement.required;
		this.concealTextArea(wrapperElement);
		this.installEventHandlers();
	}

	private createEditor(wrapperElement: HTMLElement) : Editor {
		const scriptContent = wrapperElement.querySelector('textarea + script')?.textContent ?? '';
		const editor = new Editor({
			element: wrapperElement,
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
				Link,
			],
			content: JSON.parse(scriptContent),
			autofocus: false,
			editable: !this.textAreaElement.disabled,
			injectCSS: false,
		});
		return editor;
	}

	private installEventHandlers() {
		this.editor.on('focus', this.focused);
		this.editor.on('update', this.updated);
		this.editor.on('blur', this.blurred);
		this.buttonGroupElement?.querySelectorAll('button[aria-label]').forEach(button => {
			button.addEventListener('click', this.controlButtonClicked);
		});
	}

	private concealTextArea(wrapperElement: HTMLElement) {
		wrapperElement.insertAdjacentElement('afterend', this.textAreaElement);
		this.textAreaElement.classList.add('dj-concealed');
	}

	private focused = () => {
		console.log('focus');
		this.wrapperElement.classList.add('focused');
		this.textAreaElement.dispatchEvent(new Event('focus'));
	}

	private updated = () => {
		console.log('update');
		this.textAreaElement.innerText = this.editor.getText();
		this.textAreaElement.dispatchEvent(new Event('input'));
	}

	private blurred = () => {
		console.log('blurred');
		this.wrapperElement.classList.remove('focused');
		if (this.required && !this.editor.getText()) {
			this.wrapperElement.classList.remove('valid');
			this.wrapperElement.classList.add('invalid');
		} else {
			this.wrapperElement.classList.add('valid');
			this.wrapperElement.classList.remove('invalid');
		}
		this.textAreaElement.dispatchEvent(new Event('blur'));
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

	private link() {
		const previousUrl = this.editor.getAttributes('link').href;
		const url = window.prompt('URL', previousUrl);

		// cancelled
		if (url === null)
			return;

		// empty
		if (url === '') {
			this.editor.chain().focus().extendMarkRange('link').unsetLink().run();
			return
		}

		// update link
		this.editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
	}

	private bulletList() {
		this.editor.chain().focus().toggleBulletList().run();
	}

	private clearFormat() {
		this.editor.chain().focus().unsetBold().unsetUnderline().unsetItalic().run();
	}

	private transferStyles() {
		const buttonGroupHeight = this.buttonGroupElement ? this.buttonGroupElement.getBoundingClientRect().height : 0;
		const sheet = this.declaredStyles.sheet;
		for (let index = 0; sheet && index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case '.dj-richtext-wrapper':
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'height', 'background-image', 'border', 'border-radius', 'box-shadow', 'outline',
						'resize',
					]);
					extraStyles = extraStyles.concat(`min-height:${buttonGroupHeight * 2}px;`);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.dj-richtext-wrapper.focused':
					this.textAreaElement.style.transition = 'none';
					this.textAreaElement.focus();
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'border', 'box-shadow', 'outline']);
					this.textAreaElement.blur();
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					this.textAreaElement.style.transition = '';
					break;
				case '.dj-richtext-wrapper .ProseMirror':
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'font-family', 'font-size', 'font-strech', 'font-style', 'font-weight', 'letter-spacing',
						'white-space', 'line-height', 'overflow', 'padding']);
					extraStyles = extraStyles.concat(`top:${buttonGroupHeight + 1}px;`);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.dj-richtext-wrapper [role="group"]':
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'border-bottom'
					])
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				default:
					break;
			}
		}
	}

	public getValue() : any {
		//return this.textAreaElement.innerText;
		return this.editor.getJSON();
	}
}


const RTA = Symbol('RichTextArea');

export class RichTextAreaElement extends HTMLTextAreaElement {
	private [RTA]?: RichTextArea;  // hides internal implementation

	private connectedCallback() {
		const wrapperElement = this.closest('.dj-richtext-wrapper');
		if (wrapperElement instanceof HTMLElement) {
			this[RTA] = new RichTextArea(wrapperElement, this);
		}
	}

	public get value() : any {
		return this[RTA]?.getValue();
	}

	public async getValue() {
		return this[RTA]?.getValue();
	}
}
