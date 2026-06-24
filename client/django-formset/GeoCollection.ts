import {map, latLng, tileLayer, Map, MapOptions} from 'leaflet';
import styles from './GeoCollections.scss';


class LeafletComponent {
	private readonly element: HTMLTextAreaElement;
	private readonly canvasElement: HTMLDivElement;
	private readonly options: MapOptions = {
		center: latLng(47.23, 11.15),
		zoom: 12,
		maxZoom: 18,
	};
	private map?: Map;

	constructor(element: HTMLTextAreaElement) {
		this.element = element;
		this.element.classList.add('dj-concealed');
		this.canvasElement = document.createElement('DIV') as HTMLDivElement;
		this.canvasElement.classList.add('leaflet-map');
		this.element.insertAdjacentElement('afterend', this.canvasElement);
	}

	public async connectedCallback() {
		// initialize the Leaflet map here
		this.map = map(this.canvasElement, this.options);
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
}


export class CascadeLeafletElement extends HTMLTextAreaElement {
	#leaflet: LeafletComponent;

	connectedCallback() {
		this.#leaflet = new LeafletComponent(this);
		this.#leaflet.connectedCallback();
	}

	disconnectedCallback() {
		this.#leaflet.disconnectedCallback();
	}

	get value() : any {
		return this.#leaflet.getValue();
	}
}
