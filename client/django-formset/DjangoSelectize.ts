import TomSelect from 'tom-select/src/tom-select';
import TomSettings from 'tom-select/src/types/settings';
import {TomInput} from 'tom-select/src/types';

export class DjangoSelectizeElement extends HTMLSelectElement {
	private tomSelect?: TomSelect;

	private connectedCallback() {
		// @ts-ignore
		const config: TomSettings = {
			hidePlaceholder: true
		};
		if (!this.getAttribute('multiple')) {
			config.maxItems = 1;
		}
		if (!this.hasChildNodes()) {
			config.load = (query: string, callback: Function) => this.loadOptions(query, callback);
			//config.render = this.render;
		}
		this.tomSelect = new TomSelect(this as unknown as TomInput, config);
	}

	private loadOptions(query: string, callback: Function) {
		const formset = this.tomSelect ? this.tomSelect.input.closest('django-formset') : null;
		if (!formset)
			return;
		const endpoint = formset.getAttribute('endpoint');
		if (!endpoint)
			return;
		const headers = new Headers();
		headers.append('Accept', 'application/json');
		fetch(endpoint + '?q=' + encodeURIComponent(query), {
			method: 'GET',
			headers: headers,
		}).then(response => response.json())
			.then(json => {
				callback(json.items);
			}).catch(()=>{
				callback();
			});
	}

	// custom rendering functions for options and items
	private render = {
		option: function(item, escape) {
			return `<div class="py-2 d-flex">
						<div class="icon me-3">
							<img class="img-fluid" src="${item.owner.avatar_url}" />
						</div>
						<div>
							<div class="mb-1">
								<span class="h4">
									${ escape(item.name) }
								</span>
								<span class="text-muted">by ${ escape(item.owner.login) }</span>
							</div>
							<div class="description">${ escape(item.description) }</div>
						</div>
					</div>`;
		},
		item: function(item, escape) {
			return `<div class="py-2 d-flex">
						<div class="icon me-3">
							<img class="img-fluid" src="${item.owner.avatar_url}" />
						</div>
						<div>
							<div class="mb-1">
								<span class="h4">
									${ escape(item.name) }
								</span>
								<span class="text-muted">by ${ escape(item.owner.login) }</span>
							</div>
							<div class="description">${ escape(item.description) }</div>
						</div>
					</div>`;
		}
	}
}
