import {Mark} from '@tiptap/core';

export interface TextColorOptions {
	//HTMLAttributes: Record<string, any>,
	//allowedClasses: string[],
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
			//HTMLAttributes: {style: 'color'},
			//allowedClasses: [],
		}
	},

	addAttributes() {
		return {
			textColor: {
				default: null,
				parseHTML: element => {
					console.log(element.style.color);
					return element.style.color;
				},
				renderHTML: attributes => {
					console.log(attributes);
					return {
						style: `color: ${attributes.textColor};`,
					}
				},
			},
		};
	},

	parseHTML() {
		// return [
		// 	{
		// 		tag: 'span',
		// 		//style: 'color',
		// 		getAttrs: value => {
		// 			console.log(value);
		// 			return /^(rgb\(\d{1,3}, \d{1,3}, \d{1,3}\))$/.test(value as string) && null;
		// 		}
		// 	},
		// ];
		return [{
			tag: 'span',
			//style: 'color',
			getAttrs: element => {
				console.log(element);
				const hasStyles = (element as HTMLElement).hasAttribute('style')
				if (!hasStyles)
					return false;
				return {};
			},
		}]
	},

	renderHTML({HTMLAttributes}) {
		console.log(HTMLAttributes);
		return ['span', HTMLAttributes, 0];
	},

	addCommands() {
		return {
			setColor: (color: string) => ({commands}) => {
				return commands.setMark(this.name, {textColor: color});
			},
			unsetColor: () => ({commands}) => {
				return commands.unsetMark(this.name);
			},
		}
	},
});
