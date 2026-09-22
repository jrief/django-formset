{
	name: 'custom_hyperlink',
	priority: 1000,
	keepOnSplit: false,

	addAttributes() {
		return {
			href: {
				default: null,
			},
			page_id: {
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

	hyperlink_to_document(elements) {
		const endpointUrl = elements.link_type.closest('django-formset')?.getAttribute('endpoint');
		if (!endpointUrl) {
			console.warn("No endpoint URL found");
			return {};
		}
		return new Promise((resolve, reject) => {
			const headers = new Headers({
				'Content-Type': 'application/json',
				'X-CSRFToken': document.cookie.match(/csrftoken=([0-9a-zA-Z]+)/)?.[1] ?? '',
				'X-Request-Source': 'RichtextConversion',
			});
			const body = {
				link_type: elements.link_type.value,
				href: elements.url.value,
				page_id: elements.page.value,
				custom_hyperlink: true,
			};
			fetch(endpointUrl, {
				method: 'POST',
				headers: headers,
				body: JSON.stringify(body),
			}).then(response => {
				if (response.ok) {
					response.json().then(data => {
						elements.link_type.value = data.link_type;
						elements.url.value = data.href;
						elements.page.value = String(data.page_id);
						resolve(data);
					});
				} else {
					reject(new Error(response.statusText));
				}
			}).catch(error => {
				reject(error);
			});
		});
	},
}
