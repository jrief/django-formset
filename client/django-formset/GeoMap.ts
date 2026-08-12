import {
	Control,
	ControlOptions,
	ControlPosition,
	DivIcon,
	GeoJSON,
	Icon,
	IconOptions,
	LatLng,
	LatLngExpression,
	Layer,
	LayerGroup,
	LeafletEvent,
	LeafletMouseEvent,
	Map,
	MapOptions,
	Marker,
	MarkerOptions,
	Polyline,
	PolylineOptions,
	Polygon,
	Popup,
	Tooltip,
	TooltipOptions,
	latLngBounds,
	polyline,
	tileLayer,
} from 'leaflet';
import getDataValue from 'lodash.get';
import setDataValue from 'lodash.set';
import isEqual from 'lodash.isequal';
import isPlainObject from 'lodash.isplainobject';
import {StyleHelpers} from './helpers';
import {TransientFormDialog} from './FormDialog';
import styles from './GeoMap.scss';


const CONTROL_POSITIONS: ReadonlyArray<ControlPosition> = ['topleft', 'topright', 'bottomleft', 'bottomright'] as const;

class GeoMapFormDialog extends TransientFormDialog {
	private readonly geomap: GeoMap;
	private readonly propertiesMap: Record<string, string>;
	private boundLayer: (Layer|null) = null;

	constructor(element: HTMLDialogElement, geomap: GeoMap) {
		super(element, geomap.path);
		this.geomap = geomap;
		this.propertiesMap = JSON.parse(this.formElement.dataset.propertiesMap ?? '{}');
	}

	public openDialog(button?: DjangoButton) {
		if (this.element.open || !button?.element.dataset.identifier)
			return;

		this.boundLayer = this.geomap.getLayer(button.element.dataset.identifier);
		const properties = (this.boundLayer as any).properties;
		if (isPlainObject(properties)) {
			for (const [source, target] of Object.entries(this.propertiesMap)) {
				const inputElement = this.formElement.elements.namedItem(source);
				if (!(inputElement instanceof HTMLInputElement || inputElement instanceof HTMLSelectElement || inputElement instanceof HTMLTextAreaElement))
					continue;
				inputElement.value = getDataValue(properties, `${this.extension}.${target}`, null);
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
			if (isPlainObject((this.boundLayer as any).properties)) {
				for (const [source, target] of Object.entries(this.propertiesMap)) {
					const formField = this.formElement.elements.namedItem(source);
					if (!(formField instanceof HTMLInputElement || formField instanceof HTMLSelectElement || formField instanceof HTMLTextAreaElement))
						continue;
					setDataValue((this.boundLayer as any).properties, `${this.extension}.${target}`, formField.value);
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
	protected readonly popupTemplate: HTMLDivElement;
	public readonly formDialogs: GeoMapFormDialog[] = [];
	protected readonly anchor: HTMLAnchorElement;

	constructor(geomap: GeoMap, anchor: HTMLAnchorElement) {
		this.geomap = geomap;
		this.anchor = anchor;
		const popupTemplate = this.geomap.controlsTemplate.content.querySelector(`[role="tooltip"][aria-labeledby="${this.identifier}"]`);
		if (!(popupTemplate instanceof HTMLDivElement))
			throw new Error('Could not find popup template for [role="tooltip"]');
		this.popupTemplate = popupTemplate;
		this.registerFormDialogs();
		//this.registerTooltip();
	}

	private registerFormDialogs() {
		const dialogs = this.geomap.wrapperElement.querySelectorAll(`:scope > dialog[df-induce-open][aria-describedby="${this.identifier}"]`);
		for (const dialogElement of dialogs) {
			if (!(dialogElement instanceof HTMLDialogElement))
				return;
			const formDialog = new GeoMapFormDialog(dialogElement, this.geomap);
			this.formDialogs.push(formDialog);
		}
	}

	// private registerTooltip() {
	// 	const latlng = this.anchor
	// 	const tooltip = new Tooltip(latlng, );
	// 	this.anchor.addEventListener('mouseenter', showTooltip);
	// 	this.anchor.addEventListener('mouseleave', hideTooltip);
	// }

	public closeAllDialogs() {
		this.formDialogs.forEach(dialog => dialog.closeDialog());
	}

	public get identifier()  {
		return this.anchor.ariaDescription;
	}

	public abstract register() : void;

	public abstract setInitialData(initialData: JSONValue) : void;

	public abstract clear() : void;

	public abstract getFeatures() : Record<string, any[]>[];

	public abstract getLayer(index: number) : Layer|null;

	public abstract deleteLayer(index: number) : void;

	public updateOperability(...args: any[]) {
		this.formDialogs.forEach(dialog => dialog.updateOperability(...args));
	}
}


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
		this.addTo(this.editor.geomap);
		this.attachPopup(popupTemplate);
	}

	public get identifier(): string {
		return `${this.editor.identifier}:${this.index}`;
	}

	private attachPopup(popupTemplate: HTMLDivElement) {
		const popupContent = document.importNode(popupTemplate, true);
		this.editor.geomap.formset!.assignDetachedButtons(popupContent);
		popupContent.querySelectorAll('[df-click="activate"]').forEach((button: Element) => {
			if (button instanceof HTMLButtonElement) {
				button.dataset.identifier = this.identifier;
			}
		});
		popupContent.querySelector('[name="delete_layer"]')?.addEventListener('click', () => this.deleteMarker());
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
		const map = this.editor.geomap;
		const mapContainer = map.getContainer();
		mapContainer.classList.add('marker-placement');
		const moveMarker = (event: LeafletMouseEvent) => this.setLatLng(event.latlng);
		const dropMarker = () => {
			map.off('mousemove', moveMarker);
			document.removeEventListener('keydown', handleEscape);
			mapContainer.classList.remove('marker-placement');
			this.editor.geomap.getValue();  // required for validation
		};
		const handleEscape = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				this.deleteMarker();
				dropMarker();
				document.removeEventListener('keydown', handleEscape);
			}
		};
		map.on('mousemove', moveMarker);
		map.once('click', dropMarker);
		document.addEventListener('keydown', handleEscape);
	}

	public deleteMarker() {
		this.editor.closeAllDialogs();
		this.removeFrom(this.editor.geomap);
		this.editor.deleteLayer(this.index);
	}
}


class PointEditor extends GeometryEditor {
	public readonly markers: (GeoMapMarker|null)[] = [];
	private readonly markerIcon: Icon;

