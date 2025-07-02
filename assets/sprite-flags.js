'use strict';

const fs = require('fs');
const path = require('path');
const SVGSpriter = require('svg-sprite');

// 1. Create and configure a spriter instance
// ====================================================================
const spriter = new SVGSpriter({
  'mode': {
    'css': {
      'dest': 'formset/static/formset',
      'prefix': '.flag-%s',
      'common': 'flag-icon',
      'render': {
        'css': {
          'template': 'assets/sprite-flags.css.mustache',
          'dest': 'css/sprite-flags.css'
        }
      },
      'example': false,
      'sprite': 'flags'
    }
  },
  'shape': {
    'dimension': {
      'maxWidth': 24,
      'maxHeight': 18
    }
  }
});

const svgDir = 'node_modules/flag-icons/flags/4x3';
fs.readdirSync(svgDir).forEach(file => {
  if (file.endsWith('.svg')) {
    const filePath = path.join(svgDir, file);
    spriter.add(
      filePath,
      file,
      fs.readFileSync(filePath, 'utf-8')
    );
  }
});

spriter.compile((error, result, data) => {
  for (const file of Object.values(result.css)) {
    if (file.path.endsWith('.svg')) {
      fs.writeFileSync('formset/static/formset/icons/sprite-flags.svg', file.contents);
    } else {
      fs.mkdirSync(path.dirname(file.path), {recursive: true});
      fs.writeFileSync(file.path, file.contents);
    }
  }
});
