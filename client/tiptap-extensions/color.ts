// Do not mix this Tiptap extension with `@tiptap/extension-text-style`
// as they interfere making this extension unusable
import { Mark } from '@tiptap/core';

export interface TextColorOptions {
	allowedClasses: string[],
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		textColor: {
			setColor: (color: string) => ReturnType,
			unsetColor: () => ReturnType,
		}
	}
}

export const TextColor = Mark.create<TextColorOptions>({
	name: 'textColor',

	addOptions() {
		return {
			allowedClasses: [],
		}
	},

	addAttributes() {
		return {
			textColor: {
				default: null,
				parseHTML: element => {
					if (this.options.allowedClasses.length === 0)
						return element.style.color;
					for (let cssClass of this.options.allowedClasses) {
						if (element.classList.contains(cssClass))
							return cssClass;
					}
				},
				renderHTML: attributes => {
					if (this.options.allowedClasses.length === 0)
						return {style: `color: ${attributes.textColor};`};
					return {class: attributes.textColor};
				},
			},
			classBased: {
				default: this.options.allowedClasses.length !== 0,
			},
		};
	},

	parseHTML() {
		return [{
			tag: 'span',
			getAttrs: element => {
				if (element instanceof HTMLElement) {
					if (this.options.allowedClasses.length === 0) {
						if (/^rgb\(\d{1,3},\s\d{1,3},\s\d{1,3}\)$/.test(element.style.color))
							return {};
					} else {
						if (this.options.allowedClasses.some(cssClass => element.classList.contains(cssClass)))
							return {};
					}
				}
				return false;
			},
		}];
	},

	renderHTML({HTMLAttributes}) {
		return ['span', HTMLAttributes, 0];
	},

	addCommands() {
		return {
			setColor: (color: string) => ({commands}) => {
				return commands.setMark(this.name, {textColor: color, classBased: this.options.allowedClasses.length !== 0});
			},
			unsetColor: () => ({commands}) => {
				return commands.unsetMark(this.name);
			},
		}
	},
});