	constructor(geomap: GeoMap, anchor: HTMLAnchorElement, iconOptions: IconOptions) {
		super(geomap, anchor);
		this.markerIcon = new Icon(iconOptions);
	}

	public register() {
		this.geomap.on('click', this.handleClick);
	}

	public setInitialData(initialData: JSONValue) {
		if (getDataValue(initialData, 'type') === 'FeatureCollection') {
			const features = getDataValue(initialData, 'features');
			if (Array.isArray(features)) {
				for (const feature of features) {
					if (String(getDataValue(feature, 'id', '')).split(':')[0] !== this.identifier)
						continue;
					const geometry = getDataValue(feature, 'geometry');
					if (isPlainObject(geometry) && getDataValue(geometry, 'type') === 'Point') {
						const coordinates = getDataValue(geometry, 'coordinates');
						if (Array.isArray(coordinates) && coordinates.length === 2) {
							const latlng = GeoJSON.coordsToLatLng(coordinates as [number, number]);
							const marker = new GeoMapMarker(this, latlng, this.markers.length, this.popupTemplate, this.markerIcon);
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

	public clear() {
		for (const marker of this.markers) {
			if (marker) {
				marker.deleteMarker();
			}
		}
		this.markers.length = 0;
	}

	public getFeatures() : Record<string, any[]>[] {
		const features: Record<string, any>[] = [];
		for (const marker of this.markers) {
			if (marker) {
				features.push({
					...marker.toGeoJSON(),
					properties: marker.properties,
					id: marker.identifier,
				});
			}
		}
		return features;
	}

	public getLayer(index: number) : Layer|null {
		return this.markers[index];
	}

	public deleteLayer(index: number) {
		this.markers[index]?.unbindPopup();
		this.markers[index] = null;
	}

	private handleClick = (event: LeafletMouseEvent) => {
		const target = event.originalEvent.target;
		if (!(target instanceof Element) || target.closest('[role="button"]')?.ariaDescription !== this.anchor.ariaDescription)
			return;
		const marker = new GeoMapMarker(this, event.latlng, this.markers.length, this.popupTemplate, this.markerIcon);
		this.markers.push(marker);
		marker.initialPlacement();
	};
}


class VertexMarker extends Marker {
	static readonly vertexIcon = new DivIcon({
		className: 'leaflet-div-icon vertex-marker',
		iconSize: [10, 10],
		iconAnchor: [5, 5],
	});
	static readonly halfwayOpacity = 0.7;
	private readonly path: GeoMapPolyline|GeoMapPolygon;

	constructor(latlng: LatLng, path: GeoMapPolyline|GeoMapPolygon, halfway: boolean) {
		const options: MarkerOptions = {
			icon: VertexMarker.vertexIcon,
			draggable: true,
			opacity: halfway ? VertexMarker.halfwayOpacity : 1.0,
		};
		super(latlng, options);
		this.path = path;
		this.on('drag', this.dragVertex);
		this.on('click', this.deleteVertex);
	}

	private dragVertex = (event: LeafletEvent) => {
		const latlng = (event as LeafletMouseEvent).latlng;
		if (latlng instanceof LatLng) {
			const index = this.path.vertexMarkers.indexOf(this);
			this.path.updateVertices(index, latlng);
		}
	};

	private deleteVertex = (event: LeafletEvent) => {
		const index = this.path.vertexMarkers.indexOf(this);
		if (index % 2 === 0) {
			this.path.deleteVertex(index);
		}
	};
}


class GeoMapPolyline extends Polyline {
	private readonly editor: GeometryEditor;
	public readonly properties: Record<string, any> = {};
	public readonly index: number;
	public readonly group: LayerGroup;
	private tempVertex: Polyline|null = null;  // temporary vertex moving with the cursor
	public vertexMarkers: VertexMarker[] = [];

	constructor(editor: GeometryEditor, latlngs: LatLngExpression[], index: number, popupTemplate: HTMLDivElement) {
		const options: PolylineOptions = {
			bubblingMouseEvents: true,
		};
		super(latlngs, options);
		this.editor = editor;
		this.index = index;
		this.group = new LayerGroup();
		this.group.addTo(editor.geomap);
		this.addTo(this.group);
		this.attachPopup(popupTemplate);
	}

	public get identifier(): string {
		return `${this.editor.identifier}:${this.index}`;
	}

	private attachPopup(popupTemplate: HTMLDivElement) {
		const popupContent = document.importNode(popupTemplate, true);
		this.editor.geomap.formset!.assignDetachedButtons(popupContent);
		popupContent.querySelectorAll('[df-click="activate"]').forEach((button: Element) => {
			if (button instanceof HTMLButtonElement) {
				button.dataset.identifier = this.identifier;
			}
		});
		popupContent.querySelector('[name="delete_layer"]')?.addEventListener('click', () => this.deletePolyline());
		const popup = new Popup({closeButton: false, autoClose: true, closeOnClick: true});
		popup.setContent(popupContent);
		this.bindPopup(popup);
	}

	public initialPlacement() {
		const mapContainer = this.editor.geomap.getContainer();
		mapContainer.classList.add('marker-placement');
		const moveVertex = (event: LeafletMouseEvent) => {
			if (this.tempVertex) {
				const firstLatLng = this.tempVertex.getLatLngs()[0] as LatLng;
				this.tempVertex.setLatLngs([firstLatLng, event.latlng]);
			}
		};
		const addVertex = (event: LeafletMouseEvent) => {
			if (this.tempVertex) {
				this.tempVertex.setLatLngs([event.latlng, event.latlng]);
			} else {
				const options: PolylineOptions = {
					bubblingMouseEvents: false,
					dashArray: "2 4",
					weight: 1.5,
				};
				this.tempVertex = polyline([event.latlng, event.latlng], options);
				this.tempVertex.addTo(this.group);
			}
			this.addLatLng(event.latlng);
		};
		const finishPolyline = (event: LeafletMouseEvent) => {
			const latlngs = this.getLatLngs() as LatLng[];
			if (latlngs.length > 2) {
				if (isEqual(latlngs[latlngs.length - 1], latlngs[latlngs.length - 2])) {
					latlngs.pop();  // added by second click in dblclick
				}
				this.setVertexMarkers(latlngs);
			} else {
				latlngs.length = 0;
			}
			this.setLatLngs(latlngs);
			if (this.tempVertex) {
				this.group.removeLayer(this.tempVertex);
				this.tempVertex = null;
			}
			this.editor.geomap.off('mousemove', moveVertex);
			this.editor.geomap.off('click', addVertex);
			document.removeEventListener('keydown', handleEscape);
			mapContainer.classList.remove('marker-placement');
			event.originalEvent.stopPropagation();
		};
		const handleEscape = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				this.group.removeFrom(this.editor.geomap);
				this.editor.deleteLayer(this.index);
				this.editor.geomap.off('mousemove', moveVertex);
				this.editor.geomap.off('click', addVertex);
				mapContainer.classList.remove('marker-placement');
				document.removeEventListener('keydown', handleEscape);
			}
		};
		this.editor.geomap.on('mousemove', moveVertex);
		this.editor.geomap.on('click', addVertex);
		this.editor.geomap.once('dblclick', finishPolyline);
		document.addEventListener('keydown', handleEscape);
	}

	public setVertexMarkers(latlngs: LatLng[]) {
		let prevLatLng: LatLng|null = null;
		for (const latlng of latlngs) {
			if (prevLatLng) {
				const vertextMarker = new VertexMarker(latLngBounds(prevLatLng, latlng).getCenter(), this, true);
				vertextMarker.addTo(this.group);
				this.vertexMarkers.push(vertextMarker);
			}
			const vertexMarker = new VertexMarker(latlng, this, false);
			vertexMarker.addTo(this.group);
			this.vertexMarkers.push(vertexMarker);
			prevLatLng = latlng;
		}
	}

	public updateVertices(index: number, latlng: LatLng) {
		const latlngs = this.getLatLngs() as LatLng[];
		if (index % 2 === 1) {
			// halfway – insert a vertex marker
			latlngs.splice((index + 1) / 2, 0, latlng);
			this.vertexMarkers[index].setOpacity(1.0);
			let prevVertexMarker = this.vertexMarkers[index - 1];
			prevVertexMarker = new VertexMarker(latLngBounds(prevVertexMarker.getLatLng(), latlng).getCenter(), this, true);
			prevVertexMarker.addTo(this.group);
			let nextVertexMarker = this.vertexMarkers[index + 1];
			nextVertexMarker = new VertexMarker(latLngBounds(latlng, nextVertexMarker.getLatLng()).getCenter(), this, true);
			nextVertexMarker.addTo(this.group);
			this.vertexMarkers.splice(index, 0, prevVertexMarker);
			this.vertexMarkers.splice(index + 2, 0, nextVertexMarker);
		} else {
			latlngs[index / 2] = latlng;
			const prevVertexMarker = this.vertexMarkers[index - 1];
			if (prevVertexMarker) {
				prevVertexMarker.setLatLng(latLngBounds(latlngs[index / 2 - 1], latlng).getCenter());
			}
			const nextVertexMarker = this.vertexMarkers[index + 1];
			if (nextVertexMarker) {
				nextVertexMarker.setLatLng(latLngBounds(latlng, latlngs[index / 2 + 1]).getCenter());
			}
		}
		this.setLatLngs(latlngs);
	}

	public deleteVertex(index: number) {
		const latlngs = this.getLatLngs() as LatLng[];
		const vertexMarker = this.vertexMarkers[index];
		if (index === 0) {
			this.vertexMarkers.splice(0, 2).forEach(marker => this.group.removeLayer(marker));
		} else {
			if (index < this.vertexMarkers.length - 1) {
				const [nextVertexMarker] = this.vertexMarkers.splice(index + 1, 1);
				this.group.removeLayer(nextVertexMarker);
			} else {
				this.group.removeLayer(this.vertexMarkers.pop() as Layer);
			}
			const [prevVertexMarker] = this.vertexMarkers.splice(index - 1, 1);
			this.group.removeLayer(prevVertexMarker);
		}
		if (latlngs.length <= 2) {
			this.deletePolyline();
		} else {
			index /= 2;
			if (index < latlngs.length - 1) {
				if (index === 0) {
					// this.vertexMarkers[this.vertexMarkers.length - 1].setLatLng(latLngBounds([latlngs[latlngs.length - 1], latlngs[1]]).getCenter());
				} else {
					vertexMarker.setLatLng(latLngBounds([latlngs[index - 1], latlngs[index + 1]]).getCenter());
				}
				vertexMarker.setOpacity(VertexMarker.halfwayOpacity);
			}
			latlngs.splice(index, 1);
			this.setLatLngs(latlngs);
		}
	}

	public deletePolyline() {
		this.editor.closeAllDialogs();
		this.vertexMarkers.forEach(marker => this.group.removeLayer(marker));
		this.vertexMarkers.length = 0;
		this.group.removeLayer(this);
		this.group.removeFrom(this.editor.geomap);
		this.editor.deleteLayer(this.index);
	}
}


class PolylineEditor extends GeometryEditor {
	public readonly polylines: (GeoMapPolyline | null)[] = [];

	constructor(geomap: GeoMap, anchor: HTMLAnchorElement) {
		super(geomap, anchor);
	}

	public register() {
		this.geomap.on('click', this.handleClick);
	}

	public getLayer(index: number) : Layer|null {
		return this.polylines[index];
	}

	public deleteLayer(index: number) {
		this.polylines[index]?.unbindPopup();
		this.polylines[index] = null;
	}

	private handleClick = (event: LeafletMouseEvent) => {
		const target = event.originalEvent.target;
		if (!(target instanceof Element) || target.closest('[role="button"]')?.ariaDescription !== this.anchor.ariaDescription)
			return;
		const polyline = new GeoMapPolyline(this, [], this.polylines.length, this.popupTemplate);
		this.polylines.push(polyline);
		polyline.initialPlacement();
	};

	public setInitialData(initialData: JSONValue) {
		if (getDataValue(initialData, 'type') === 'FeatureCollection') {
			const features = getDataValue(initialData, 'features');
			if (Array.isArray(features)) {
				for (const feature of features) {
					if (String(getDataValue(feature, 'id', '')).split(':')[0] !== this.identifier)
						continue;
					const geometry = getDataValue(feature, 'geometry');
					if (isPlainObject(geometry) && getDataValue(geometry, 'type') === 'LineString') {
						const latlngs = (GeoJSON.geometryToLayer(geometry as any) as any).getLatLngs() as LatLng[];
						const polyline = new GeoMapPolyline(this, latlngs, this.polylines.length, this.popupTemplate);
						const properties = getDataValue(feature, 'properties');
						if (isPlainObject(properties)) {
							Object.assign(polyline.properties, properties);
						}
						polyline.setVertexMarkers(latlngs);
						this.polylines.push(polyline);
					}
				}
			}
		}
	}

	public clear() {
		for (const polyline of this.polylines) {
			if (polyline) {
				polyline.deletePolyline();
			}
		}
		this.polylines.length = 0;
	}

	public getFeatures() : Record<string, any[]>[] {
		const features: Record<string, any>[] = [];
		for (const polyline of this.polylines) {
			if (polyline) {
				features.push({
					...polyline.toGeoJSON(),
					properties: polyline.properties,
					id: polyline.identifier,
				});
			}
		}
		return features;
	}
}


class GeoMapPolygon extends Polygon {
	private readonly editor: GeometryEditor;
	public readonly properties: Record<string, any> = {};
	public readonly index: number;
	public readonly group: LayerGroup;
	private tempVertex: Polyline|null = null;  // temporary vertex moving with the cursor
	public vertexMarkers: VertexMarker[] = [];

	constructor(editor: GeometryEditor, latlngs: LatLngExpression[], index: number, popupTemplate: HTMLDivElement) {
		const options: PolylineOptions = {
			bubblingMouseEvents: true,
		};
		super(latlngs, options);
		this.editor = editor;
		this.index = index;
		this.group = new LayerGroup();
		this.group.addTo(editor.geomap);
		this.addTo(this.group);
		this.attachPopup(popupTemplate);
	}

	public get identifier(): string {
		return `${this.editor.identifier}:${this.index}`;
	}

	private attachPopup(popupTemplate: HTMLDivElement) {
		const popupContent = document.importNode(popupTemplate, true);
		this.editor.geomap.formset!.assignDetachedButtons(popupContent);
		popupContent.querySelectorAll('[df-click="activate"]').forEach((button: Element) => {
			if (button instanceof HTMLButtonElement) {
				button.dataset.identifier = this.identifier;
			}
		});
		popupContent.querySelector('[name="delete_layer"]')?.addEventListener('click', () => this.deletePolygon());
		const popup = new Popup({closeButton: false, autoClose: true, closeOnClick: true});
		popup.setContent(popupContent);
		this.bindPopup(popup);
	}

	public initialPlacement() {
		const mapContainer = this.editor.geomap.getContainer();
		mapContainer.classList.add('marker-placement');
		const moveVertex = (event: LeafletMouseEvent) => {
			if (this.tempVertex) {
				const latLngs = this.getLatLngs()[0] as LatLng[];
				const lastLatLng = this.tempVertex.getLatLngs()[0] as LatLng;
				if (latLngs.length < 2) {
					this.tempVertex.setLatLngs([lastLatLng, event.latlng]);
				} else {
					this.tempVertex.setLatLngs([lastLatLng, event.latlng, latLngs[0]]);
				}
			}
		};
		const addVertex = (event: LeafletMouseEvent) => {
			if (this.tempVertex) {
				this.tempVertex.setLatLngs([event.latlng, event.latlng]);
			} else {
				const options: PolylineOptions = {
					bubblingMouseEvents: false,
					dashArray: "2 4",
					weight: 1.5,
				};
				this.tempVertex = polyline([event.latlng, event.latlng], options);
				this.tempVertex.addTo(this.group);
			}
			this.addLatLng(event.latlng);
		};
		const finishPolygon = (event: LeafletMouseEvent) => {
			const latlngs = this.getLatLngs()[0] as LatLng[];
			if (latlngs.length > 2) {
				if (isEqual(latlngs[latlngs.length - 1], latlngs[latlngs.length - 2])) {
					latlngs.pop();  // added by second click in dblclick
				}
				this.setVertexMarkers(latlngs);
			} else {
				latlngs.length = 0;
			}
			this.setLatLngs(latlngs);
			if (this.tempVertex) {
				this.group.removeLayer(this.tempVertex);
				this.tempVertex = null;
			}
			this.editor.geomap.off('mousemove', moveVertex);
			this.editor.geomap.off('click', addVertex);
			document.removeEventListener('keydown', handleEscape);
			mapContainer.classList.remove('marker-placement');
			event.originalEvent.stopPropagation();
			// this.closePopup();
		};
		const handleEscape = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				this.group.removeFrom(this.editor.geomap);
				this.editor.deleteLayer(this.index);
				this.editor.geomap.off('mousemove', moveVertex);
				this.editor.geomap.off('click', addVertex);
				mapContainer.classList.remove('marker-placement');
				document.removeEventListener('keydown', handleEscape);
			}
		};
		this.editor.geomap.on('mousemove', moveVertex);
		this.editor.geomap.on('click', addVertex);
		this.editor.geomap.once('dblclick', finishPolygon);
		document.addEventListener('keydown', handleEscape);
	}

	public setVertexMarkers(latlngs: LatLng[]) {
		let prevLatLng: LatLng|null = null;
		for (const latlng of latlngs) {
			if (prevLatLng) {
				const vertextMarker = new VertexMarker(latLngBounds(prevLatLng, latlng).getCenter(), this, true);
				vertextMarker.addTo(this.group);
				this.vertexMarkers.push(vertextMarker);
			}
			const vertexMarker = new VertexMarker(latlng, this, false);
			vertexMarker.addTo(this.group);
			this.vertexMarkers.push(vertexMarker);
			prevLatLng = latlng;
		}
		if (prevLatLng) {
			const vertextMarker = new VertexMarker(latLngBounds(prevLatLng, latlngs[0]).getCenter(), this, true);
			vertextMarker.addTo(this.group);
			this.vertexMarkers.push(vertextMarker);
		}
	}

	public updateVertices(index: number, latlng: LatLng) {
		const latlngs = this.getLatLngs()[0] as LatLng[];
		if (index % 2 === 1) {
			// halfway – insert a vertex marker
			latlngs.splice((index + 1) / 2, 0, latlng);
			this.vertexMarkers[index].setOpacity(1.0);
			let prevVertexMarker = this.vertexMarkers[index - 1];
			prevVertexMarker = new VertexMarker(latLngBounds(prevVertexMarker.getLatLng(), latlng).getCenter(), this, true);
			prevVertexMarker.addTo(this.group);
			let nextVertexMarker = index === this.vertexMarkers.length - 1 ? this.vertexMarkers[0] : this.vertexMarkers[index + 1];
			nextVertexMarker = new VertexMarker(latLngBounds(latlng, nextVertexMarker.getLatLng()).getCenter(), this, true);
			nextVertexMarker.addTo(this.group);
			this.vertexMarkers.splice(index, 0, prevVertexMarker);
			this.vertexMarkers.splice(index + 2, 0, nextVertexMarker);
		} else {
			latlngs[index / 2] = latlng;
			if (index === 0) {
				const prevVertexMarker = this.vertexMarkers[this.vertexMarkers.length - 1];
				prevVertexMarker.setLatLng(latLngBounds(latlngs[this.vertexMarkers.length / 2 - 1], latlng).getCenter());
			} else {
				const prevVertexMarker = this.vertexMarkers[index - 1];
				prevVertexMarker.setLatLng(latLngBounds(latlngs[index / 2 - 1], latlng).getCenter());
			}
			const nextVertexMarker = this.vertexMarkers[index + 1];
			if (index === this.vertexMarkers.length - 2) {
				nextVertexMarker.setLatLng(latLngBounds(latlng, latlngs[0]).getCenter());
			} else {
				nextVertexMarker.setLatLng(latLngBounds(latlng, latlngs[index / 2 + 1]).getCenter());
			}
		}
		this.setLatLngs(latlngs);
	}

	public deleteVertex(index: number) {
		const latlngs = this.getLatLngs()[0] as LatLng[];
		console.log('delete vertex: ', latlngs.length, index);
		const vertexMarker = this.vertexMarkers[index];
		if (index === 0) {
			this.vertexMarkers.splice(0, 2).forEach(marker => this.group.removeLayer(marker));
		} else {
			const [nextVertexMarker] = this.vertexMarkers.splice(index + 1, 1);
			this.group.removeLayer(nextVertexMarker);
			const [prevVertexMarker] = this.vertexMarkers.splice(index - 1, 1);
			this.group.removeLayer(prevVertexMarker);
		}
		if (latlngs.length <= 2) {
			this.deletePolygon();
		} else {
			index /= 2;
			if (index < latlngs.length - 1) {
				if (index === 0) {
					this.vertexMarkers[this.vertexMarkers.length - 1].setLatLng(latLngBounds([latlngs[latlngs.length - 1], latlngs[1]]).getCenter());
				} else {
					vertexMarker.setLatLng(latLngBounds([latlngs[index - 1], latlngs[index + 1]]).getCenter());
				}
				vertexMarker.setOpacity(VertexMarker.halfwayOpacity);
			} else {
				vertexMarker.setLatLng(latLngBounds([latlngs[index - 1], latlngs[0]]).getCenter());
				vertexMarker.setOpacity(VertexMarker.halfwayOpacity);
			}
			latlngs.splice(index, 1);
			this.setLatLngs(latlngs);
		}
	}

	public deletePolygon() {
		this.editor.closeAllDialogs();
		this.vertexMarkers.forEach(marker => this.group.removeLayer(marker));
		this.vertexMarkers.length = 0;
		this.group.removeLayer(this);
		this.group.removeFrom(this.editor.geomap);
		this.editor.deleteLayer(this.index);
	}
}


class PolygonEditor extends GeometryEditor {
	public readonly polygones: (GeoMapPolygon | null)[] = [];

	constructor(geomap: GeoMap, anchor: HTMLAnchorElement) {
		super(geomap, anchor);
	}

	public register() {
		this.geomap.on('click', this.handleClick);
	}

	public getLayer(index: number) : Layer|null {
		return this.polygones[index];
	}

	public deleteLayer(index: number) {
		this.polygones[index]?.unbindPopup();
		this.polygones[index] = null;
	}

	private handleClick = (event: LeafletMouseEvent) => {
		const target = event.originalEvent.target;
		if (!(target instanceof Element) || target.closest('[role="button"]')?.ariaDescription !== this.anchor.ariaDescription)
			return;
		const polygon = new GeoMapPolygon(this, [], this.polygones.length, this.popupTemplate);
		this.polygones.push(polygon);
		polygon.initialPlacement();
	};

	public setInitialData(initialData: JSONValue) {
		if (getDataValue(initialData, 'type') === 'FeatureCollection') {
			const features = getDataValue(initialData, 'features');
			if (Array.isArray(features)) {
				for (const feature of features) {
					if (String(getDataValue(feature, 'id', '')).split(':')[0] !== this.identifier)
						continue;
					const geometry = getDataValue(feature, 'geometry');
					if (isPlainObject(geometry) && getDataValue(geometry, 'type') === 'Polygon') {
						const latlngs = (GeoJSON.geometryToLayer(geometry as any) as any).getLatLngs()[0] as LatLng[];
						const polygon = new GeoMapPolygon(this, latlngs, this.polygones.length, this.popupTemplate);
						const properties = getDataValue(feature, 'properties');
						if (isPlainObject(properties)) {
							Object.assign(polygon.properties, properties);
						}
						polygon.setVertexMarkers(latlngs);
						this.polygones.push(polygon);
					}
				}
			}
		}
	}

	public clear() {
		for (const polygon of this.polygones) {
			if (polygon) {
				polygon.deletePolygon();
			}
		}
		this.polygones.length = 0;
	}

	public getFeatures() : Record<string, any[]>[] {
		const features: Record<string, any>[] = [];
		for (const polygon of this.polygones) {
			if (polygon) {
				features.push({
					...polygon.toGeoJSON(),
					properties: polygon.properties,
					id: polygon.identifier,
				});
			}
		}
		return features;
	}
}


const registry: Record<string, new (geomap: GeoMap, anchor: HTMLAnchorElement, ...args: any[]) => GeometryEditor> = {
	PointEditor,
	PolylineEditor,
	PolygonEditor,
};


class GeoMap extends Map implements Inducible {
	private readonly textAreaElement: HTMLTextAreaElement;
	private readonly baseSelector = '.dj-geomap-wrapper';
	public readonly wrapperElement: HTMLDivElement;
	public readonly controlsTemplate: HTMLTemplateElement;
	public formset?: DjangoFormset;
	private readonly intersectionObserver?: IntersectionObserver;
	private readonly mutationObserver: MutationObserver;
	private resizeObserver?: ResizeObserver;
	public initialData: JSONValue = null;
	public readonly editors: Record<string, GeometryEditor> = {};

	constructor(element: GeoMapElement) {
		const wrapperElement = element.previousElementSibling as HTMLDivElement;
		const mapElement = wrapperElement?.querySelector('.leaflet-map') as HTMLDivElement;
		if (!(mapElement instanceof HTMLDivElement))
			throw new Error(`Could not find .leaflet-map element in ${wrapperElement}`);
		const options: MapOptions = {maxZoom: 18, minZoom: 1, zoom: 10, center: new LatLng(0, 0)};
		super(mapElement, options);
		this.textAreaElement = element;
		this.wrapperElement = wrapperElement;
		const controlsTemplate = wrapperElement.querySelector('template');
		if (!(controlsTemplate instanceof HTMLTemplateElement))
			throw new Error(`Could not find <template> element in ${wrapperElement}`);
		this.controlsTemplate = controlsTemplate;
		this.registerInducer();
		if (!StyleHelpers.stylesAreInstalled(this.baseSelector)) {
			if (wrapperElement.checkVisibility()) {
				this.transferStyles();
				this.concealTextArea();
			} else {
				this.intersectionObserver = new IntersectionObserver(entries => {
					entries.forEach(entry => {
						if (entry.isIntersecting) {
							if (!StyleHelpers.stylesAreInstalled(this.baseSelector)) {
								this.transferStyles();
							}
							this.concealTextArea();
						}
					});
				});
				this.intersectionObserver.observe(wrapperElement);
			}
		}
		this.mutationObserver = new MutationObserver(this.attributesChanged);
		this.mutationObserver.observe(this.textAreaElement, {attributes: true});
	}

	public connectedCallback() {
		tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			tileSize: 512,
			zoomOffset: -1,
			attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
			crossOrigin: true,
			detectRetina: true,
		}).addTo(this);
		this.extendControls();
		this.resizeObserver = new ResizeObserver((entries) => {
			for (const entry of entries) {
				if (entry.contentBoxSize) {
					this.invalidateSize();
				}
			}
		});
		this.resizeObserver.observe(this.wrapperElement);
		const form = this.textAreaElement.form as HTMLFormElement;
		form.addEventListener('reset', this.formResetted);
		form.addEventListener('submitted', this.formSubmitted);
		this.initialData = JSON.parse(this.textAreaElement.dataset.content as string ?? 'null');
	}

