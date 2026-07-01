import {
	Control,
	ControlOptions,
	ControlPosition,
	Icon,
	IconOptions,
	LatLng,
	LatLngBounds,
	LeafletMouseEvent,
	Map,
	MapOptions,
	Marker,
	MarkerOptions,
	Popup,
	map,
	latLng,
	tileLayer, LatLngExpression
} from 'leaflet';
import getDataValue from 'lodash.get';
import setDataValue from 'lodash.set';
import isPlainObject from 'lodash.isplainobject';
import {StyleHelpers} from './helpers';
import {TransientFormDialog} from './FormDialog';
import styles from './GeoMap.scss';


const CONTROL_POSITIONS: ReadonlyArray<ControlPosition> = ['topleft', 'topright', 'bottomleft', 'bottomright'] as const;

const MarkerIcon = new Icon({
	iconUrl: '/static/formset/icons/marker-icon.svg',
	iconSize: [25, 41],
	iconAnchor: [13, 41],
	popupAnchor: [-2, -44],
	shadowUrl: '/static/formset/icons/marker-shadow.png',
	shadowSize: [68, 68],
	shadowAnchor: [22, 68],
} as IconOptions);


class GeoMapMarker extends Marker {
	private readonly geomap: GeoMap;
	public readonly properties: Record<string, any> = {};
	public readonly index: Number;

	constructor(geomap: GeoMap, latlng: LatLng, index: Number) {
		const options: MarkerOptions = {
			icon: MarkerIcon,
			draggable: true,
			autoPan: true,
			bubblingMouseEvents: true,
		};
		super(latlng, options);
		this.geomap = geomap;
		this.addTo(this.geomap.map);
		this.closePopup();
		this.index = index;
	}

	openPopup(latlng?: LatLngExpression): this {
		this.geomap.formDialogs.forEach(dialog => dialog.closeDialog());
		return super.openPopup(latlng);
	}

	public initialPlacement() {
		const mapContainer = this.geomap.map.getContainer();
		mapContainer.classList.add('marker-placement');
		const moveMarker = (event: LeafletMouseEvent) => this.setLatLng(event.latlng);
		this.geomap.map.on('mousemove', moveMarker);
		this.geomap.map.once('click', (event: LeafletMouseEvent) => {
			moveMarker(event);
			this.geomap.map.off('mousemove', moveMarker);
			mapContainer.classList.remove('marker-placement');
		});
	}
}


class GeoMapFormDialog extends TransientFormDialog {
	private readonly geomap: GeoMap;
	private readonly propertiesMap: Record<string, string>;
	private boundMarker: (GeoMapMarker|null) = null;

	constructor(element: HTMLDialogElement, geomap: GeoMap) {
		super(element, geomap.path);
		this.geomap = geomap;
		this.propertiesMap = JSON.parse(this.formElement.dataset.propertiesMap || '{}');
	}

	public openDialog(button?: DjangoButton) {
		if (this.element.open || !button)
			return;
		this.boundMarker = this.geomap.markers.at(Number(button.element.dataset.markerIndex)) ?? null;
		if (this.boundMarker) {
			for (const [source, target] of Object.entries(this.propertiesMap)) {
				const inputElement = this.formElement.elements.namedItem(source);
				if (!(inputElement instanceof HTMLInputElement || inputElement instanceof HTMLSelectElement || inputElement instanceof HTMLTextAreaElement))
					continue;
				inputElement.value = getDataValue(this.boundMarker.properties, `${this.extension}.${target}`, null);
				inputElement.dispatchEvent(new Event('change', {bubbles: true}));
				const groupElement = inputElement.closest('[role="group"]');
				if (groupElement instanceof HTMLElement) {
					groupElement.classList.remove('dj-dirty', 'dj-touched');
					groupElement.classList.add('dj-pristine', 'dj-untouched');
					groupElement.querySelector('.dj-errorlist .dj-placeholder')?.replaceChildren();
				}
			}
		}
		super.openDialog();
	}

