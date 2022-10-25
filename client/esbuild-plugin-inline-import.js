const path = require('path');
const fs = require('fs').promises;

module.exports = options => {
  // Code pilfered from https://github.com/claviska/esbuild-plugin-inline-import
  // however, here the filter is only used for matching and not for replacement. This is required
  // to make the TypeScript code compatible with https://github.com/bennypowers/lit-css
  const { filter, namespace, transform } = Object.assign(
    {
      /**
       *  A regex filter to match the desired import. Defaults to imports that start with `inline:`, e.g.
       *  import './mystyles.scss';
       */
      filter: /.scss$/,

      /**
       * The namespace to use. If you use more than one instance of this plugin, each one should have a unique
       * namespace. This is a random string by default, so you won't need to change it unless you're targeting a
       * specific namespace.
       */
      namespace: '_' + Math.random().toString(36).substr(2, 9),

      /**
       * A function to transform the contents of the imported file. This can be a simple string replace or a more
       * complex operation, such as a call to PostCSS, Sass, etc. The function must return a string.
       *
       * The contents argument will be a string containing the file's contents. The args argument is passed through from
       * esbuild, but the most useful is probably args.path which references the file path.
       *
       * Note that heavy operations here can impact esbuild's performance!
       */
      transform: async (contents, args) => contents
    },
    options
  );

  return {
    name: 'esbuild-inline-plugin',
    setup(build) {
      build.onResolve({ filter }, args => {
        return {
          path: path.resolve(args.resolveDir, args.path),
          namespace
        };
      });

      build.onLoad({ filter: /.*/, namespace }, async args => {
        let contents = await fs.readFile(args.path, 'utf8');

        if (typeof transform === 'function') {
          contents = await transform(contents, args);
        }

        return {
          contents,
          loader: 'text'
        };
      });
    }
  };
};