	public disconnectedCallback() {
		this.resizeObserver?.unobserve(this.wrapperElement);
	}

	public get path(): Path {
		return this.textAreaElement.name.split('.');
	}

	private formResetted = () => {
		this.initialData = JSON.parse(this.textAreaElement.dataset.content as string ?? 'null');
		this.setInitialData(this.initialData);
		for (const editor of Object.values(this.editors)) {
			editor.clear();
			editor.setInitialData(this.initialData);
		}
		this.getValue();
	};

	private formSubmitted = () => {
		this.textAreaElement.checkValidity();
	};

	private concealTextArea() {
		if (!this.textAreaElement.classList.contains('dj-concealed')) {
			const style = window.getComputedStyle(this.textAreaElement);
			this.wrapperElement.style.height = style.height;
			this.wrapperElement.style.width = style.width;
			this.textAreaElement.classList.add('dj-concealed');
		}
	}

	private setInitialData(initialData: JSONValue) {
		const bbox = getDataValue(initialData, 'bbox') as number[];
		if (bbox) {
			const bounds = latLngBounds([bbox[1], bbox[0]], [bbox[3], bbox[2]]);
			this.flyToBounds(bounds, {animate: false});
		}
		for (const editor of Object.values(this.editors)) {
			editor.clear();
			editor.setInitialData(initialData);
		}
	}

