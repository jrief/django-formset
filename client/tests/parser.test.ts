import {parse} from '../django-formset/tag-attributes';

test('action1 -> action2 !~ action3', () => {
	const ast = parse('action1 -> action2 !~ action3', {startRule: 'Ternary'});
	expect(ast).toEqual( {
		condition: true,
		fulfilled: {
			rejectChain: [{
				args: [],
				funcname: 'action3',
			}],
			successChain: [{
				args: [],
				funcname: 'action1',
			}, {
				args: [],
				funcname: 'action2',
			}],
		},
		otherwise: null,
	});
});
