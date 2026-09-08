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


const styleSheet = new CSSStyleSheet();
styleSheet.replaceSync(styles);
styleSheet.insertRule(':host > div {width:100%; height:100%; min-height:150px; z-index:0;}');


class GeoJSONRenderer extends HTMLElement {
	readonly #shadowRoot: ShadowRoot;
	readonly #leaflet: Map;
	static readonly defaultUrlTemplate = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
	static readonly defaultMapOptions: MapOptions = {
		maxZoom: 18,
		minZoom: 1,
		zoom: 9,
		center: new LatLng(51.5, 0),
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
		this.#shadowRoot = this.attachShadow({mode: 'open'});
		try {
			this.#shadowRoot.adoptedStyleSheets.push(styleSheet);
		} catch (e) {
			const styleElem = document.createElement('style');
			styleElem.textContent = styles;
			this.#shadowRoot.appendChild(styleElem);
		}
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
		if (geojson.type !== 'FeatureCollection')
			throw new Error('Invalid GeoJSON');
		geojson['features'] ??= [];
		let filterFunction: (feature: any) => boolean;
		try {
			const filterString = decodeURIComponent(this.getAttribute('filter') ?? 'true');
			filterFunction = new Function('feature', `return ${filterString}`) as (feature: any) => boolean;
		} catch (e) {
			filterFunction = (feature: any) => true;
		}
		const bbox = getDataValue(geojson, 'bbox') as number[];
		const options: GeoJSONOptions = {
			filter: filterFunction,
			pointToLayer: (feature, latlng) => {
				const options: MarkerOptions = {
					icon: new Icon(feature.properties._marker_.icon as IconOptions),
				};
				return new Marker(latlng, options);
			},
			onEachFeature: (feature, layer) => {
				if (feature.properties._popup_) {
					const options = feature.properties._popup_.options ?? {} as PopupOptions;
					layer.bindPopup(feature.properties._popup_.content, options);
				}
				if (feature.properties._tooltip_) {
					const options = feature.properties._tooltip_.options ?? {} as TooltipOptions;
					layer.bindTooltip(feature.properties._tooltip_.content, options);
				}
			},
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
		} else {
			window.requestIdleCallback(() => {
				this.#leaflet.invalidateSize();
			});
		}
	}
}

window.customElements.define('geojson-renderer', GeoJSONRenderer);
