import {newE2EPage} from '@stencil/core/testing';
//import { DjangoFormset } from './django-form';

describe('django-formset', () => {
  let page, formset;

  // @ts-ignore
  beforeEach(async () => {
    page = await newE2EPage();
    await page.setContent(
      '<django-formset endpoint="/endpoint">' +
        '<form name="subscribe">' +
          '<django-field-group class="dj-required">' +
            '<label>Label:</label>' +
            '<input type="text" name="foo" maxlength="5" minlength="2" value="A" required>' +
            '<django-error-messages value_missing="This field is required." too_long="Ensure this value has at most 5 characters." too_short="Ensure this value has at least 2 characters." bad_input="Null characters are not allowed."></django-error-messages>' +
            '<ul class="dj-errorlist"><li class="dj-placeholder"></li></ul>' +
          '</django-field-group>' +
        '</form>' +
        '<button type="button" click="submit" auto-disable="true">Submit</button>' +
      '</django-formset>'
    );
    formset = await page.find('django-formset');
  });

  // @ts-ignore
  it('renders', async () => {
    expect(formset).toHaveClass('hydrated');
  });

  // @ts-ignore
  it('validates data', async () => {
    const button = await page.find('button');
    expect(button).toHaveProperty('nodeName', 'BUTTON');
    const disabled = await button.getProperty('click');
    expect(disabled).toBeTruthy();
    console.log(button);
    //expect(button).toBeInstanceOf(E2EElement);
  });
});
