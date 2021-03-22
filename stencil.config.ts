import { Config } from '@stencil/core';
import {sass} from '@stencil/sass';

export const config: Config = {
  namespace: 'django-formset',
  devServer: {
    openBrowser: false
  },
  srcDir: "client",
  outputTargets: [
    {
      type: 'dist',
      esmLoaderPath: '../loader',
      dir: 'formset/static',
    },
    {
      type: 'dist-custom-elements-bundle',
      dir: 'formset/static',
    },
  ],
  plugins: [
    sass({
      includePaths: [
        'node_modules',
        'client/global',
      ],
      sourceMap: true,
    })
  ],
};
