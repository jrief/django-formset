// Do not mix this Tiptap extension with `@tiptap/extension-text-style`
// as they interfere making this extension unusable
import {Mark} from '@tiptap/core';

export interface FontFamilyOptions {
	allowedClasses: string[],
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		fontFamily: {
			setFont: (cssClass: string) => ReturnType,
			unsetFont: () => ReturnType,
		}
	}
}

export const FontFamily = Mark.create<FontFamilyOptions>({
	name: 'fontFamily',

	addOptions() {
		return {
			allowedClasses: [],
		}
	},

	addAttributes() {
		return {
			fontFamily: {
				default: null,
				parseHTML: element => {
					for (let cssClass of this.options.allowedClasses) {
						if (element.classList.contains(cssClass))
							return cssClass;
					}
				},
				renderHTML: attributes => {
					return {class: attributes.fontFamily};
				},
			},
		};
	},

	parseHTML() {
		return [{
			tag: 'span',
			getAttrs: element => {
				if (element instanceof HTMLElement) {
					if (this.options.allowedClasses.some(cssClass => element.classList.contains(cssClass)))
						return {};
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
			setFont: (cssClass: string) => ({commands}) => {
				return commands.setMark(this.name, {fontFamily: cssClass});
			},
			unsetFont: () => ({commands}) => {
				return commands.unsetMark(this.name);
			},
		}
	},
});
