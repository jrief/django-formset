import {
	Control,
	ControlOptions,
	ControlPosition,
	Icon,
	IconOptions,
	LatLng,
	LatLngBounds,
	Layer,
	LeafletKeyboardEvent,
	LeafletMouseEvent,
	Map,
	MapOptions,
	Marker,
	MarkerOptions,
	Popup,
	map,
	latLng,
	LatLngExpression,
	tileLayer,
} from 'leaflet';
import getDataValue from 'lodash.get';
import setDataValue from 'lodash.set';
import isPlainObject from 'lodash.isplainobject';
import {StyleHelpers} from './helpers';
import {TransientFormDialog} from './FormDialog';
import styles from './GeoMap.scss';


const CONTROL_POSITIONS: ReadonlyArray<ControlPosition> = ['topleft', 'topright', 'bottomleft', 'bottomright'] as const;

class GeoMapMarker extends Marker {
	private readonly editor: GeometryEditor;
	public readonly properties: Record<string, any> = {};
	public readonly index: number;

	constructor(editor: GeometryEditor, latlng: LatLng, index: number, popupTemplate: HTMLDivElement, icon: Icon) {
		const options: MarkerOptions = {
			icon: icon,
			draggable: true,
			autoPan: true,
			bubblingMouseEvents: true,
		};
		super(latlng, options);
		this.editor = editor;
		this.index = index;
		this.addTo(this.editor.geomap.map);
		this.attachPopup(popupTemplate);
	}

	private attachPopup(popupTemplate: HTMLDivElement) {
		const popupContent = document.importNode(popupTemplate, true);
		this.editor.geomap.formset!.assignDetachedButtons(popupContent);
		popupContent.querySelectorAll('[df-click="activate"]').forEach((button: Element) => {
			if (button instanceof HTMLButtonElement) {
				button.dataset.identifier = `${this.editor.identifier}:${this.index}`;
			}
		});
		popupContent.querySelector('[name="delete_marker"]')?.addEventListener('click', () => this.deleteMarker());
		const popup = new Popup({closeButton: false, autoClose: true, closeOnClick: true});
		popup.setContent(popupContent);
		this.bindPopup(popup);
	}

	openPopup(latlng?: LatLngExpression): this {
		this.editor.geomap.closeAllDialogs();
		return super.openPopup(latlng);
	}

	closePopup(): this {
		return super.closePopup();
	}

	public initialPlacement() {
		const map = this.editor.geomap.map;
		const mapContainer = map.getContainer();
		mapContainer.classList.add('marker-placement');
		const moveMarker = (event: LeafletMouseEvent) => this.setLatLng(event.latlng);
		const dropMarker = () => {
			map.off('mousemove', moveMarker);
			mapContainer.classList.remove('marker-placement');
		};
		const handleEscape = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				this.deleteMarker();
				dropMarker();
				document.removeEventListener('keydown', handleEscape);
			}
		};
		map.on('mousemove', moveMarker);
		document.addEventListener('keydown', handleEscape);
		map.once('click', dropMarker);
	}

	private deleteMarker() {
		this.removeFrom(this.editor.geomap.map);
		this.editor.deleteLayer(this.index);
	}
}


class GeoMapFormDialog extends TransientFormDialog {
	private readonly geomap: GeoMap;
	private readonly propertiesMap: Record<string, string>;
	private boundLayer: (Layer|null) = null;

	constructor(element: HTMLDialogElement, geomap: GeoMap) {
		super(element, geomap.path);
		this.geomap = geomap;
		this.propertiesMap = JSON.parse(this.formElement.dataset.propertiesMap || '{}');
	}

