{
	name: 'simple_geomap',
	inline: true,
	group: 'inline',
	draggable: true,

	addAttributes() {
		return {
			content: {
				default: JSON.stringify({type: 'FeatureCollection'}),
				renderHTML: attributes => {
					return {json: JSON.stringify(attributes.content)};
				},
				parseHTML: element => {
					return JSON.parse(element.getAttribute('content') ?? '{"type": "FeatureCollection"}');
				},
			},
			style: {
				default: 'height: 350px; display: block;',
			}
		};
	},

	parseHTML() {
		return [{tag: 'geojson-renderer'}];
	},

	renderHTML({HTMLAttributes}) {
		return ['geojson-renderer', HTMLAttributes];
	},

	geomap_to_document(elements) {
		console.log('geomap_to_document', elements);
		const endpointUrl = elements.geomap.closest('django-formset')?.getAttribute('endpoint');
		if (!endpointUrl) {
			return {content: elements.geomap.value};
		}
		return new Promise((resolve, reject) => {
			fetch(endpointUrl, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': document.cookie.match(/csrftoken=([0-9a-zA-Z]+)/)?.[1] ?? '',
				},
				body: JSON.stringify(elements.geomap.value),
			}).then(response => {
				if (response.ok) {
					response.json().then(data => resolve({content: data}));
				} else {
					reject(new Error("Failed to save geomap data"));
				}
			}).catch(error => {
				reject(error);
			});
		});
	},

	document_to_geomap(inputElement, attributes) {
		inputElement.dataset.content = JSON.stringify(attributes.content);
	},
}
