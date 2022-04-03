// build with `npx tailwindcss --input assets/tailwind-styles.css --config assets/tailwind.config.js --output formset/static/formset/css/tailwind.css`
module.exports = {
  content: [
    'formset/templates/formset/tailwind/**/*.html',
    'testapp/templates/tailwind/*.html',
  ],
  theme: {
    extend: {},
  },
  variants: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