	public openDialog(button?: DjangoButton) {
		if (this.element.open || !button?.element.dataset.identifier)
			return;

		this.boundLayer = this.geomap.getLayer(button.element.dataset.identifier);
		if (this.boundLayer instanceof GeoMapMarker) {
			for (const [source, target] of Object.entries(this.propertiesMap)) {
				const inputElement = this.formElement.elements.namedItem(source);
				if (!(inputElement instanceof HTMLInputElement || inputElement instanceof HTMLSelectElement || inputElement instanceof HTMLTextAreaElement))
					continue;
				inputElement.value = getDataValue(this.boundLayer.properties, `${this.extension}.${target}`, null);
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
			if (this.boundLayer instanceof GeoMapMarker) {
				for (const [source, target] of Object.entries(this.propertiesMap)) {
					const formField = this.formElement.elements.namedItem(source);
					if (!(formField instanceof HTMLInputElement || formField instanceof HTMLSelectElement || formField instanceof HTMLTextAreaElement))
						continue;
					setDataValue(this.boundLayer.properties, `${this.extension}.${target}`, formField.value);
				}
			}
		}
		super.closeDialog(button, returnValue);
		if (this.boundLayer) {
			this.boundLayer.closePopup();
			this.boundLayer = null;
		}
	}
}


abstract class GeometryEditor {
	public readonly geomap: GeoMap;
	public readonly formDialogs: GeoMapFormDialog[] = [];

	constructor(geomap: GeoMap) {
		this.geomap = geomap;
		this.registerFormDialogs();
	}

	private registerFormDialogs() {
		const dialogs = this.geomap.wrapperElement.querySelectorAll(`:scope > dialog[df-induce-open][aria-labeledby="${this.identifier}"]`);
		for (const dialogElement of dialogs) {
			if (!(dialogElement instanceof HTMLDialogElement))
				return;
			const formDialog = new GeoMapFormDialog(dialogElement, this.geomap);
			this.formDialogs.push(formDialog);
		}
	}

	public closeAllDialogs() {
		this.formDialogs.forEach(dialog => dialog.closeDialog());
	}

	public abstract get identifier(): string;

	public abstract register() : void;

	public abstract resetToInitial() : void;

	public abstract getFeatures() : Record<string, any[]>[];

	public abstract getLayer(index: number) : Layer|null;

	public abstract deleteLayer(index: number) : void;

	public updateOperability(...args: any[]) {
		this.formDialogs.forEach(dialog => dialog.updateOperability(...args));
	}
}


class PointEditor extends GeometryEditor {
	public readonly markers: (GeoMapMarker|null)[] = [];
	private readonly popupTemplate: HTMLDivElement;
	private readonly markerIcon: Icon;

	constructor(geomap: GeoMap, iconOptions: IconOptions) {
		super(geomap);
		const popupTemplate = this.geomap.controlsTemplate.content.querySelector(`[role="tooltip"][aria-labeledby="${this.identifier}"]`);
		if (!(popupTemplate instanceof HTMLDivElement))
			throw new Error('Could not find popup template for [role="tooltip"]');
		this.popupTemplate = popupTemplate;
		this.markerIcon = new Icon(iconOptions);
	}

	public get identifier() {
		return 'point-editor';
	}

	public register() {
		this.setupInitialMarkers();
		this.geomap.map.on('click', this.handleClick);
	}

	public resetToInitial() {
		for (const marker of this.markers) {
			if (marker) {
				marker.removeFrom(this.geomap.map);
			}
		}
		this.markers.splice(0, this.markers.length);
		this.setupInitialMarkers();
	}

	public getFeatures() : Record<string, any[]>[] {
		const features: Record<string, any>[] = [];
		for (const marker of this.markers) {
			if (!marker)
				continue;
			const latlng = marker.getLatLng();
			features.push({
				geometry: {
					type: 'Point',
					coordinates: [latlng.lng, latlng.lat],
				},
				properties: marker.properties,
			});
		}
		return features;
	}

	public getLayer(index: number) : Layer|null {
		return this.markers[index];
	}

	public deleteLayer(index: number) {
		this.markers[index] = null;
	}

	private handleClick = (event: LeafletMouseEvent) => {
		const target = event.originalEvent.target;
		if (!(target instanceof Element) || target.closest('[role="button"]')?.ariaLabel !== 'point-editor')
			return;
		const marker = new GeoMapMarker(this, event.latlng, this.markers.length, this.popupTemplate, this.markerIcon);
		this.markers.push(marker);
		marker.initialPlacement();
	};

