const inlineImportPlugin = require('./esbuild-plugin-inline-import');
const path = require('path');
const sass = require('sass');
const { build } = require('esbuild');
const buildOptions = require('yargs-parser')(process.argv.slice(2), {
  boolean: ['debug', 'monolith'],
});

build({
  entryPoints: [buildOptions.monolith ? 'client/django-formset.monolith.ts' : 'client/django-formset.ts'],
  bundle: true,
  minify: !buildOptions.debug,
  sourcemap: buildOptions.debug,
  outdir: 'formset/static/formset/js/',
  splitting: true,
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
  target: ['es2020', 'chrome84', 'firefox84', 'safari14', 'edge84']
}).catch(() => process.exit(1));
