import {build} from 'esbuild';
import inlineImportPlugin from './esbuild-plugin-inline-import.cjs';
import path from 'path';
import parser from 'yargs-parser';
import * as sass from 'sass';

const buildOptions = parser(process.argv.slice(2), {
  boolean: ['debug', 'monolith'],
});

await build({
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
  target: ['es2022', 'chrome100', 'firefox100', 'safari15', 'edge100']
}).catch(() => process.exit(1));
