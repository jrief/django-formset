import {parse} from 'build/tag-attributes';

test('action1 -> action2 !~ action3', () => {
	const expected = {
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
	};
	expect(parse('action1->action2!~action3', {startRule: 'Ternary'})).toEqual(expected);
	expect(parse('action1 -> action2 !~ action3', {startRule: 'Ternary'})).toEqual(expected);
	// fails: expect(parse(' action1 -> action2 !~ action3 ', {startRule: 'Ternary'})).toEqual(expected);
});

test('activate(prefill(a.b))', () => {
	const expected = {
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
	};
	expect(parse('activate(prefill(a.b)) ', {startRule: 'Ternary'})).toEqual(expected);
	expect(parse('activate ( prefill ( a.b ) )', {startRule: 'Ternary'})).toEqual(expected);
	expect(parse(' activate ( prefill ( a.b ) ) ', {startRule: 'Ternary'})).toEqual(expected);
});