	public async closeDialog(button?: DjangoButton, returnValue?: string) {
		if (returnValue === 'apply') {
			this.formElement.dispatchEvent(new Event('submit', {bubbles: true}));
			if (!this.formElement.reportValidity()) {
				// reportValidity() triggers the invalid event for each invalid input field
				return;
			}
			if (this.boundMarker) {
				for (const [source, target] of Object.entries(this.propertiesMap)) {
					const formField = this.formElement.elements.namedItem(source);
					if (!(formField instanceof HTMLInputElement || formField instanceof HTMLSelectElement || formField instanceof HTMLTextAreaElement))
						continue;
					setDataValue(this.boundMarker.properties, `${this.extension}.${target}`, formField.value);
				}
			}
		}
		super.closeDialog(button, returnValue);
		if (this.boundMarker) {
			this.boundMarker.closePopup();
			this.boundMarker = null;
		}
	}
}


class GeoMap implements Inducible {
	private readonly textAreaElement: HTMLTextAreaElement;
	private readonly baseSelector = '.dj-geomap-wrapper';
	private readonly mapElement: HTMLDivElement;
	private readonly wrapperElement: HTMLDivElement;
	private readonly controlsTemplate: HTMLTemplateElement;
	private readonly initialContent: JSONValue;
	private formset?: DjangoFormset;
	private resizeObserver?: ResizeObserver;
	public readonly formDialogs: GeoMapFormDialog[] = [];
	public readonly markers: (GeoMapMarker|null)[] = [];
	public map: Map;

	constructor(element: GeoMapElement) {
		this.textAreaElement = element;
		this.wrapperElement = element.previousElementSibling as HTMLDivElement;
		const controlsTemplate = this.wrapperElement.querySelector('template');
		if (!(controlsTemplate instanceof HTMLTemplateElement))
			throw new Error(`Could not find <template> element in ${this.wrapperElement}`);
		this.controlsTemplate = controlsTemplate;
		this.mapElement = this.wrapperElement?.querySelector('.leaflet-map') as HTMLDivElement;
		if (!(this.mapElement instanceof HTMLDivElement))
			throw new Error(`Could not find .leaflet-map element in ${this.wrapperElement}`);
		this.registerInducer();
		if (!StyleHelpers.stylesAreInstalled(this.baseSelector) && this.wrapperElement.checkVisibility()) {
			this.transferStyles();
		}
		this.textAreaElement.classList.add('dj-concealed');
		this.initialContent = JSON.parse(this.textAreaElement.dataset.content as string ?? 'null');
		this.map = this.createMap();
	}

