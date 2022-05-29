// build with `npx tailwindcss --input assets/tailwind-styles.css --config assets/tailwind.config.js --output formset/static/formset/css/tailwind.css`
module.exports = {
  content: [
    'formset/templates/formset/tailwind/**/*.html',
    'testapp/templates/tailwind/*.html',
  ],
  safelist: [
    // CSS classes referenced in Python code, hence unreachable by Tailwind's HTML parser
    'flex', 'flex-wrap', 'mb-4', '-mx-3', 'w-full', 'px-3', 'w-1/4', 'w-3/4', 'w-2/5', 'w-3/5',
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
