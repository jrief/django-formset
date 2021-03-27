// build with `npx tailwindcss build assets/tailwind-styles.css -o testapp/static/testapp/tailwind.css`
module.exports = {
  purge: [],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {},
  },
  variants: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms')
  ],
}
