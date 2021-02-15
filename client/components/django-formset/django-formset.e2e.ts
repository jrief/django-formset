import {newE2EPage} from '@stencil/core/testing';

describe('django-formset', () => {
	let formset;

	// @ts-ignore
	beforeEach(async () => {
		const page = await newE2EPage();
		page.on('console', async msg => console[msg._type](
			...await Promise.all(msg.args().map(arg => arg.jsonValue()))
		));
		await page.setContent(`
			<django-formset endpoint="/endpoint">
				<form name="subscribe">
					<django-field-group class="dj-required">
					<label>Label:</label>
					<input type="text" name="foo" maxlength="5" minlength="3" value="A" required>
					<django-error-messages value_missing="This field is required." too_long="Ensure this value has at most 5 characters." too_short="Ensure this value has at least 2 characters." bad_input="Null characters are not allowed."></django-error-messages>
					<ul class="dj-errorlist"><li class="dj-placeholder"></li></ul>
				  </django-field-group>
				</form>
				<button type="button" click="submit" auto-disable="true">Submit</button>
			</django-formset>
		`);
		formset = await page.find('django-formset');
	});

	it('renders', async () => {
		expect(formset).toHaveClass('hydrated');
	});

	it('validates data', async () => {
		const button = await formset.find('button');
		expect(button).toHaveAttribute('disabled');
	});

	it('checks id form is invalid', async () => {
		const form = await formset.find('form:invalid');
		expect(form).toHaveProperty('nodeName', 'FORM');
	});

});