	private extendControls() {
		const self = this;
		const CustomControls = Control.extend({
			onAdd: function(map: Map) {
				const opts = (this as any).options as ControlOptions;
				const controlTemplate = self.controlsTemplate.content.querySelector(`[aria-current="${opts.position}"]`);
				if (!(controlTemplate instanceof HTMLDivElement))
					throw new Error(`Could not find control template for position ${opts.position}`);
				const controlElements = document.importNode(controlTemplate, true);
				controlElements.querySelectorAll('a[aria-label]').forEach((anchor: Element) => {
					if (anchor instanceof HTMLAnchorElement && anchor.ariaLabel && registry[anchor.ariaLabel] instanceof Function) {
						if (!anchor.ariaDescription)
							throw new Error(`${anchor} is missing property aria-description`);
						if (Object.keys(self.editors).includes(anchor.ariaDescription))
							throw new Error(`Duplicate editor identifier ${anchor.ariaDescription}`);
						const iconOptions = JSON.parse(anchor.dataset.marker as any) as IconOptions;
						self.editors[anchor.ariaDescription] = new registry[anchor.ariaLabel](self, anchor, iconOptions);
					}
				});
				return controlElements;
			},
			onRemove: (map: Map) => {
				// Nothing to do yet
			},
		});
		const customControls = (opts: ControlOptions) => new CustomControls(opts);
		for (let position of CONTROL_POSITIONS) {
			customControls({position: position as ControlPosition}).addTo(this);
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
			Object.values(this.editors).forEach(editor => editor.register());
			this.setInitialData(this.initialData);
			this.getValue();  // to set "_has_value_" on textarea element
		}, {once: true});
	}

