{
	name: 'simple_link',
	priority: 1000,
	keepOnSplit: false,

	addAttributes() {
		return {
			href: {
				default: null,
			},
		};
	},

	parseHTML() {
		return [{tag: 'a[href]:not([href *= "javascript:" i])'}];
	},

	renderHTML({HTMLAttributes}) {
		return ['a', HTMLAttributes, 0];
	},
}
