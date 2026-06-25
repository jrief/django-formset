import {Control, map, latLng, tileLayer, Map, MapOptions} from 'leaflet';
import {StyleHelpers, toAbsPath} from './helpers';
import styles from './GeoMap.scss';


class GeoMapComponent {
	private readonly textAreaElement: HTMLTextAreaElement;
	private readonly baseSelector = '[is="django-geo-map"] + div';
	private readonly mapElement: HTMLDivElement;
	private readonly options: MapOptions = {
		center: latLng(47.23, 11.15),
		zoom: 12,
		maxZoom: 18,
	};
	private map?: Map;

	constructor(element: GeoMapElement) {
		this.textAreaElement = element;
		const wrapperDiv = document.createElement('DIV') as HTMLDivElement;
		this.textAreaElement.insertAdjacentElement('afterend', wrapperDiv);
		this.mapElement = document.createElement('DIV') as HTMLDivElement;
		this.mapElement.classList.add('leaflet-map');
		wrapperDiv.appendChild(this.mapElement);
		if (!StyleHelpers.stylesAreInstalled(this.baseSelector) && wrapperDiv.checkVisibility()) {
			this.transferStyles();
		}
		this.textAreaElement.classList.add('dj-concealed');
	}

	public async connectedCallback() {
		// initialize the Leaflet map here
		this.map = map(this.mapElement, this.options);
		tileLayer('https://maptiles.uibk.ac.at/{z}/{x}/{y}.png', {
			tileSize: 512,
			zoomOffset: -1,
			minZoom: 1,
			attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
			crossOrigin: true,
			detectRetina: true,
		}).addTo(this.map);
	}

	public disconnectedCallback() {
		// clean up the Leaflet map here
	}

	public getValue() {
		// return the values from the Leaflet map here
		return {};
	}

	private transferStyles() {
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		if (!declaredStyles.sheet)
			throw new Error("Could not create <style> element");
		const sheet = declaredStyles.sheet;

		let loaded = false;
		for (let index = 0; index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case this.baseSelector:
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'height', 'background-image', 'border-style', 'border-width', 'border-radius', 'box-shadow',
						'outline', 'resize',
					]);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					loaded = true;
					break;
				default:
					break;
			}
		}

		// border color may change during runtime
		StyleHelpers.replaceMediaQueryStyles(
			-1,
			sheet,
			this.baseSelector,
			{'--border-color': 'border-color'},
			this.textAreaElement,
		);

		if (!loaded)
			throw new Error(`Could not load styles for ${this.baseSelector}`);
	}

}


export class GeoMapElement extends HTMLTextAreaElement {
	#geomap: GeoMapComponent;

	constructor() {
		super();
		this.#geomap = new GeoMapComponent(this);
	}

	connectedCallback() {
		this.#geomap.connectedCallback();
	}

	disconnectedCallback() {
		this.#geomap.disconnectedCallback();
	}
}