	public closeAllDialogs() {
		Object.values(this.editors).forEach(editor => editor.closeAllDialogs());
	}

	public getLayer(identifier: string) : Layer|null {
		const [editorName, layerIndex] = [...identifier.split(':')];
		return this.editors[editorName]?.getLayer(Number(layerIndex)) ?? null;
	}

	private attributesChanged = (mutationsList: Array<MutationRecord>) => {
		for (const mutation of mutationsList) {
			if (mutation.type !== 'attributes') {
				continue;
			}
			if (mutation.attributeName === 'data-content') {
				this.initialData = JSON.parse(this.textAreaElement.dataset.content as string);
				if (getDataValue(this.initialData, 'type') === 'FeatureCollection') {
					window.requestIdleCallback(() => {
						this.setInitialData(this.initialData);
					});
				} else {
					Object.values(this.editors).forEach(editor => editor.clear());
				}
			}
		}
	};

	public getValue() : object {
		// return the values from the Leaflet map here
		const bounds = this.getBounds();
		const result = {
			type: 'FeatureCollection',
			bbox: bounds ? [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()] : null,
			features: [] as Record<string, any>,
		};
		for (const editor of Object.values(this.editors)) {
			result.features.push(...editor.getFeatures());
		}
		this.textAreaElement.innerText = result.features.length === 0 ? "" : "_has_value_";  // required for validation
		return result;
	}

	public updateOperability(...args: any[]) {
		Object.values(this.editors).forEach(editor => editor.updateOperability(...args));
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
						'background-image', 'border-style', 'border-width', 'border-radius', 'box-shadow',
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
