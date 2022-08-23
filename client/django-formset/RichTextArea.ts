import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Document from '@tiptap/extension-document'
import Paragraph from '@tiptap/extension-paragraph'
import Text from '@tiptap/extension-text'
import styles from 'sass:./RichTextArea.scss';
import { StyleHelpers } from "./helpers";


export class RichTextArea {
	private readonly declaredStyles: HTMLStyleElement;
	private readonly field: FieldGroup;
	private readonly editor: Editor;
	private readonly required: Boolean;

	constructor(fieldGroup: FieldGroup, textAreaElement: HTMLTextAreaElement) {
		this.declaredStyles = document.createElement('style');
		this.declaredStyles.innerText = styles;
		document.head.appendChild(this.declaredStyles);
		this.field = fieldGroup;
		this.editor = this.createEditor(textAreaElement);
		this.required = textAreaElement.required;
		//textAreaElement.required = false;
		textAreaElement.hidden = true;
	}

	private createEditor(textAreaElement: HTMLTextAreaElement) : Editor {
		const divElement = document.createElement('DIV');
		textAreaElement.insertAdjacentElement('afterend', divElement);
		const editor = new Editor({
			element: divElement,
			extensions: [
				StarterKit,
				Document,
				Paragraph,
				Text,
			],
			content: '',
			autofocus: false,
			editable: !textAreaElement.disabled,
			injectCSS: false,
		});
		this.transferStyles(textAreaElement);
		return editor;
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

}