	private setupInitialMarkers() {
		if (getDataValue(this.geomap.initialData, 'type') === 'FeatureCollection') {
			const features = getDataValue(this.geomap.initialData, 'features');
			if (Array.isArray(features)) {
				for (const [index, feature] of features.entries()) {
					const geometry = getDataValue(feature, 'geometry');
					if (isPlainObject(geometry) && getDataValue(geometry, 'type') === 'Point') {
						const coordinates = getDataValue(geometry, 'coordinates');
						if (Array.isArray(coordinates) && coordinates.length === 2) {
							const latlng = latLng(coordinates[1] as number, coordinates[0] as number);
							const marker = new GeoMapMarker(this, latlng, index, this.popupTemplate, this.markerIcon);
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
}


const registry: Record<string, new (...args: any[]) => GeometryEditor> = {
	'point-editor': PointEditor,
};


class GeoMap implements Inducible {
	private readonly textAreaElement: HTMLTextAreaElement;
	private readonly baseSelector = '.dj-geomap-wrapper';
	private readonly mapElement: HTMLDivElement;
	public readonly wrapperElement: HTMLDivElement;
	public readonly controlsTemplate: HTMLTemplateElement;
	public formset?: DjangoFormset;
	private resizeObserver?: ResizeObserver;
	public readonly initialData: JSONValue;
	public readonly editors: GeometryEditor[] = [];
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
		this.initialData = JSON.parse(this.textAreaElement.dataset.content as string ?? 'null');
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
		this.resizeObserver = new ResizeObserver((entries) => {
			for (const entry of entries) {
				if (entry.contentBoxSize) {
					this.map.invalidateSize();
				}
			}
		});
		this.resizeObserver.observe(this.wrapperElement);
		const form = this.textAreaElement.form as HTMLFormElement;
		form.addEventListener('reset', this.formResetted);
		form.addEventListener('submitted', this.formSubmitted);
	}

	public disconnectedCallback() {
		this.resizeObserver?.unobserve(this.wrapperElement);
	}

	public get path(): Path {
		return this.textAreaElement.name.split('.');
	}

	private formResetted = () => {
		this.editors.forEach(editor => editor.resetToInitial());
	};

	private formSubmitted = () => {
		this.textAreaElement.checkValidity();
	};

	private createMap() : Map {
		const bbox = getDataValue(this.initialData, 'bbox', [-175, -75, 175, 75]) as number[];
		const bounds = new LatLngBounds([bbox[1], bbox[0]], [bbox[3], bbox[2]]);
		const options: MapOptions = {maxZoom: 18, minZoom: 1, zoom: 10, center: bounds.getCenter()};
		const leafletMap = map(this.mapElement, options);
		leafletMap.setZoom(leafletMap.getBoundsZoom(bounds));
		return leafletMap;
	}

	private extendControls() {
		const self = this;
		const CustomControls = Control.extend({
			onAdd: function(map: Map) {
				const opts = (this as any).options as ControlOptions;
				const controlTemplate = self.controlsTemplate.content.querySelector(`[aria-current="${opts.position}"]`);
				if (!(controlTemplate instanceof HTMLDivElement))
					throw new Error(`Could not find control template for position ${opts.position}`);
				controlTemplate.querySelectorAll('a[aria-label]').forEach((anchor: Element) => {
					if (anchor instanceof HTMLAnchorElement && anchor.ariaLabel && registry[anchor.ariaLabel] instanceof Function) {
						const iconOptions = JSON.parse(anchor.dataset.marker as any) as IconOptions;
						self.editors.push(new registry[anchor.ariaLabel](self, iconOptions));
					}
				});
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
			this.editors.forEach(editor => editor.register());
		}, {once: true});
	}

	public closeAllDialogs() {
		this.editors.forEach(editor => editor.closeAllDialogs());
	}

	public getLayer(identifier: string) : Layer|null {
		const [editorName, index] = [...identifier.split(':')];
		return this.editors.find(editor => editor.identifier === editorName)?.getLayer(Number(index)) ?? null;
	}

	public getValue() : object {
		// return the values from the Leaflet map here
		const bounds = this.map.getBounds();
		const result = {
			type: 'FeatureCollection',
			bbox: bounds ? [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()] : null,
			features: [] as Record<string, any>,
		};
		for (const editor of this.editors) {
			result.features.push(...editor.getFeatures());
		}
		this.textAreaElement.innerText = result.features.length === 0 ? "" : "_has_value_";  // required for validation
		return result;
	}

	public updateOperability(...args: any[]) {
		this.editors.forEach(editor => editor.updateOperability(...args));
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

	get value(): any {
		return this.#geomap.getValue();
	}
}
