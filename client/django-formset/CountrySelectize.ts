import {DjangoSelectize} from './DjangoSelectize';
import {RecursivePartial, TomOption} from 'tom-select/src/types';
import {TomSettings} from 'tom-select/src/types/settings';
import template from 'lodash.template';
import styles from './CountrySelectize.scss';


class CountrySelectize extends DjangoSelectize {
	constructor(element: HTMLSelectElement) {
		super(element);
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = styles;
		this.shadowRoot.insertBefore(declaredStyles, this.shadowRoot.firstChild);
		if (!declaredStyles.sheet)
			throw new Error("Could not create <style> element");
	}

	protected getSettings(tomInput: HTMLSelectElement) : RecursivePartial<TomSettings> {
		const settings = super.getSettings(tomInput);
		const templ = tomInput.parentElement?.querySelector('template.select-country-item');
		if (templ) {
			const renderItem = (data: TomOption) => {
				return template(templ.innerHTML)({...data, code: data.id.toLowerCase()});
			};
			settings.render = {...settings.render, option: renderItem, item: renderItem};
		}
		return settings;
	}
}


const CS = Symbol('CountrySelectize');

export class CountrySelectizeElement extends HTMLSelectElement {
	private [CS]!: CountrySelectize;  // hides internal implementation

	constructor() {
		super();
		this[CS] = new CountrySelectize(this);
	}

	connectedCallback() {
		this[CS].initialize();
	}
}
