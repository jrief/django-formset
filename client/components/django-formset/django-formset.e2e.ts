import {newE2EPage} from '@stencil/core/testing';

describe('test validity of <django-formset>', () => {
	let page, formset, inputField;

	beforeEach(async () => {
		page = await newE2EPage();
		page.on('console', async msg => console[msg._type](
			...await Promise.all(msg.args().map(arg => arg.jsonValue()))
		));
		await page.setContent(`
			<django-formset endpoint="/endpoint">
				<form name="subscribe">
					<django-field-group>
						<input type="text" name="foo" maxlength="5" minlength="3" value="1" required>
						<django-error-messages value_missing="This field is required." too_long="Ensure this value has at most 5 characters." too_short="Ensure this value has at least 3 characters." bad_input="Null characters are not allowed."></django-error-messages>
						<ul class="dj-errorlist"><li class="dj-placeholder"></li></ul>
				  </django-field-group>
				</form>
			</django-formset>
		`);
		formset = await page.find('django-formset');
		expect(formset).toHaveClass('hydrated');
		inputField = await formset.find('input');
	});

	it('checks that bound field keeps form invalid', async () => {
		const form = await formset.find('form:invalid');
		expect(form).toBeTruthy();
	});

	it('checks that too short input is detected', async () => {
		await inputField.click();
		await inputField.focus();
		await inputField.type('2');
		await inputField.press('Enter');
		//await page.waitForChanges();
		const form = await formset.find('form:invalid');
		expect(form).toBeTruthy();
		const placeholder = await formset.find('ul.dj-errorlist > li.dj-placeholder');
		expect(placeholder).toBeTruthy();
		expect(placeholder.textContent).toBe('Ensure this value has at least 3 characters.');
	});

	it('checks that valid input turns form valid', async () => {
		await inputField.click();
		await inputField.focus();
		await inputField.type('23');
		//await page.waitForChanges();
		const form = await formset.find('form:valid');
		expect(form).toBeTruthy();
		const value = await inputField.getProperty('value');
		expect(value).toBe('123');
	});

	it('checks that too long input is truncated', async () => {
		await inputField.click();
		await inputField.focus();
		await page.keyboard.press('Backspace');
		await inputField.type('abcdefgh');
		const form = await formset.find('form:valid');
		expect(form).toBeTruthy();
		const value = await inputField.getProperty('value');
		expect(value).toBe('abcde');
	});

	it('checks that empty input is detected', async () => {
		await inputField.click();
		await inputField.focus();
		await page.keyboard.press('Backspace');
		await inputField.press('Enter');
		const form = await formset.find('form:invalid');
		expect(form).toBeTruthy();
		const placeholder = await formset.find('ul.dj-errorlist > li.dj-placeholder');
		expect(placeholder).toBeTruthy();
		expect(placeholder.textContent).toBe('This field is required.');
	});

});

describe('test required checkbox in <django-formset>', () => {
	let page, formset, inputField;

	beforeEach(async () => {
		page = await newE2EPage();
		page.on('console', async msg => console[msg._type](
			...await Promise.all(msg.args().map(arg => arg.jsonValue()))
		));
		await page.setContent(`
			<django-formset endpoint="/endpoint">
				<form name="subscribe">
					<django-field-group class="dj-required">
						<input type="checkbox" name="subscribe" required>
						<django-error-messages value_missing="This field is required." bad_input="Null characters are not allowed."></django-error-messages>
						<ul class="dj-errorlist"><li class="dj-placeholder"></li></ul>
					</django-field-group>
					<button type="button" click="submit" auto-disable="true">Submit</button>
				</form>
			</django-formset>
		`);
		formset = await page.find('django-formset');
		expect(formset).toHaveClass('hydrated');
		inputField = await formset.find('input');
	});

	it('checks that checkbox is checked', async () => {
		const form = await formset.find('form:invalid');
		expect(form).toBeTruthy();
		const placeholder = await formset.find('ul.dj-errorlist > li.dj-placeholder');
		page.debugger();
		expect(placeholder.textContent).toBe('');
	});

});
