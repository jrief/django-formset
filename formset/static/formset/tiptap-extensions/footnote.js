{
	name: 'footnote',
	keepOnSplit: false,
	inline: true,
	group: 'inline',
	selectable: true,

	addAttributes() {
		return {
			content: {
				default: null,
				renderHTML: attributes => {
					return {
						content: JSON.stringify(attributes.content ?? {type: 'doc'}),
					};
				},
				parseHTML: element => {
					return JSON.parse(element.getAttribute('content') ?? '{"type": "doc"}');
				},
			},
			role: {
				default: 'note',
			},
		}
	},

	parseHTML() {
		return [{
			tag: 'span',
			role: 'note',
		}];
	},

	renderHTML({HTMLAttributes}) {
		return ['span', HTMLAttributes];
	},

}
