import {parse} from 'build/no-comments';

test('line comment', () => {
	const source = `
// This is a comment
console.log('Hello, world!'); // This is another comment
// This is a comment
`;
	const expected = `console.log('Hello, world!');`;
	expect(parse(source, {startRule: 'JavaScript'})).toEqual(expected);
});


test('line comment in string', () => {
	const source = `
console.log('Hello // world!'); // This is another comment
`;
	const expected = `console.log('Hello // world!');`;
	expect(parse(source, {startRule: 'JavaScript'})).toEqual(expected);
});


test('block comment inline', () => {
	const source = `
/* This is another comment */
console.log('Hello world!');
/* This is another comment */
`;
	const expected = `console.log('Hello world!');`;
	expect(parse(source, {startRule: 'JavaScript'})).toEqual(expected);
});


test('block comment multi lines', () => {
	const source = `
/*
console.log("Don't parse this");
*/
console.log("Hello world!");
`;
	const expected = `console.log("Hello world!");`;
	expect(parse(source, {startRule: 'JavaScript'})).toEqual(expected);
});


test('block comment in string', () => {
	const source = `
console.log("Hello /* world! */");
`;
	const expected = `console.log("Hello /* world! */");`;
	expect(parse(source, {startRule: 'JavaScript'})).toEqual(expected);
});
