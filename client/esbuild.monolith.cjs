const inlineImportPlugin = require('./esbuild-plugin-inline-import');
const path = require('path');
const sass = require('sass');
const { build } = require('esbuild');

build({
  entryPoints: ['client/django-formset.ts'],
  bundle: true,
  minify: true,
  outfile: 'formset/static/formset/js/django-formset.js',
  splitting: false,
  format: 'esm',
  plugins: [
    // Run inline style imports through Sass
    inlineImportPlugin({
      filter: /\.scss$/,
      transform: async (contents, args) => {
        return await new Promise((resolve, reject) => {
          sass.render(
            {
              data: contents,
              includePaths: [path.dirname(args.path)],
              outputStyle: 'compressed'
            },
            (err, result) => {
              if (err) {
                reject(err);
                return;
              }
              resolve(result.css.toString());
            }
          );
        });
      }
    }),
  ],
  loader: {'.svg': 'text'},
  sourcemap: true,
  target: ['es2020', 'chrome84', 'firefox84', 'safari14', 'edge84']
}).catch(() => process.exit(1));
