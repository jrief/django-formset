import template from 'lodash.template';
import {StyleHelpers} from './helpers';
import styles from './FileUploadWidget.scss';


export class FileUploadWidget {
	private readonly fieldGroup: FieldGroup;
	private readonly dropbox: HTMLElement;
	private readonly chooseFileButton: HTMLButtonElement;
	private readonly progressBar: HTMLProgressElement|null = null;
	private readonly dropboxItemTemplate: Function;
	private readonly emptyDropboxItem: HTMLDivElement;
	private readonly observer: MutationObserver;
	private readonly initialData: Object[];
	private readonly initialRequired: boolean;
	private readonly maxUploadSize: number;
	private readonly baseSelector = 'django-formset .dj-control-panel:has(input[type="file"])';
	private readonly styleSheet: CSSStyleSheet;
	public readonly inputElement: HTMLInputElement;
	public uploadedFiles: Object[];

	constructor(fieldGroup: FieldGroup, inputElement: HTMLInputElement) {
		this.fieldGroup = fieldGroup;
		this.inputElement = inputElement;
		this.maxUploadSize = parseInt(this.inputElement.getAttribute('max-size') ?? '0');
		this.dropbox = this.fieldGroup.element.querySelector('figure.dj-dropbox') as HTMLElement;
		if (!this.dropbox)
			throw new Error('Element <input type="file"> requires sibling element <figure class="dj-dropbox"></figure>');

		this.chooseFileButton = this.fieldGroup.element.querySelector(`button[aria-controls="${inputElement.id}"]`) as HTMLButtonElement;
		if (!this.chooseFileButton)
			throw new Error(`Element ${inputElement} requires sibling element <button aria-controls="${inputElement.id}"></button>`);

		this.progressBar = this.fieldGroup.element.querySelector('progress') as HTMLProgressElement;
		if (this.progressBar) {
			this.progressBar.style.visibility = 'hidden';
		}

		this.emptyDropboxItem = this.dropbox.querySelector('div.dj-empty-item') as HTMLDivElement;
		if (!this.emptyDropboxItem)
			throw new Error('Element <input type="file"> requires sibling element <figure><div class="dj-empty-item"></div></figure>');

		const dropboxItemTemplate = this.fieldGroup.element.querySelector('.dj-dropbox-items');
		if (!dropboxItemTemplate)
			throw new Error('Element <input type="file"> requires sibling element <template class="dj-dropbox-items"></template>');
		this.dropboxItemTemplate = template(dropboxItemTemplate.innerHTML) as Function;

		this.observer = new MutationObserver(mutationsList => this.attributesChanged(mutationsList));
		this.observer.observe(this.inputElement, {attributes: true});
		this.chooseFileButton.disabled = inputElement.disabled;
		this.styleSheet = StyleHelpers.stylesAreInstalled(this.baseSelector) ?? this.transferStyles();

		const initialData = document.getElementById(`initial_${inputElement.id}`);
		if (initialData?.textContent) {
			this.uploadedFiles = this.initialData = [JSON.parse(initialData.textContent)];
			this.renderDropbox();
		} else {
			this.uploadedFiles = this.initialData = [];
		}
		this.initialRequired = this.inputElement.required;
		this.dropbox.addEventListener('dragover', this.handleDragOver);
		this.dropbox.addEventListener('dragleave', this.handleDragLeave);
		this.dropbox.addEventListener('drop', this.handleFileDrop);
		this.chooseFileButton.addEventListener('click', () => {
			inputElement.click();
		});
		inputElement.addEventListener('change', () => this.uploadFiles(this.inputElement.files).then(() => {
			this.fieldGroup.inputted();
			this.fieldGroup.validate();
		}).catch(() => {
			this.fieldGroup.errorPlaceholder.reportCustomError(gettext("File upload failed."));
		}).finally(() => {
			this.chooseFileButton.blur();
			this.fieldGroup.touch();
		}));
	}

	private matchesMimeType(mimeType: string): boolean {
		if (!this.inputElement.accept)
			return true;
		const acceptTypes = this.inputElement.accept.split(',').map(s => s.trim());
		const [mainType, subType] = mimeType.split('/');
		for (const acceptType of acceptTypes) {
			if (!acceptType || acceptType === mimeType || subType === '*' && acceptType.split('/')[0] === mainType)
				return true;
		}
		return false;
	}

	private handleFileDrop = (event: DragEvent) => {
		this.dropbox.classList.remove('drag-over');
		this.fieldGroup.element.classList.remove('dj-untouched');
		this.fieldGroup.element.classList.add('dj-touched');
		this.swallowEvent(event);
		if (event.dataTransfer) {
			for (const file of event.dataTransfer.files) {
				if (!this.matchesMimeType(file.type)) {
					event.dataTransfer.clearData();
					const message = gettext(`A file with MIME-type '${file.type}' can not be dropped here.`);
					this.fieldGroup.errorPlaceholder.reportCustomError(message);
					return;
				}
			}
			this.fieldGroup.touch();
			this.inputElement.files = event.dataTransfer.files;
			this.uploadFiles(this.inputElement.files).then(() => {
				this.fieldGroup.inputted();
				this.fieldGroup.validate();
			});
		}
	};

	private fileRemove = () => {
		this.inputElement.value = '';  // used to clear readonly `this.inputElement.files`
		this.inputElement.required = this.initialRequired;
		this.uploadedFiles = this.initialData.length > 0 ? [{}] : [];
		while (this.dropbox.firstChild) {
			this.dropbox.removeChild(this.dropbox.firstChild);
		}
		this.dropbox.appendChild(this.emptyDropboxItem);
		this.fieldGroup.touch();
		this.fieldGroup.inputted();
		this.fieldGroup.validate();
	};

