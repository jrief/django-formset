{
	name: 'simple_geomap',
	inline: true,
	group: 'inline',
	draggable: true,

	addAttributes() {
		return {
			content: {
				default: null,
				renderHTML: attributes => {
					return {
						content: JSON.stringify(attributes.content ?? {type: 'FeatureCollection'}),
					};
				},
				parseHTML: element => {
					return JSON.parse(element.getAttribute('content') ?? '{"type": "FeatureCollection"}');
				},
			},
		};
	},

	parseHTML() {
		return [{tag: 'geojson-renderer'}];
	},

	renderHTML({HTMLAttributes}) {
		return ['geojson-renderer', HTMLAttributes];
	},

}
