import {
	Control,
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
	TileLayerOptions,
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

type ControlOptions = {
	position: string;
	leafletBar: HTMLElement;
}

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
				inputElement.value = getDataValue(properties, `${this.extension}.${target}`, '');
				const groupElement = inputElement.closest('[role="group"]');
				if (groupElement instanceof HTMLElement) {
					groupElement.classList.remove('dj-dirty', 'dj-submitted', 'dj-touched');
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
	protected readonly minEntries: number|null;
	protected readonly maxEntries: number|null;

	constructor(geomap: GeoMap, anchor: HTMLAnchorElement) {
		this.geomap = geomap;
		this.anchor = anchor;
		this.minEntries = anchor.dataset.minEntries ? parseInt(anchor.dataset.minEntries) : null;
		this.maxEntries = anchor.dataset.maxEntries ? parseInt(anchor.dataset.maxEntries) : null;
		const popupTemplate = this.geomap.controlsTemplate.content.querySelector(`[role="tooltip"][aria-labeledby="${this.identifier}"]`);
		if (!(popupTemplate instanceof HTMLDivElement))
			throw new Error('Could not find popup template for [role="tooltip"]');
		this.popupTemplate = popupTemplate;
		this.registerFormDialogs();
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

	public closeAllDialogs() {
		this.formDialogs.forEach(dialog => dialog.closeDialog());
	}

	public get identifier()  {
		return this.anchor.ariaDescription;
	}

	protected abstract handleClick(event: LeafletMouseEvent) : void;

	public abstract setInitialData(initialData: JSONValue) : void;

	public abstract clear() : void;

	public abstract getFeatures() : Record<string, any[]>[];

	public abstract getLayer(index: [number, number]) : Layer|null;

	public abstract deleteLayer(index: [number, number]) : void;

	public abstract cancelInitialPlacement() : void;

	public abstract checkValidity() : boolean;

	public extendLayer(index: [number, number]) {}

	public register() {
		this.geomap.on('click', this.handleClick);
	}

	public updateOperability(...args: any[]) {
		this.formDialogs.forEach(dialog => dialog.updateOperability(...args));
	}
}


class GeoMapMarker extends Marker {
	private readonly editor: GeometryEditor;
	private readonly popup: Popup;
	public readonly properties: Record<string, any> = {};
	public readonly index: [number, number];
	public moveMarker: Function|null = null;

	constructor(editor: GeometryEditor, latlng: LatLng, index: [number, number], popupTemplate: HTMLDivElement, icon: Icon) {
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
		this.popup = this.attachPopup(popupTemplate);
	}

	public get identifier(): string {
		return `${this.editor.identifier}:${this.index[0]}`;
	}

	private attachPopup(popupTemplate: HTMLDivElement) : Popup {
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
		return popup;
	}

	public openPopup(latlng?: LatLngExpression): this {
		this.editor.geomap.closeAllDialogs();
		return super.openPopup(latlng);
	}

	public initialPlacement() {
		const map = this.editor.geomap;
		map.getContainer().classList.add('marker-placement');
		this.moveMarker = (event: LeafletMouseEvent) => this.setLatLng(event.latlng);
		map.on('mousemove', this.moveMarker as any);
		map.once('click', this.dropMarker);
	}

	public dropMarker = () => {
		const map = this.editor.geomap;
		map.off('mousemove', this.moveMarker as any);
		this.moveMarker = null;
		map.getContainer().classList.remove('marker-placement');
		map.checkValidity();
	};

	public deleteMarker() {
		this.editor.closeAllDialogs();
		this.removeFrom(this.editor.geomap);
		this.editor.deleteLayer(this.index);
		this.editor.geomap.checkValidity();
	}
}


class PointEditor extends GeometryEditor {
	public readonly markers: (GeoMapMarker|null)[] = [];
	private readonly markerIcon: Icon;

	constructor(geomap: GeoMap, anchor: HTMLAnchorElement, iconOptions: IconOptions) {
		super(geomap, anchor);
		this.markerIcon = new Icon(iconOptions);
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
							const marker = new GeoMapMarker(this, latlng, [this.markers.length, 0], this.popupTemplate, this.markerIcon);
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

	public getLayer(index: [number, number]) : Layer|null {
		return this.markers[index[0]];
	}

	public cancelInitialPlacement() {
		if (this.markers.at(-1)?.moveMarker) {
			const marker = this.markers.pop()!;
			const map = this.geomap;
			map.getContainer().classList.remove('marker-placement');
			map.off('mousemove', marker.moveMarker as any);
			map.off('click', marker.dropMarker as any);
			marker.moveMarker = null;
			marker.deleteMarker();
		}
	}

	public checkValidity(): boolean {
		const numEntries = this.markers.filter(marker => marker !== null).length;
 		this.anchor.ariaDisabled = this.maxEntries !== null && numEntries >= this.maxEntries ? 'true' : null;
		return (this.minEntries === null || numEntries >= this.minEntries);
	}

	public deleteLayer(index: [number, number]) {
		this.markers[index[0]]?.unbindPopup();
		this.markers[index[0]] = null;
	}

	protected handleClick = (event: LeafletMouseEvent) => {
		const target = event.originalEvent.target;
		if (!(target instanceof Element) || target.closest('[role="button"]')?.ariaDescription !== this.anchor.ariaDescription)
			return;
		this.geomap.cancelInitialPlacements();
		const marker = new GeoMapMarker(this, event.latlng, [this.markers.length, 0], this.popupTemplate, this.markerIcon);
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
			for (const [index0, vertextMarkers] of this.path.vertexMarkers.entries()) {
				const index1 = vertextMarkers.indexOf(this);
				if (index1 === -1)
					continue;
				this.path.updateVertices([index0, index1], latlng);
			}
		}
	};

	private deleteVertex = (event: LeafletEvent) => {
		for (const [index0, vertexMarkers] of this.path.vertexMarkers.entries()) {
			const index1 = vertexMarkers.indexOf(this);
			if (index1 === -1)
				continue;
			if (index1 % 2 === 0) {
				this.path.deleteVertex([index0, index1]);
			}
		}
	}
}


class GeoMapPolyline extends Polyline {
	private readonly editor: GeometryEditor;
	public readonly properties: Record<string, any> = {};
	public readonly index: [number, number];
	public readonly group: LayerGroup;
	private readonly popup: Popup;
	private tempVertex: Polyline|null = null;  // temporary vertex moving with the cursor
	public vertexMarkers: VertexMarker[][] = [];
	public moveVertex: Function|null = null;

	constructor(editor: GeometryEditor, latlngs: LatLngExpression[], index: [number, number], popupTemplate: HTMLDivElement) {
		const options: PolylineOptions = {
			bubblingMouseEvents: true,
		};
		super(latlngs, options);
		this.editor = editor;
		this.index = index;
		this.group = new LayerGroup();
		this.group.addTo(editor.geomap);
		this.addTo(this.group);
		this.popup = this.attachPopup(popupTemplate);
	}

	public get identifier(): string {
		return `${this.editor.identifier}:${this.index[0]}`;
	}

	private attachPopup(popupTemplate: HTMLDivElement) : Popup {
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
		return popup;
	}

	public openPopup(latlng?: LatLngExpression): this {
		this.editor.geomap.closeAllDialogs();
		return super.openPopup(latlng);
	}

	public initialPlacement() {
		const map = this.editor.geomap;
		map.getContainer().classList.add('marker-placement');
		this.moveVertex = (event: LeafletMouseEvent) => {
			if (this.tempVertex) {
				const firstLatLng = this.tempVertex.getLatLngs()[0] as LatLng;
				this.tempVertex.setLatLngs([firstLatLng, event.latlng]);
			}
		};
		this.closePopup();
		this.unbindPopup();
		map.on('mousemove', this.moveVertex as any);
		map.on('click', this.addVertex);
		map.once('dblclick', this.finishPolyline);
	}

	public addVertex = (event: LeafletMouseEvent) => {
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

	public finishPolyline = (event: LeafletMouseEvent) => {
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
		const map = this.editor.geomap;
		map.off('mousemove', this.moveVertex as any);
		map.off('click', this.addVertex);
		this.moveVertex = null;
		map.getContainer().classList.remove('marker-placement');
		map.checkValidity();
		this.bindPopup(this.popup);
	};

	public setVertexMarkers(latlngs: LatLng[]) {
		let prevLatLng: LatLng|null = null;
		while (this.index[0] >= this.vertexMarkers.length) {
			this.vertexMarkers.push([]);
		}
		for (const latlng of latlngs) {
			if (prevLatLng) {
				const vertextMarker = new VertexMarker(latLngBounds(prevLatLng, latlng).getCenter(), this, true);
				vertextMarker.addTo(this.group);
				this.vertexMarkers[this.index[0]].push(vertextMarker);
			}
			const vertexMarker = new VertexMarker(latlng, this, false);
			vertexMarker.addTo(this.group);
			this.vertexMarkers[this.index[0]].push(vertexMarker);
			prevLatLng = latlng;
		}
	}

	public updateVertices(index: [number, number], latlng: LatLng) {
		const latlngs = this.getLatLngs() as LatLng[];
		const [index0, index1] = index;
		if (index1 % 2 === 1) {
			// halfway – insert a vertex marker
			latlngs.splice((index1 + 1) / 2, 0, latlng);
			this.vertexMarkers[index0][index1].setOpacity(1.0);
			let prevVertexMarker = this.vertexMarkers[index0][index1 - 1];
			prevVertexMarker = new VertexMarker(latLngBounds(prevVertexMarker.getLatLng(), latlng).getCenter(), this, true);
			prevVertexMarker.addTo(this.group);
			let nextVertexMarker = this.vertexMarkers[index0][index1 + 1];
			nextVertexMarker = new VertexMarker(latLngBounds(latlng, nextVertexMarker.getLatLng()).getCenter(), this, true);
			nextVertexMarker.addTo(this.group);
			this.vertexMarkers[index0].splice(index1, 0, prevVertexMarker);
			this.vertexMarkers[index0].splice(index1 + 2, 0, nextVertexMarker);
		} else {
			latlngs[index1 / 2] = latlng;
			const prevVertexMarker = this.vertexMarkers[index0][index1 - 1];
			if (prevVertexMarker) {
				prevVertexMarker.setLatLng(latLngBounds(latlngs[index1 / 2 - 1], latlng).getCenter());
			}
			const nextVertexMarker = this.vertexMarkers[index0][index1 + 1];
			if (nextVertexMarker) {
				nextVertexMarker.setLatLng(latLngBounds(latlng, latlngs[index1 / 2 + 1]).getCenter());
			}
		}
		this.setLatLngs(latlngs);
	}

	public deleteVertex(index: [number, number]) {
		const latlngs = this.getLatLngs() as LatLng[];
		let [index0, index1] = index;
		const vertexMarker = this.vertexMarkers[index0][index1];
		if (index1 === 0) {
			this.vertexMarkers[index0].splice(0, 2).forEach(marker => this.group.removeLayer(marker));
		} else {
			if (index1 < this.vertexMarkers[index0].length - 1) {
				const [nextVertexMarker] = this.vertexMarkers[index0].splice(index1 + 1, 1);
				this.group.removeLayer(nextVertexMarker);
			} else {
				this.group.removeLayer(this.vertexMarkers[index0].pop() as Layer);
			}
			const [prevVertexMarker] = this.vertexMarkers[index0].splice(index1 - 1, 1);
			this.group.removeLayer(prevVertexMarker);
		}
		if (latlngs.length <= 2) {
			this.deletePolyline();
		} else {
			index1 /= 2;
			if (index1 < latlngs.length - 1) {
				if (index1 !== 0) {
					vertexMarker.setLatLng(latLngBounds([latlngs[index1 - 1], latlngs[index1 + 1]]).getCenter());
				}
				vertexMarker.setOpacity(VertexMarker.halfwayOpacity);
			}
			latlngs.splice(index1, 1);
			this.setLatLngs(latlngs);
		}
	}

	public deletePolyline() {
		this.editor.closeAllDialogs();
		if (this.tempVertex) {
			this.group.removeLayer(this.tempVertex);
			this.tempVertex = null;
		}
		this.vertexMarkers.forEach(markers => markers.forEach(marker => this.group.removeLayer(marker)));
		this.vertexMarkers.length = 0;
		this.group.removeLayer(this);
		this.group.removeFrom(this.editor.geomap);
		this.editor.deleteLayer(this.index);
		this.editor.geomap.checkValidity();
	}
}


class PolylineEditor extends GeometryEditor {
	public readonly polylines: (GeoMapPolyline|null)[] = [];

	constructor(geomap: GeoMap, anchor: HTMLAnchorElement) {
		super(geomap, anchor);
	}

	public getLayer(index: [number, number]) : Layer|null {
		return this.polylines[index[0]];
	}

	public cancelInitialPlacement() {
		if (this.polylines.at(-1)?.moveVertex) {
			const polyline = this.polylines.pop()!;
			const map = this.geomap;
			map.getContainer().classList.remove('marker-placement');
			map.off('mousemove', polyline.moveVertex as any);
			map.off('click', polyline.addVertex as any);
			map.off('dblclick', polyline.finishPolyline as any);
			polyline.moveVertex = null;
			polyline.deletePolyline();
		}
	}

	public checkValidity(): boolean {
		const numEntries = this.polylines.filter(polyline => polyline !== null).length;
 		this.anchor.ariaDisabled = this.maxEntries !== null && numEntries >= this.maxEntries ? 'true' : null;
		return (this.minEntries === null || numEntries >= this.minEntries);
	}

	public deleteLayer(index: [number, number]) {
		this.polylines[index[0]]?.unbindPopup();
		this.polylines[index[0]] = null;
	}

	protected handleClick = (event: LeafletMouseEvent) => {
		const target = event.originalEvent.target;
		if (!(target instanceof Element) || target.closest('[role="button"]')?.ariaDescription !== this.anchor.ariaDescription)
			return;
		this.geomap.cancelInitialPlacements();
		const polyline = new GeoMapPolyline(this, [], [this.polylines.length, 0], this.popupTemplate);
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
						const polyline = new GeoMapPolyline(this, latlngs, [this.polylines.length, 0], this.popupTemplate);
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
	public readonly properties: Record<string, Record<string, any>> = {};
	public readonly index: [number, number];
	public readonly group: LayerGroup;
	private readonly popup: Popup;
	private tempVertex: Polyline|null = null;  // temporary vertex moving with the cursor
	public vertexMarkers: VertexMarker[][] = [];
	public moveVertex: Function|null = null;

	constructor(editor: GeometryEditor, latlngs: LatLngExpression[][], index: [number, number], popupTemplate: HTMLDivElement) {
		const options: PolylineOptions = {
			bubblingMouseEvents: true,
		};
		super(latlngs, options);
		this.editor = editor;
		this.index = index;
		this.group = new LayerGroup();
		this.group.addTo(editor.geomap);
		this.addTo(this.group);
		this.popup = this.attachPopup(popupTemplate);
	}

	public get identifier(): string {
		return `${this.editor.identifier}:${this.index[0]}`;
	}

	private attachPopup(popupTemplate: HTMLDivElement) : Popup {
		const popupContent = document.importNode(popupTemplate, true);
		this.editor.geomap.formset!.assignDetachedButtons(popupContent);
		popupContent.querySelectorAll('[df-click="activate"]').forEach((button: Element) => {
			if (button instanceof HTMLButtonElement) {
				button.dataset.identifier = this.identifier;
			}
		});
		popupContent.querySelector('[name="delete_layer"]')?.addEventListener('click', () => this.deleteAllPolygons());
		popupContent.querySelector('[name="extend_layer"]')?.addEventListener('click', () => this.editor.extendLayer(this.index));
		const popup = new Popup({closeButton: false, autoClose: true, closeOnClick: true});
		popup.setContent(popupContent);
		this.bindPopup(popup);
		return popup;
	}


	public openPopup(latlng?: LatLngExpression): this {
		this.editor.geomap.closeAllDialogs();
		return super.openPopup(latlng);
	}

	public initialPlacement(index: number) {
		this.moveVertex = (event: LeafletMouseEvent) => {
			if (this.tempVertex) {
				const lastLatLng = this.tempVertex.getLatLngs()[0] as LatLng;
				const latLngs = this.getLatLngs()[index] as LatLng[];
				if (latLngs.length < 2) {
					this.tempVertex.setLatLngs([lastLatLng, event.latlng]);
				} else {
					this.tempVertex.setLatLngs([lastLatLng, event.latlng, latLngs[0]]);
				}
			}
		};
		this.closePopup();
		this.unbindPopup();
		const map = this.editor.geomap;
		map.getContainer().classList.add('marker-placement');
		map.on('mousemove', this.moveVertex as any);
		map.on('click', this.addVertex);
		map.once('dblclick', this.finishPolygon);
	}

	public addVertex = (event: LeafletMouseEvent) => {
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
		const latlngRing = this.getLatLngs().at(-1) as LatLng[];
		this.addLatLng(event.latlng, latlngRing);
	};

	public finishPolygon = (event: LeafletMouseEvent) => {
		const latlngs = this.getLatLngs().at(-1) as LatLng[];
		if (latlngs.length > 2) {
			if (isEqual(latlngs[latlngs.length - 1], latlngs[latlngs.length - 2])) {
				latlngs.pop();  // added by second click in dblclick
			}
			this.setVertexMarkers(this.getLatLngs() as LatLng[][]);
		} else {
			latlngs.length = 0;
		}
		this.redraw();
		if (this.tempVertex) {
			this.group.removeLayer(this.tempVertex);
			this.tempVertex = null;
		}
		const map = this.editor.geomap;
		map.off('mousemove', this.moveVertex as any);
		map.off('click', this.addVertex);
		this.moveVertex = null;
		map.getContainer().classList.remove('marker-placement');
		map.checkValidity();
		this.bindPopup(this.popup);
	};

	public setVertexMarkers(latlngRings: LatLng[][]) {
		for (const [index, latlngs] of latlngRings.entries()) {
			while (this.vertexMarkers.length <= index) {
				this.vertexMarkers.push([]);
			}
			let prevLatLng: LatLng|null = null;
			for (const latlng of latlngs) {
				if (prevLatLng) {
					const vertextMarker = new VertexMarker(latLngBounds(prevLatLng, latlng).getCenter(), this, true);
					vertextMarker.addTo(this.group);
					this.vertexMarkers[index].push(vertextMarker);
				}
				const vertexMarker = new VertexMarker(latlng, this, false);
				vertexMarker.addTo(this.group);
				this.vertexMarkers[index].push(vertexMarker);
				prevLatLng = latlng;
			}
			if (prevLatLng) {
				const vertextMarker = new VertexMarker(latLngBounds(prevLatLng, latlngs[0]).getCenter(), this, true);
				vertextMarker.addTo(this.group);
				this.vertexMarkers[index].push(vertextMarker);
			}
		}
	}

	public updateVertices(index: [number, number], latlng: LatLng) {
		const [index0, index1] = index;
		const latlngs = this.getLatLngs()[index0] as LatLng[];
		if (index1 % 2 === 1) {
			// halfway – insert a vertex marker
			latlngs.splice((index1 + 1) / 2, 0, latlng);
			this.vertexMarkers[index0][index1].setOpacity(1.0);
			let prevVertexMarker = this.vertexMarkers[index0][index1 - 1];
			prevVertexMarker = new VertexMarker(latLngBounds(prevVertexMarker.getLatLng(), latlng).getCenter(), this, true);
			prevVertexMarker.addTo(this.group);
			let nextVertexMarker = index1 === this.vertexMarkers[index0].length - 1 ? this.vertexMarkers[index0][0] : this.vertexMarkers[index0][index1 + 1];
			nextVertexMarker = new VertexMarker(latLngBounds(latlng, nextVertexMarker.getLatLng()).getCenter(), this, true);
			nextVertexMarker.addTo(this.group);
			this.vertexMarkers[index0].splice(index1, 0, prevVertexMarker);
			this.vertexMarkers[index0].splice(index1 + 2, 0, nextVertexMarker);
		} else {
			latlngs[index1 / 2] = latlng;
			if (index1 === 0) {
				const prevVertexMarker = this.vertexMarkers[index0][this.vertexMarkers[index0].length - 1];
				prevVertexMarker.setLatLng(latLngBounds(latlngs[this.vertexMarkers[index0].length / 2 - 1], latlng).getCenter());
			} else {
				const prevVertexMarker = this.vertexMarkers[index0][index1 - 1];
				prevVertexMarker.setLatLng(latLngBounds(latlngs[index1 / 2 - 1], latlng).getCenter());
			}
			const nextVertexMarker = this.vertexMarkers[index0][index1 + 1];
			if (index1 === this.vertexMarkers[index0].length - 2) {
				nextVertexMarker.setLatLng(latLngBounds(latlng, latlngs[0]).getCenter());
			} else {
				nextVertexMarker.setLatLng(latLngBounds(latlng, latlngs[index1 / 2 + 1]).getCenter());
			}
		}
		this.redraw();
	}

	public deleteVertex(index: [number, number]) {
		let [index0, index1] = index;
		const latlngs = this.getLatLngs()[index0] as LatLng[];
		const vertexMarker = this.vertexMarkers[index0][index1];
		if (index1 === 0) {
			this.vertexMarkers[index0].splice(0, 2).forEach(marker => this.group.removeLayer(marker));
		} else {
			const [nextVertexMarker] = this.vertexMarkers[index0].splice(index1 + 1, 1);
			this.group.removeLayer(nextVertexMarker);
			const [prevVertexMarker] = this.vertexMarkers[index0].splice(index1 - 1, 1);
			this.group.removeLayer(prevVertexMarker);
		}
		if (latlngs.length <= 2) {
			this.deletePolygon(index0);
		} else {
			index1 /= 2;
			if (index1 < latlngs.length - 1) {
				if (index1 === 0) {
					this.vertexMarkers[index0][this.vertexMarkers[index0].length - 1].setLatLng(latLngBounds([latlngs[latlngs.length - 1], latlngs[1]]).getCenter());
				} else {
					vertexMarker.setLatLng(latLngBounds([latlngs[index1 - 1], latlngs[index1 + 1]]).getCenter());
				}
				vertexMarker.setOpacity(VertexMarker.halfwayOpacity);
			} else {
				vertexMarker.setLatLng(latLngBounds([latlngs[index1 - 1], latlngs[0]]).getCenter());
				vertexMarker.setOpacity(VertexMarker.halfwayOpacity);
			}
			latlngs.splice(index1, 1);
			this.redraw();
		}
	}

	public deletePolygon(index0: number) {
		if (this.tempVertex) {
			this.group.removeLayer(this.tempVertex);
			this.tempVertex = null;
		}
		if (Array.isArray(this.vertexMarkers[index0])) {
			this.vertexMarkers[index0].forEach(marker => this.group.removeLayer(marker));
			this.vertexMarkers.splice(index0, 1);
		}
		this.getLatLngs().splice(index0, 1);
		if (this.getLatLngs().length === 0) {
			this.deleteAllPolygons();
		} else {
			this.redraw();
		}
		this.bindPopup(this.popup);
	}

	public deleteAllPolygons() {
		this.editor.closeAllDialogs();
		if (this.tempVertex) {
			this.group.removeLayer(this.tempVertex);
			this.tempVertex = null;
		}
		this.vertexMarkers.forEach(markers => markers.forEach(marker => this.group.removeLayer(marker)));
		this.vertexMarkers.length = 0;
		this.group.removeLayer(this);
		this.group.removeFrom(this.editor.geomap);
		this.editor.deleteLayer(this.index);
		this.editor.geomap.checkValidity();
	}
}


class PolygonEditor extends GeometryEditor {
	public readonly polygones: (GeoMapPolygon|null)[] = [];

	constructor(geomap: GeoMap, anchor: HTMLAnchorElement) {
		super(geomap, anchor);
	}

	public getLayer(index: [number, number]) : Layer|null {
		return this.polygones[index[0]];
	}

	public cancelInitialPlacement() {
		if (this.polygones.at(-1)?.moveVertex) {
			const polygon = this.polygones.pop()!;
			const map = this.geomap;
			map.getContainer().classList.remove('marker-placement');
			map.off('mousemove', polygon.moveVertex as any);
			map.off('click', polygon.addVertex as any);
			map.off('dblclick', polygon.finishPolygon as any);
			polygon.moveVertex = null;
			polygon.deletePolygon(polygon.getLatLngs().length - 1);
		}
	}

	public checkValidity(): boolean {
		const numEntries = this.polygones.filter(polygone => polygone !== null).length;
 		this.anchor.ariaDisabled = this.maxEntries !== null && numEntries >= this.maxEntries ? 'true' : null;
		return (this.minEntries === null || numEntries >= this.minEntries);
	}

	public deleteLayer(index: [number, number]) {
		this.polygones[index[0]]?.unbindPopup();
		this.polygones[index[0]] = null;
	}

	protected handleClick = (event: LeafletMouseEvent) => {
		const target = event.originalEvent.target;
		if (!(target instanceof Element) || target.closest('[role="button"]')?.ariaDescription !== this.anchor.ariaDescription)
			return;
		this.geomap.cancelInitialPlacements();
		const polygon = new GeoMapPolygon(this, [], [this.polygones.length, 0], this.popupTemplate);
		this.polygones.push(polygon);
		polygon.initialPlacement(0);
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
						const latlngs = (GeoJSON.geometryToLayer(geometry as any) as any).getLatLngs() as LatLng[][];
						const polygon = new GeoMapPolygon(this, latlngs, [this.polygones.length, 0], this.popupTemplate);
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
				polygon.deleteAllPolygons();
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


class MultiPolygonEditor extends PolygonEditor {
	constructor(geomap: GeoMap, anchor: HTMLAnchorElement) {
		super(geomap, anchor);
	}

	public extendLayer(index: [number, number]) {
		const polygon = this.polygones[index[0]];
		if (polygon) {
			const latLngs = polygon.getLatLngs();
			latLngs.push([] as any);  // add empty polygon
			polygon.redraw();
			polygon.initialPlacement(latLngs.length - 1);
		}
	}
}


const registry: Record<string, new (geomap: GeoMap, anchor: HTMLAnchorElement, ...args: any[]) => GeometryEditor> = {
	PointEditor,
	PolylineEditor,
	PolygonEditor,
	MultiPolygonEditor,
};


class GeoMap extends Map implements Inducible {
	private readonly textAreaElement: HTMLTextAreaElement;
	private readonly baseSelector = '.dj-geomap-wrapper';
	public readonly wrapperElement: HTMLDivElement;
	public readonly controlsTemplate: HTMLTemplateElement;
	public formset?: DjangoFormset;
	private readonly intersectionObserver: IntersectionObserver;
	private readonly mutationObserver: MutationObserver;
	private resizeObserver: ResizeObserver;
	public readonly editors: Record<string, GeometryEditor> = {};
	private readonly initialBBox: Record<string, string>;
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

	constructor(element: GeoMapElement) {
		const wrapperElement = element.previousElementSibling as HTMLDivElement;
		const mapElement = wrapperElement?.querySelector('.leaflet-map') as HTMLDivElement;
		if (!(mapElement instanceof HTMLDivElement))
			throw new Error(`Could not find .leaflet-map element in ${wrapperElement}`);
		const options = element.dataset.mapOptions ? JSON.parse(element.dataset.mapOptions) : GeoMap.defaultMapOptions;
		super(mapElement, options);
		this.textAreaElement = element;
		this.wrapperElement = wrapperElement;
		const controlsTemplate = wrapperElement.querySelector('template');
		if (!(controlsTemplate instanceof HTMLTemplateElement))
			throw new Error(`Could not find <template> element in ${wrapperElement}`);
		this.controlsTemplate = controlsTemplate;
		this.registerInducer();
		this.intersectionObserver = new IntersectionObserver(this.handleVisibility);
		this.mutationObserver = new MutationObserver(this.attributesChanged);
		this.resizeObserver = new ResizeObserver(this.handleResize);
		this.initialBBox = this.computeInitialBBox();
	}

	public connectedCallback() {
		const urlTemplate = this.textAreaElement.dataset.urlTemplate ?? 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
		const options = this.textAreaElement.dataset.tileLayerOptions ? JSON.parse(this.textAreaElement.dataset.tileLayerOptions) : GeoMap.defaultTileLayerOptions;
		tileLayer(urlTemplate, options).addTo(this);
		this.extendControls();
		if (this.wrapperElement.checkVisibility()) {
			if (!StyleHelpers.stylesAreInstalled(this.baseSelector)) {
				this.transferStyles();
			}
			this.concealTextArea();
		} else {
			this.intersectionObserver.observe(this.wrapperElement);
		}
		this.mutationObserver.observe(this.textAreaElement, {attributes: true});
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

	private computeInitialBBox() {
		const style = this.textAreaElement.style;
		const computedStyle = window.getComputedStyle(this.textAreaElement);
		return {
			height: style.height ? style.height: computedStyle.height,
			minHeight: style.minHeight,
			maxHeight: style.maxHeight,
		};
	}

	private formResetted = () => {
		const initialData = JSON.parse(this.textAreaElement.dataset.content as string ?? 'null');
		this.setInitialData(initialData);
		this.checkValidity();
	};

	private formSubmitted = () => {
		this.textAreaElement.checkValidity();
	};

	private concealTextArea() {
		if (!this.textAreaElement.classList.contains('dj-concealed')) {
			Object.assign(this.wrapperElement.style, {
				height: this.initialBBox.height,
				minHeight: this.initialBBox.minHeight,
				maxHeight: this.initialBBox.maxHeight,
			});
			const cssClass = this.textAreaElement.classList.toString();
			if (cssClass) {
				this.wrapperElement.classList.add(...cssClass.split(/\s+/));
			}
			this.textAreaElement.classList.add('dj-concealed');
		}
	}

	private setInitialData(initialData: JSONValue) {
		const bbox = getDataValue(initialData, 'bbox') as number[];
		if (bbox) {
			const bounds = latLngBounds([bbox[1], bbox[0]], [bbox[3], bbox[2]]);
			window.requestIdleCallback(() => this.flyToBounds(bounds, {animate: false}));
		}
		for (const editor of Object.values(this.editors)) {
			editor.clear();
			editor.setInitialData(initialData);
		}
		this.checkValidity();
	}

	private extendControls() {
		const self = this;
		const CustomControls = Control.extend({
			onAdd: function(map: Map) {
				const opts = (this as any).options;
				const controlElements = document.importNode(opts.leafletBar, true);
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
		const customControls = (opts: ControlOptions) => new CustomControls(opts as any);
		for (const position of CONTROL_POSITIONS) {
			for (const leafletBar of self.controlsTemplate.content.querySelectorAll(`[aria-current="${position}"] > .leaflet-bar`) as NodeListOf<HTMLDivElement>) {
				customControls({position, leafletBar}).addTo(this);
			}
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
			const initialData = JSON.parse(this.textAreaElement.dataset.content as string ?? 'null');
			this.setInitialData(initialData);
			const handleEscape = (event: KeyboardEvent) => {
				if (event.key === 'Escape') {
					this.cancelInitialPlacements();
				}
			};
			document.addEventListener('keydown', handleEscape);
		}, {once: true});
	}

	public closeAllDialogs() {
		Object.values(this.editors).forEach(editor => editor.closeAllDialogs());
	}

	public cancelInitialPlacements() {
		Object.values(this.editors).forEach(editor => editor.cancelInitialPlacement());
	}

	public getLayer(identifier: string) : Layer|null {
		const [editorName, layerIndex] = [...identifier.split(':')];
		return this.editors[editorName]?.getLayer([Number(layerIndex), 0]) ?? null;
	}

	private handleVisibility = (entries: IntersectionObserverEntry[]) => {
		entries.forEach(entry => {
			if (entry.isIntersecting) {
				if (!StyleHelpers.stylesAreInstalled(this.baseSelector)) {
					this.transferStyles();
				}
				this.concealTextArea();
			}
		});
	};

	private attributesChanged = (mutationsList: Array<MutationRecord>) => {
		for (const mutation of mutationsList) {
			if (mutation.type === 'attributes' && mutation.attributeName === 'data-content') {
				const initialData = JSON.parse(this.textAreaElement.dataset.content as string);
				if (getDataValue(initialData, 'type') === 'FeatureCollection') {
					window.requestIdleCallback(() => {
						this.setInitialData(initialData);
					});
				} else {
					Object.values(this.editors).forEach(editor => editor.clear());
				}
			}
		}
	};

	private handleResize = (entries: ResizeObserverEntry[]) => {
		if (!this.wrapperElement.checkVisibility())
			return;
		for (const entry of entries) {
			if (entry.contentBoxSize) {
				this.invalidateSize();
			}
		}
	};

	public getValue() : Record<string, any> {
		// return the values from the Leaflet map here
		const bounds = this.getBounds();
		const result = {
			type: 'FeatureCollection',
			bbox: bounds ? [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()] : null,
			features: [] as Record<string, any>[],
		};
		for (const editor of Object.values(this.editors)) {
			result.features.push(...editor.getFeatures());
		}
		return result;
	}

	public checkValidity() {
		const isValid = Object.values(this.editors).every(editor => editor.checkValidity());
		this.textAreaElement.innerText = isValid ? "_is_valid_" : "";  // required for validation
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
			{
				'--border-color': 'border-color',
				'--text-color': 'color',
				'--background-color': 'background-color',
			},
			this.textAreaElement,
		);
		StyleHelpers.replaceMediaQueryStyles(
			-1,
			sheet,
			this.baseSelector,
			{
				'--text-muted-color': 'color',
				'--background-muted-color': 'background-color',
			},
			this.textAreaElement, {'disabled': ''},
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
