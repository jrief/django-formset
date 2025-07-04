import fs from 'fs';
import path from 'path';
import SVGSpriter from 'svg-sprite';
import {Resvg} from '@resvg/resvg-js';

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
      'maxWidth': 48,
      'maxHeight': 36
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
      // fs.writeFileSync('formset/static/formset/icons/sprite-flags.svg', file.contents);
      // instead, prefer to render as PNG since it's about 1/10 of the size
      const resvg = new Resvg(file.contents, {
        background: 'rgba(255, 255, 255, 0)',
        fitTo: {
          mode: 'width',
          value: 720
        }
      });
      fs.writeFileSync('formset/static/formset/icons/sprite-flags.png', resvg.render().asPng());
    } else {
      fs.mkdirSync(path.dirname(file.path), {recursive: true});
      fs.writeFileSync(file.path, file.contents);
    }
  }
});