	private handleDragOver = (event: Event) => {
		this.dropbox.classList.add('drag-over');
		this.swallowEvent(event);
	};

	private handleDragLeave = (event: Event) => {
		this.dropbox.classList.remove('drag-over');
		this.swallowEvent(event);
	};

	private swallowEvent = (event: Event) => {
		event.stopPropagation();
		event.preventDefault();
	};

	private async uploadFiles(files: FileList | null) : Promise<void> {
		if (!files || files.length === 0)
			return Promise.reject();
		return new Promise<void>((resolve, reject) => {
			// Django currently can't handle multiple file uploads, restrict to first file
			const file = files.item(0);
			if (file && (!this.maxUploadSize || file.size <= this.maxUploadSize)) {
				this.uploadFile(file, this.dropbox.clientHeight).then(response => {
					this.uploadedFiles = [response];
					this.renderDropbox();
					this.fieldGroup.inputted();
					this.inputElement.dataset.fileupload = JSON.stringify(response);
					resolve();
				}).catch(() => {
					reject();
				});
			} else {
				reject();
			}
		});
	}

	private async uploadFile(file: File, imageHeight: number): Promise<Object> {
		let self = this;

		function updateProgress(event: ProgressEvent) {
			const complete = event.lengthComputable ? event.loaded / event.total : 0;
			if (self.progressBar) {
				self.progressBar.style.visibility = 'visible';
				// the remaining 3% of the progress bar are reserved for image transformation
				self.progressBar.value = 0.97 * complete;
			}
		}

		const body = new FormData();
		body.append('temp_file', file);
		body.append('image_height', imageHeight.toString());

		return new Promise<Response>((resolve, reject) => {
			function transferComplete() {
				if (self.progressBar) {
					self.progressBar.value = 1;
					window.setTimeout(() => self.progressBar!.style.visibility = 'hidden', 333);
				}
				if (request.status === 200) {
					resolve(request.response);
				} else {
					reject(request.response);
				}
			}

			const request = new XMLHttpRequest();
			if (self.progressBar) {
				request.addEventListener('loadstart', updateProgress);
				request.upload.addEventListener('progress', updateProgress, false);
			}
			request.addEventListener('loadend', transferComplete);
			request.open('POST', this.fieldGroup.form.formset.endpoint, true);
			const csrfToken = this.fieldGroup.form.formset.CSRFToken;
			if (csrfToken) {
				request.setRequestHeader('X-CSRFToken', csrfToken);
			}
			request.responseType = 'json';
			request.send(body as XMLHttpRequestBodyInit);
		});
	}

	private renderDropbox() {
		try {
			// @ts-ignore
			const list = this.uploadedFiles.map(this.dropboxItemTemplate);
			if (list.length > 0) {
				this.dropbox.innerHTML = list.join('');
				this.inputElement.dataset.fileupload = JSON.stringify(this.uploadedFiles[0]);
			} else {
				this.dropbox.replaceChildren(this.emptyDropboxItem);
			}
		} catch (e) {
			console.warn(`Error while rendering dropbox template: ${e}`);
		}
	}

	private attributesChanged(mutationsList: Array<MutationRecord>) {
		for (const mutation of mutationsList) {
			if (mutation.type !== 'attributes') {
				continue;
			}
			if (mutation.attributeName === 'disabled' && this.chooseFileButton.disabled != this.inputElement.disabled) {
				this.chooseFileButton.disabled = this.inputElement.disabled;
			}
			if (mutation.attributeName === 'data-fileupload') {
				const fileUpload = this.inputElement.dataset.fileupload;
				if (fileUpload) {
					this.dropbox.innerHTML = this.dropboxItemTemplate(JSON.parse(fileUpload));
					const button = this.dropbox.querySelector('.dj-delete-file');
					if (button) {
						button.addEventListener('click', this.fileRemove, {once: true});
					}
					this.inputElement.required = false;
				} else {
					this.inputElement.required = this.initialRequired;
				}
			}
			if (mutation.attributeName === 'required' && this.inputElement.dataset.fileupload) {
				this.inputElement.required = false;
			}
		}
	}

	private transferStyles() : CSSStyleSheet {
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		if (!declaredStyles.sheet)
			throw new Error("Could not create <style> element");
		this.inputElement.style.transition = 'none';  // prevent transition while pilfering styles
		let loaded = false;
		for (let index = 0; declaredStyles.sheet && index < declaredStyles.sheet.cssRules.length; index++) {
			const cssRule = declaredStyles.sheet.cssRules.item(index) as CSSStyleRule;
			const selector = cssRule.selectorText.trim();
			let extraStyles = '';
			switch (selector) {
				case this.baseSelector:
					loaded = true;
					break;
				default:
					break;
			}
			if (extraStyles) {
				declaredStyles.sheet.insertRule(`${selector}{${extraStyles}}`, ++index);
			}
		}
		this.inputElement.style.transition = '';
		StyleHelpers.pushMediaQueryStyles(
			declaredStyles.sheet,
			this.baseSelector,
			{
				'--outline-color': 'outline-color',
			},
			this.inputElement,
		);
		if (!loaded)
			throw new Error(`Could not load styles for ${this.baseSelector}`);
		return declaredStyles.sheet as CSSStyleSheet;
	}

	public inProgress(): boolean {
		return !!this.inputElement.files && this.inputElement.files.length > 0 && !this.uploadedFiles.length;
	}

	public resetToInitial() {
		this.uploadedFiles = this.initialData;
		this.renderDropbox();
	}
}
