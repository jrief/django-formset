import {
	GeoJSON,
	GeoJSONOptions,
	Icon,
	IconOptions,
	LatLng,
	Map,
	MapOptions,
	Marker,
	MarkerOptions,
	PopupOptions,
	TileLayer,
	TileLayerOptions,
	TooltipOptions,
	latLngBounds,
} from 'leaflet';
import getDataValue from 'lodash.get';
import styles from 'django-formset/GeoMap.scss';


class GeoJSONRenderer extends HTMLElement {
	readonly #shadowRoot: ShadowRoot;
	readonly #leaflet: Map;
	static readonly defaultUrlTemplate = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
	static readonly defaultMapOptions: MapOptions = {
		maxZoom: 18,
		minZoom: 1,
		zoom: 9,
		center: new LatLng(47, 9),
		doubleClickZoom: false,
	};
	static readonly defaultTileLayerOptions: TileLayerOptions = {
		tileSize: 512,
		zoomOffset: -1,
		attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
		crossOrigin: true,
		detectRetina: true,
	};
	static observedAttributes = ['json'];

	constructor() {
		super();
		this.#shadowRoot = this.attachShadow({mode: 'closed'});
		const styleSheet = new CSSStyleSheet();
		styleSheet.replace(styles).then(() => {
			styleSheet.insertRule(':host > div {width: 100%; min-height: 150px; height: 100%;}');
			this.#shadowRoot.adoptedStyleSheets.push(styleSheet);
		});
		const divElem = document.createElement('div') as HTMLDivElement;
		this.#shadowRoot.appendChild(divElem);
		this.#leaflet = new Map(divElem, GeoJSONRenderer.defaultMapOptions);
		const tileLayer = new TileLayer(GeoJSONRenderer.defaultUrlTemplate, GeoJSONRenderer.defaultTileLayerOptions);
		this.#leaflet.addLayer(tileLayer);
	}

	attributeChangedCallback(name: string) {
		if (name === 'json') {
			this.#setGeoData();
		}
	}

	disconnectedCallback() {
		this.#leaflet.remove();
	}

	#setGeoData() {
		this.#leaflet.eachLayer(layer => {
			if (layer instanceof GeoJSON) {
				this.#leaflet.removeLayer(layer);
			}
		});
		const geojson = JSON.parse(this.getAttribute('json') ?? '{}');
		const bbox = getDataValue(geojson, 'bbox') as number[];
		const options: GeoJSONOptions = {
			pointToLayer: (feature, latlng) => {
				const options: MarkerOptions = {
					icon: new Icon(feature.properties.marker.icon as IconOptions),
				};
				return new Marker(latlng, options);
			},
			onEachFeature: (feature, layer) => {
				if (feature.properties.popup) {
					const options = feature.properties.popup.options ?? {} as PopupOptions;
					layer.bindPopup(feature.properties.popup.content, options);
				}
				if (feature.properties.tooltip) {
					const options = feature.properties.tooltip.options ?? {} as TooltipOptions;
					layer.bindTooltip(feature.properties.tooltip.content, options);
				}
			}
		};
		const nextLayer = new GeoJSON(geojson, options);
		this.#leaflet.addLayer(nextLayer);
		if (bbox) {
			const bounds = latLngBounds([bbox[1], bbox[0]], [bbox[3], bbox[2]]);
			window.requestIdleCallback(() => {
				this.#leaflet.invalidateSize();
				this.#leaflet.fitBounds(bounds);
				this.#leaflet.flyToBounds(bounds, {animate: false});
			});
		}
	}
}

window.customElements.define('geojson-renderer', GeoJSONRenderer);
