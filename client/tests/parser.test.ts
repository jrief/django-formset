import {parse} from 'build/tag-attributes';

test('action1 -> action2 !~ action3', () => {
	const ast = parse('action1 -> action2 !~ action3', {startRule: 'Ternary'});
	expect(ast).toEqual( {
		condition: true,
		fulfilled: {
			rejectChain: [{
				_funcArgs: [],
				_funcName: 'action3',
			}],
			successChain: [{
				_funcArgs: [],
				_funcName: 'action1',
			}, {
				_funcArgs: [],
				_funcName: 'action2',
			}],
		},
		otherwise: null,
	});
});

test('activate(prefill(a.b))', () => {
	const ast = parse(' activate ( prefill ( a.b ) ) ', {startRule: 'Ternary'});
	expect(ast).toEqual( {
		condition: true,
		fulfilled: {
			rejectChain: [],
			successChain: [{
				_funcName: 'activate',
				_funcArgs: [{
					_funcName: 'prefill',
					_funcArgs: [{
						_funcName: 'getDataValue',
						_funcArgs: [['a', 'b']],
					}]
				}],
			}],
		},
		otherwise: null,
	});
});


test('activate(prefill(a.b))', () => {
	const ast = parse(' activate ( prefill ( a.b ) ) ', {startRule: 'Ternary'});
	expect(ast).toEqual( {
		condition: true,
		fulfilled: {
			rejectChain: [{
				args: [],
				funcname: 'action3',
			}],
			successChain: [{
				_funcName: 'activate',
				_funcArgs: [{
					_funcName: 'prefill',
					_funcArgs: [{
						_funcName: 'getDataValue',
						_funcArgs: [['a', 'b']],
					}]
				}],
			}],
		},
		otherwise: null,
	});
});