	public connectedCallback() {
		tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			tileSize: 512,
			zoomOffset: -1,
			attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
			crossOrigin: true,
			detectRetina: true,
		}).addTo(this.map);
		this.extendControls();
		this.registerFormDialogs();
		this.setupMarkers(this.initialContent);
		this.resizeObserver = new ResizeObserver((entries) => {
			for (const entry of entries) {
				if (entry.contentBoxSize) {
					this.map.invalidateSize();
				}
			}
		});
		this.resizeObserver.observe(this.wrapperElement);
	}

	public disconnectedCallback() {
		this.resizeObserver?.unobserve(this.wrapperElement);
	}

	public get path(): Path {
		const path = ['map'];  // TODO: remove hardcoded hack!
		return path;
	}

	private createMap() : Map {
		const bbox = getDataValue(this.initialContent, 'bbox', [-175, -75, 175, 75]) as number[];
		const bounds = new LatLngBounds([bbox[1], bbox[0]], [bbox[3], bbox[2]]);
		const options: MapOptions = {maxZoom: 18, minZoom: 1, zoom: 10, center: bounds.getCenter()};
		const leafletMap = map(this.mapElement, options);
		leafletMap.setZoom(leafletMap.getBoundsZoom(bounds));
		return leafletMap;
	}

	private registerInducer() {
		const formset = this.wrapperElement.closest('django-formset');
		if (!formset)
			return;
		formset.addEventListener('django-formset-connected', (event: Event) => {
			if (!(event instanceof CustomEvent))
				return;
			this.formset = event.detail.formset as DjangoFormset;
			this.formset.registerInducer(this);
			this.markers.forEach(marker => marker !== null && this.bindPopup(marker));
		}, {once: true});
	}

	private setupMarkers(initialData: JSONValue) {
		if (getDataValue(initialData, 'type') === 'FeatureCollection') {
			const features = getDataValue(initialData, 'features');
			if (Array.isArray(features)) {
				for (const [index, feature] of features.entries()) {
					const geometry = getDataValue(feature, 'geometry');
					if (isPlainObject(geometry) && getDataValue(geometry, 'type') === 'Point') {
						const coordinates = getDataValue(geometry, 'coordinates');
						if (Array.isArray(coordinates) && coordinates.length === 2) {
							const latlng = latLng(coordinates[1] as number, coordinates[0] as number);
							const marker = new GeoMapMarker(this, latlng, index);
							const properties = getDataValue(feature, 'properties');
							if (isPlainObject(properties)) {
								Object.assign(marker.properties, properties);
							}
							this.markers.push(marker);
						}
					}
				}
			}
		}
	}

	private deleteMarker(marker: GeoMapMarker) {
		marker.removeFrom(this.map);
		this.markers[this.markers.indexOf(marker)] = null;
	}

	private extendControls() {
		const self = this;
		const CustomControls = Control.extend({
			onAdd: function(map: Map) {
				const opts = (this as any).options as ControlOptions;
				const controlTemplate = self.controlsTemplate.content.querySelector(`[aria-current="${opts.position}"]`);
				if (!(controlTemplate instanceof HTMLDivElement))
					throw new Error(`Could not find control template for position ${opts.position}`);
				return document.importNode(controlTemplate, true);
			},
			onRemove: (map: Map) => {
				// Nothing to do yet
			},
		});
		const customControls = (opts: ControlOptions) => new CustomControls(opts);
		for (let position of CONTROL_POSITIONS) {
			customControls({position: position as ControlPosition}).addTo(this.map);
		}
		this.map.on('click', this.handleClick);
	}

	private handleClick = (event: LeafletMouseEvent) => {
		const target = event.originalEvent.target;
		if (!(target instanceof Element) || target.closest('[role="button"]')?.ariaLabel !== 'map-pin')
			return;
		const marker = new GeoMapMarker(this, event.latlng, this.markers.length);
		this.markers.push(marker);
		marker.initialPlacement();
		this.bindPopup(marker);
	};

	public bindPopup(marker: GeoMapMarker) {
		const popupTemplate = this.controlsTemplate.content.querySelector('[role="tooltip"]');
		if (!(popupTemplate instanceof HTMLDivElement))
			throw new Error('Could not find popup template for [role="tooltip"]');
		const popupContent = document.importNode(popupTemplate, true);
		if (popupContent && this.formset) {
			this.formset.assignDetachedButtons(popupContent);
		}
		popupContent.querySelectorAll('[df-click="activate"]').forEach((button: Element) => {
			if (button instanceof HTMLButtonElement) {
				button.dataset.markerIndex = String(marker.index);
			}
		});
		popupContent.querySelector('[name="delete_marker"]')?.addEventListener('click', () => this.deleteMarker(marker));
		const popup = new Popup({closeButton: false, autoClose: true, closeOnClick: true});
		popup.setContent(popupContent);
		marker.bindPopup(popup);
	}

	private registerFormDialogs() {
		this.wrapperElement.querySelectorAll(':scope > dialog[df-induce-open]').forEach(dialogElement => {
			if (!(dialogElement instanceof HTMLDialogElement))
				return;
			const formDialog = new GeoMapFormDialog(dialogElement, this);
			this.formDialogs.push(formDialog);
		});
	}

	public getValue() : object {
		// return the values from the Leaflet map here
		const bounds = this.map.getBounds();
		const result = {
			type: 'FeatureCollection',
			bbox: bounds ? [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()] : null,
			features: [] as Record<string, any>,
		};
		for (const marker of this.markers) {
			if (!marker?.properties)
				continue;
			const coord = marker.getLatLng();
			result.features.push({
				type: 'Feature',
				geometry: {
					type: 'Point',
					coordinates: [coord.lng, coord.lat],
				},
				properties: marker.properties,
			});
		}
		this.textAreaElement.innerText = result.features.length === 0 ? "" : "_has_value_";  // required for validation
		return result;
	}

	public updateOperability(...args: any[]) {
		this.formDialogs.forEach(dialog => dialog.updateOperability(...args));
	}

	public forceVisibility(formElement: HTMLFormElement) {}

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
						'outline', 'overflow', 'resize',
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
	readonly #geomap: GeoMap;

	constructor() {
		super();
		this.#geomap = new GeoMap(this);
	}

	connectedCallback() {
		this.#geomap.connectedCallback();
	}

	disconnectedCallback() {
		this.#geomap.disconnectedCallback();
	}

	get value() : any {
		return this.#geomap.getValue();
	}
}
