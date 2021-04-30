// @ts-nocheck
export class SyntaxError extends Error {
    constructor(message, expected, found, location) {
        super();
        this.message = message;
        this.expected = expected;
        this.found = found;
        this.location = location;
        this.name = "SyntaxError";
        if (typeof Error.captureStackTrace === "function") {
            Error.captureStackTrace(this, SyntaxError);
        }
    }
    static buildMessage(expected, found) {
        function hex(ch) {
            return ch.charCodeAt(0).toString(16).toUpperCase();
        }
        function literalEscape(s) {
            return s
                .replace(/\\/g, "\\\\")
                .replace(/"/g, "\\\"")
                .replace(/\0/g, "\\0")
                .replace(/\t/g, "\\t")
                .replace(/\n/g, "\\n")
                .replace(/\r/g, "\\r")
                .replace(/[\x00-\x0F]/g, (ch) => "\\x0" + hex(ch))
                .replace(/[\x10-\x1F\x7F-\x9F]/g, (ch) => "\\x" + hex(ch));
        }
        function classEscape(s) {
            return s
                .replace(/\\/g, "\\\\")
                .replace(/\]/g, "\\]")
                .replace(/\^/g, "\\^")
                .replace(/-/g, "\\-")
                .replace(/\0/g, "\\0")
                .replace(/\t/g, "\\t")
                .replace(/\n/g, "\\n")
                .replace(/\r/g, "\\r")
                .replace(/[\x00-\x0F]/g, (ch) => "\\x0" + hex(ch))
                .replace(/[\x10-\x1F\x7F-\x9F]/g, (ch) => "\\x" + hex(ch));
        }
        function describeExpectation(expectation) {
            switch (expectation.type) {
                case "literal":
                    return "\"" + literalEscape(expectation.text) + "\"";
                case "class":
                    const escapedParts = expectation.parts.map((part) => {
                        return Array.isArray(part)
                            ? classEscape(part[0]) + "-" + classEscape(part[1])
                            : classEscape(part);
                    });
                    return "[" + (expectation.inverted ? "^" : "") + escapedParts + "]";
                case "any":
                    return "any character";
                case "end":
                    return "end of input";
                case "other":
                    return expectation.description;
            }
        }
        function describeExpected(expected1) {
            const descriptions = expected1.map(describeExpectation);
            let i;
            let j;
            descriptions.sort();
            if (descriptions.length > 0) {
                for (i = 1, j = 1; i < descriptions.length; i++) {
                    if (descriptions[i - 1] !== descriptions[i]) {
                        descriptions[j] = descriptions[i];
                        j++;
                    }
                }
                descriptions.length = j;
            }
            switch (descriptions.length) {
                case 1:
                    return descriptions[0];
                case 2:
                    return descriptions[0] + " or " + descriptions[1];
                default:
                    return descriptions.slice(0, -1).join(", ")
                        + ", or "
                        + descriptions[descriptions.length - 1];
            }
        }
        function describeFound(found1) {
            return found1 ? "\"" + literalEscape(found1) + "\"" : "end of input";
        }
        return "Expected " + describeExpected(expected) + " but " + describeFound(found) + " found.";
    }
}
function peg$parse(input, options) {
    options = options !== undefined ? options : {};
    const peg$FAILED = {};
    const peg$startRuleFunctions = { actions: peg$parseactions };
    let peg$startRuleFunction = peg$parseactions;
    const peg$c0 = "!~";
    const peg$c1 = peg$literalExpectation("!~", false);
    const peg$c2 = function (successChain, rejectChain) { return { successChain: successChain, rejectChain: rejectChain }; };
    const peg$c3 = function (successChain) { return { successChain: successChain, rejectChain: [] }; };
    const peg$c4 = "->";
    const peg$c5 = peg$literalExpectation("->", false);
    const peg$c6 = function (lhs, rhs) { return [lhs].concat(rhs); };
    const peg$c7 = function (func) { return [func]; };
    const peg$c8 = "(";
    const peg$c9 = peg$literalExpectation("(", false);
    const peg$c10 = ")";
    const peg$c11 = peg$literalExpectation(")", false);
    const peg$c12 = function (funcname, args) { return { funcname: funcname, args: args }; };
    const peg$c13 = "()";
    const peg$c14 = peg$literalExpectation("()", false);
    const peg$c15 = function (funcname) { return { funcname: funcname, args: [] }; };
    const peg$c16 = ",";
    const peg$c17 = peg$literalExpectation(",", false);
    const peg$c18 = function (arg) { return [arg]; };
    const peg$c19 = /^[ \t\n\r]/;
    const peg$c20 = peg$classExpectation([" ", "\t", "\n", "\r"], false, false);
    const peg$c21 = "[";
    const peg$c22 = peg$literalExpectation("[", false);
    const peg$c23 = "{";
    const peg$c24 = peg$literalExpectation("{", false);
    const peg$c25 = "]";
    const peg$c26 = peg$literalExpectation("]", false);
    const peg$c27 = "}";
    const peg$c28 = peg$literalExpectation("}", false);
    const peg$c29 = ":";
    const peg$c30 = peg$literalExpectation(":", false);
    const peg$c31 = "false";
    const peg$c32 = peg$literalExpectation("false", false);
    const peg$c33 = function () { return false; };
    const peg$c34 = "null";
    const peg$c35 = peg$literalExpectation("null", false);
    const peg$c36 = function () { return null; };
    const peg$c37 = "true";
    const peg$c38 = peg$literalExpectation("true", false);
    const peg$c39 = function () { return true; };
    const peg$c40 = function (head, m) { return m; };
    const peg$c41 = function (head, tail) {
        var result = {};
        [head].concat(tail).forEach(function (element) {
            result[element.name] = element.value;
        });
        return result;
    };
    const peg$c42 = function (members) { return members !== null ? members : {}; };
    const peg$c43 = function (name, value) { return { name: name, value: value }; };
    const peg$c44 = /^[$A-Za-z_]/;
    const peg$c45 = peg$classExpectation(["$", ["A", "Z"], ["a", "z"], "_"], false, false);
    const peg$c46 = /^[$0-9A-Za-z_]/;
    const peg$c47 = peg$classExpectation(["$", ["0", "9"], ["A", "Z"], ["a", "z"], "_"], false, false);
    const peg$c48 = function (head, v) { return v; };
    const peg$c49 = function (head, tail) { return [head].concat(tail); };
    const peg$c50 = function (values) { return values !== null ? values : []; };
    const peg$c51 = peg$otherExpectation("number");
    const peg$c52 = function () { return parseFloat(text()); };
    const peg$c53 = ".";
    const peg$c54 = peg$literalExpectation(".", false);
    const peg$c55 = /^[1-9]/;
    const peg$c56 = peg$classExpectation([["1", "9"]], false, false);
    const peg$c57 = /^[eE]/;
    const peg$c58 = peg$classExpectation(["e", "E"], false, false);
    const peg$c59 = "-";
    const peg$c60 = peg$literalExpectation("-", false);
    const peg$c61 = "+";
    const peg$c62 = peg$literalExpectation("+", false);
    const peg$c63 = "0";
    const peg$c64 = peg$literalExpectation("0", false);
    const peg$c65 = peg$otherExpectation("string");
    const peg$c66 = "\"";
    const peg$c67 = peg$literalExpectation("\"", false);
    const peg$c68 = function (chars) { return chars; };
    const peg$c69 = "'";
    const peg$c70 = peg$literalExpectation("'", false);
    const peg$c71 = /^[^\0-\x1F"\\]/;
    const peg$c72 = peg$classExpectation([["\0", "\x1F"], "\"", "\\"], true, false);
    const peg$c73 = "\\\"";
    const peg$c74 = peg$literalExpectation("\\\"", false);
    const peg$c75 = function () { return '"'; };
    const peg$c76 = /^[^\0-\x1F'\\]/;
    const peg$c77 = peg$classExpectation([["\0", "\x1F"], "'", "\\"], true, false);
    const peg$c78 = "\\'";
    const peg$c79 = peg$literalExpectation("\\'", false);
    const peg$c80 = function () { return "'"; };
    const peg$c81 = "\\\\";
    const peg$c82 = peg$literalExpectation("\\\\", false);
    const peg$c83 = "\\b";
    const peg$c84 = peg$literalExpectation("\\b", false);
    const peg$c85 = "\\f";
    const peg$c86 = peg$literalExpectation("\\f", false);
    const peg$c87 = "\\n";
    const peg$c88 = peg$literalExpectation("\\n", false);
    const peg$c89 = "\\r";
    const peg$c90 = peg$literalExpectation("\\r", false);
    const peg$c91 = "\\t";
    const peg$c92 = peg$literalExpectation("\\t", false);
    const peg$c93 = "\\u";
    const peg$c94 = peg$literalExpectation("\\u", false);
    const peg$c95 = function (digits) { return String.fromCharCode(parseInt(digits, 16)); };
    const peg$c96 = /^[0-9]/;
    const peg$c97 = peg$classExpectation([["0", "9"]], false, false);
    const peg$c98 = /^[0-9a-f]/i;
    const peg$c99 = peg$classExpectation([["0", "9"], ["a", "f"]], false, true);
    let peg$currPos = 0;
    let peg$savedPos = 0;
    const peg$posDetailsCache = [{ line: 1, column: 1 }];
    let peg$maxFailPos = 0;
    let peg$maxFailExpected = [];
    let peg$silentFails = 0;
    let peg$result;
    if (options.startRule !== undefined) {
        if (!(options.startRule in peg$startRuleFunctions)) {
            throw new Error("Can't start parsing from rule \"" + options.startRule + "\".");
        }
        peg$startRuleFunction = peg$startRuleFunctions[options.startRule];
    }
    function text() {
        return input.substring(peg$savedPos, peg$currPos);
    }
    function location() {
        return peg$computeLocation(peg$savedPos, peg$currPos);
    }
    function expected(description, location1) {
        location1 = location1 !== undefined
            ? location1
            : peg$computeLocation(peg$savedPos, peg$currPos);
        throw peg$buildStructuredError([peg$otherExpectation(description)], input.substring(peg$savedPos, peg$currPos), location1);
    }
    function error(message, location1) {
        location1 = location1 !== undefined
            ? location1
            : peg$computeLocation(peg$savedPos, peg$currPos);
        throw peg$buildSimpleError(message, location1);
    }
    function peg$literalExpectation(text1, ignoreCase) {
        return { type: "literal", text: text1, ignoreCase: ignoreCase };
    }
    function peg$classExpectation(parts, inverted, ignoreCase) {
        return { type: "class", parts: parts, inverted: inverted, ignoreCase: ignoreCase };
    }
    function peg$anyExpectation() {
        return { type: "any" };
    }
    function peg$endExpectation() {
        return { type: "end" };
    }
    function peg$otherExpectation(description) {
        return { type: "other", description: description };
    }
    function peg$computePosDetails(pos) {
        let details = peg$posDetailsCache[pos];
        let p;
        if (details) {
            return details;
        }
        else {
            p = pos - 1;
            while (!peg$posDetailsCache[p]) {
                p--;
            }
            details = peg$posDetailsCache[p];
            details = {
                line: details.line,
                column: details.column
            };
            while (p < pos) {
                if (input.charCodeAt(p) === 10) {
                    details.line++;
                    details.column = 1;
                }
                else {
                    details.column++;
                }
                p++;
            }
            peg$posDetailsCache[pos] = details;
            return details;
        }
    }
    function peg$computeLocation(startPos, endPos) {
        const startPosDetails = peg$computePosDetails(startPos);
        const endPosDetails = peg$computePosDetails(endPos);
        return {
            start: {
                offset: startPos,
                line: startPosDetails.line,
                column: startPosDetails.column
            },
            end: {
                offset: endPos,
                line: endPosDetails.line,
                column: endPosDetails.column
            }
        };
    }
    function peg$fail(expected1) {
        if (peg$currPos < peg$maxFailPos) {
            return;
        }
        if (peg$currPos > peg$maxFailPos) {
            peg$maxFailPos = peg$currPos;
            peg$maxFailExpected = [];
        }
        peg$maxFailExpected.push(expected1);
    }
    function peg$buildSimpleError(message, location1) {
        return new SyntaxError(message, [], "", location1);
    }
    function peg$buildStructuredError(expected1, found, location1) {
        return new SyntaxError(SyntaxError.buildMessage(expected1, found), expected1, found, location1);
    }
    function peg$parseactions() {
        let s0, s1, s2, s3, s4, s5, s6;
        s0 = peg$currPos;
        s1 = peg$parsechain();
        if (s1 !== peg$FAILED) {
            s2 = peg$parse_();
            if (s2 !== peg$FAILED) {
                if (input.substr(peg$currPos, 2) === peg$c0) {
                    s3 = peg$c0;
                    peg$currPos += 2;
                }
                else {
                    s3 = peg$FAILED;
                    if (peg$silentFails === 0) {
                        peg$fail(peg$c1);
                    }
                }
                if (s3 !== peg$FAILED) {
                    s4 = peg$parse_();
                    if (s4 !== peg$FAILED) {
                        s5 = peg$parsechain();
                        if (s5 !== peg$FAILED) {
                            s6 = peg$parse_();
                            if (s6 !== peg$FAILED) {
                                peg$savedPos = s0;
                                s1 = peg$c2(s1, s5);
                                s0 = s1;
                            }
                            else {
                                peg$currPos = s0;
                                s0 = peg$FAILED;
                            }
                        }
                        else {
                            peg$currPos = s0;
                            s0 = peg$FAILED;
                        }
                    }
                    else {
                        peg$currPos = s0;
                        s0 = peg$FAILED;
                    }
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        if (s0 === peg$FAILED) {
            s0 = peg$currPos;
            s1 = peg$parsechain();
            if (s1 !== peg$FAILED) {
                peg$savedPos = s0;
                s1 = peg$c3(s1);
            }
            s0 = s1;
        }
        return s0;
    }
    function peg$parsechain() {
        let s0, s1, s2, s3, s4, s5, s6;
        s0 = peg$currPos;
        s1 = peg$parsefunction();
        if (s1 !== peg$FAILED) {
            s2 = peg$parse_();
            if (s2 !== peg$FAILED) {
                if (input.substr(peg$currPos, 2) === peg$c4) {
                    s3 = peg$c4;
                    peg$currPos += 2;
                }
                else {
                    s3 = peg$FAILED;
                    if (peg$silentFails === 0) {
                        peg$fail(peg$c5);
                    }
                }
                if (s3 !== peg$FAILED) {
                    s4 = peg$parse_();
                    if (s4 !== peg$FAILED) {
                        s5 = peg$parsechain();
                        if (s5 !== peg$FAILED) {
                            s6 = peg$parse_();
                            if (s6 !== peg$FAILED) {
                                peg$savedPos = s0;
                                s1 = peg$c6(s1, s5);
                                s0 = s1;
                            }
                            else {
                                peg$currPos = s0;
                                s0 = peg$FAILED;
                            }
                        }
                        else {
                            peg$currPos = s0;
                            s0 = peg$FAILED;
                        }
                    }
                    else {
                        peg$currPos = s0;
                        s0 = peg$FAILED;
                    }
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        if (s0 === peg$FAILED) {
            s0 = peg$currPos;
            s1 = peg$parsefunction();
            if (s1 !== peg$FAILED) {
                peg$savedPos = s0;
                s1 = peg$c7(s1);
            }
            s0 = s1;
        }
        return s0;
    }
    function peg$parsefunction() {
        let s0, s1, s2, s3, s4, s5, s6;
        s0 = peg$currPos;
        s1 = peg$parse_();
        if (s1 !== peg$FAILED) {
            s2 = peg$currPos;
            s3 = peg$parsekeystring();
            if (s3 !== peg$FAILED) {
                s2 = input.substring(s2, peg$currPos);
            }
            else {
                s2 = s3;
            }
            if (s2 !== peg$FAILED) {
                if (input.charCodeAt(peg$currPos) === 40) {
                    s3 = peg$c8;
                    peg$currPos++;
                }
                else {
                    s3 = peg$FAILED;
                    if (peg$silentFails === 0) {
                        peg$fail(peg$c9);
                    }
                }
                if (s3 !== peg$FAILED) {
                    s4 = peg$parsearglist();
                    if (s4 !== peg$FAILED) {
                        if (input.charCodeAt(peg$currPos) === 41) {
                            s5 = peg$c10;
                            peg$currPos++;
                        }
                        else {
                            s5 = peg$FAILED;
                            if (peg$silentFails === 0) {
                                peg$fail(peg$c11);
                            }
                        }
                        if (s5 !== peg$FAILED) {
                            s6 = peg$parse_();
                            if (s6 !== peg$FAILED) {
                                peg$savedPos = s0;
                                s1 = peg$c12(s2, s4);
                                s0 = s1;
                            }
                            else {
                                peg$currPos = s0;
                                s0 = peg$FAILED;
                            }
                        }
                        else {
                            peg$currPos = s0;
                            s0 = peg$FAILED;
                        }
                    }
                    else {
                        peg$currPos = s0;
                        s0 = peg$FAILED;
                    }
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        if (s0 === peg$FAILED) {
            s0 = peg$currPos;
            s1 = peg$currPos;
            s2 = peg$parsekeystring();
            if (s2 !== peg$FAILED) {
                s1 = input.substring(s1, peg$currPos);
            }
            else {
                s1 = s2;
            }
            if (s1 !== peg$FAILED) {
                if (input.substr(peg$currPos, 2) === peg$c13) {
                    s2 = peg$c13;
                    peg$currPos += 2;
                }
                else {
                    s2 = peg$FAILED;
                    if (peg$silentFails === 0) {
                        peg$fail(peg$c14);
                    }
                }
                if (s2 !== peg$FAILED) {
                    peg$savedPos = s0;
                    s1 = peg$c15(s1);
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
            if (s0 === peg$FAILED) {
                s0 = peg$currPos;
                s1 = peg$currPos;
                s2 = peg$parsekeystring();
                if (s2 !== peg$FAILED) {
                    s1 = input.substring(s1, peg$currPos);
                }
                else {
                    s1 = s2;
                }
                if (s1 !== peg$FAILED) {
                    peg$savedPos = s0;
                    s1 = peg$c15(s1);
                }
                s0 = s1;
            }
        }
        return s0;
    }
    function peg$parsearglist() {
        let s0, s1, s2, s3, s4, s5;
        s0 = peg$currPos;
        s1 = peg$parseargument();
        if (s1 !== peg$FAILED) {
            s2 = peg$parse_();
            if (s2 !== peg$FAILED) {
                if (input.charCodeAt(peg$currPos) === 44) {
                    s3 = peg$c16;
                    peg$currPos++;
                }
                else {
                    s3 = peg$FAILED;
                    if (peg$silentFails === 0) {
                        peg$fail(peg$c17);
                    }
                }
                if (s3 !== peg$FAILED) {
                    s4 = peg$parse_();
                    if (s4 !== peg$FAILED) {
                        s5 = peg$parsearglist();
                        if (s5 !== peg$FAILED) {
                            peg$savedPos = s0;
                            s1 = peg$c6(s1, s5);
                            s0 = s1;
                        }
                        else {
                            peg$currPos = s0;
                            s0 = peg$FAILED;
                        }
                    }
                    else {
                        peg$currPos = s0;
                        s0 = peg$FAILED;
                    }
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        if (s0 === peg$FAILED) {
            s0 = peg$currPos;
            s1 = peg$parseargument();
            if (s1 !== peg$FAILED) {
                peg$savedPos = s0;
                s1 = peg$c18(s1);
            }
            s0 = s1;
        }
        return s0;
    }
    function peg$parseargument() {
        let s0;
        s0 = peg$parsenumber();
        if (s0 === peg$FAILED) {
            s0 = peg$parsestring();
            if (s0 === peg$FAILED) {
                s0 = peg$parseobject();
                if (s0 === peg$FAILED) {
                    s0 = peg$parsearray();
                }
            }
        }
        return s0;
    }
    function peg$parse_() {
        let s0, s1;
        s0 = [];
        if (peg$c19.test(input.charAt(peg$currPos))) {
            s1 = input.charAt(peg$currPos);
            peg$currPos++;
        }
        else {
            s1 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c20);
            }
        }
        while (s1 !== peg$FAILED) {
            s0.push(s1);
            if (peg$c19.test(input.charAt(peg$currPos))) {
                s1 = input.charAt(peg$currPos);
                peg$currPos++;
            }
            else {
                s1 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c20);
                }
            }
        }
        return s0;
    }
    function peg$parsebegin_array() {
        let s0, s1, s2, s3;
        s0 = peg$currPos;
        s1 = peg$parse_();
        if (s1 !== peg$FAILED) {
            if (input.charCodeAt(peg$currPos) === 91) {
                s2 = peg$c21;
                peg$currPos++;
            }
            else {
                s2 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c22);
                }
            }
            if (s2 !== peg$FAILED) {
                s3 = peg$parse_();
                if (s3 !== peg$FAILED) {
                    s1 = [s1, s2, s3];
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parsebegin_object() {
        let s0, s1, s2, s3;
        s0 = peg$currPos;
        s1 = peg$parse_();
        if (s1 !== peg$FAILED) {
            if (input.charCodeAt(peg$currPos) === 123) {
                s2 = peg$c23;
                peg$currPos++;
            }
            else {
                s2 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c24);
                }
            }
            if (s2 !== peg$FAILED) {
                s3 = peg$parse_();
                if (s3 !== peg$FAILED) {
                    s1 = [s1, s2, s3];
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parseend_array() {
        let s0, s1, s2, s3;
        s0 = peg$currPos;
        s1 = peg$parse_();
        if (s1 !== peg$FAILED) {
            if (input.charCodeAt(peg$currPos) === 93) {
                s2 = peg$c25;
                peg$currPos++;
            }
            else {
                s2 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c26);
                }
            }
            if (s2 !== peg$FAILED) {
                s3 = peg$parse_();
                if (s3 !== peg$FAILED) {
                    s1 = [s1, s2, s3];
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parseend_object() {
        let s0, s1, s2, s3;
        s0 = peg$currPos;
        s1 = peg$parse_();
        if (s1 !== peg$FAILED) {
            if (input.charCodeAt(peg$currPos) === 125) {
                s2 = peg$c27;
                peg$currPos++;
            }
            else {
                s2 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c28);
                }
            }
            if (s2 !== peg$FAILED) {
                s3 = peg$parse_();
                if (s3 !== peg$FAILED) {
                    s1 = [s1, s2, s3];
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parsename_separator() {
        let s0, s1, s2, s3;
        s0 = peg$currPos;
        s1 = peg$parse_();
        if (s1 !== peg$FAILED) {
            if (input.charCodeAt(peg$currPos) === 58) {
                s2 = peg$c29;
                peg$currPos++;
            }
            else {
                s2 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c30);
                }
            }
            if (s2 !== peg$FAILED) {
                s3 = peg$parse_();
                if (s3 !== peg$FAILED) {
                    s1 = [s1, s2, s3];
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parsevalue_separator() {
        let s0, s1, s2, s3;
        s0 = peg$currPos;
        s1 = peg$parse_();
        if (s1 !== peg$FAILED) {
            if (input.charCodeAt(peg$currPos) === 44) {
                s2 = peg$c16;
                peg$currPos++;
            }
            else {
                s2 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c17);
                }
            }
            if (s2 !== peg$FAILED) {
                s3 = peg$parse_();
                if (s3 !== peg$FAILED) {
                    s1 = [s1, s2, s3];
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parsevalue() {
        let s0;
        s0 = peg$parsefalse();
        if (s0 === peg$FAILED) {
            s0 = peg$parsenull();
            if (s0 === peg$FAILED) {
                s0 = peg$parsetrue();
                if (s0 === peg$FAILED) {
                    s0 = peg$parseobject();
                    if (s0 === peg$FAILED) {
                        s0 = peg$parsearray();
                        if (s0 === peg$FAILED) {
                            s0 = peg$parsenumber();
                            if (s0 === peg$FAILED) {
                                s0 = peg$parsestring();
                            }
                        }
                    }
                }
            }
        }
        return s0;
    }
    function peg$parsefalse() {
        let s0, s1;
        s0 = peg$currPos;
        if (input.substr(peg$currPos, 5) === peg$c31) {
            s1 = peg$c31;
            peg$currPos += 5;
        }
        else {
            s1 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c32);
            }
        }
        if (s1 !== peg$FAILED) {
            peg$savedPos = s0;
            s1 = peg$c33();
        }
        s0 = s1;
        return s0;
    }
    function peg$parsenull() {
        let s0, s1;
        s0 = peg$currPos;
        if (input.substr(peg$currPos, 4) === peg$c34) {
            s1 = peg$c34;
            peg$currPos += 4;
        }
        else {
            s1 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c35);
            }
        }
        if (s1 !== peg$FAILED) {
            peg$savedPos = s0;
            s1 = peg$c36();
        }
        s0 = s1;
        return s0;
    }
    function peg$parsetrue() {
        let s0, s1;
        s0 = peg$currPos;
        if (input.substr(peg$currPos, 4) === peg$c37) {
            s1 = peg$c37;
            peg$currPos += 4;
        }
        else {
            s1 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c38);
            }
        }
        if (s1 !== peg$FAILED) {
            peg$savedPos = s0;
            s1 = peg$c39();
        }
        s0 = s1;
        return s0;
    }
    function peg$parseobject() {
        let s0, s1, s2, s3, s4, s5, s6, s7;
        s0 = peg$currPos;
        s1 = peg$parsebegin_object();
        if (s1 !== peg$FAILED) {
            s2 = peg$currPos;
            s3 = peg$parsemember();
            if (s3 !== peg$FAILED) {
                s4 = [];
                s5 = peg$currPos;
                s6 = peg$parsevalue_separator();
                if (s6 !== peg$FAILED) {
                    s7 = peg$parsemember();
                    if (s7 !== peg$FAILED) {
                        peg$savedPos = s5;
                        s6 = peg$c40(s3, s7);
                        s5 = s6;
                    }
                    else {
                        peg$currPos = s5;
                        s5 = peg$FAILED;
                    }
                }
                else {
                    peg$currPos = s5;
                    s5 = peg$FAILED;
                }
                while (s5 !== peg$FAILED) {
                    s4.push(s5);
                    s5 = peg$currPos;
                    s6 = peg$parsevalue_separator();
                    if (s6 !== peg$FAILED) {
                        s7 = peg$parsemember();
                        if (s7 !== peg$FAILED) {
                            peg$savedPos = s5;
                            s6 = peg$c40(s3, s7);
                            s5 = s6;
                        }
                        else {
                            peg$currPos = s5;
                            s5 = peg$FAILED;
                        }
                    }
                    else {
                        peg$currPos = s5;
                        s5 = peg$FAILED;
                    }
                }
                if (s4 !== peg$FAILED) {
                    peg$savedPos = s2;
                    s3 = peg$c41(s3, s4);
                    s2 = s3;
                }
                else {
                    peg$currPos = s2;
                    s2 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s2;
                s2 = peg$FAILED;
            }
            if (s2 === peg$FAILED) {
                s2 = null;
            }
            if (s2 !== peg$FAILED) {
                s3 = peg$parseend_object();
                if (s3 !== peg$FAILED) {
                    peg$savedPos = s0;
                    s1 = peg$c42(s2);
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parsemember() {
        let s0, s1, s2, s3;
        s0 = peg$currPos;
        s1 = peg$parsestring();
        if (s1 !== peg$FAILED) {
            s2 = peg$parsename_separator();
            if (s2 !== peg$FAILED) {
                s3 = peg$parsevalue();
                if (s3 !== peg$FAILED) {
                    peg$savedPos = s0;
                    s1 = peg$c43(s1, s3);
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        if (s0 === peg$FAILED) {
            s0 = peg$currPos;
            s1 = peg$currPos;
            s2 = peg$parsekeystring();
            if (s2 !== peg$FAILED) {
                s1 = input.substring(s1, peg$currPos);
            }
            else {
                s1 = s2;
            }
            if (s1 !== peg$FAILED) {
                s2 = peg$parsename_separator();
                if (s2 !== peg$FAILED) {
                    s3 = peg$parsevalue();
                    if (s3 !== peg$FAILED) {
                        peg$savedPos = s0;
                        s1 = peg$c43(s1, s3);
                        s0 = s1;
                    }
                    else {
                        peg$currPos = s0;
                        s0 = peg$FAILED;
                    }
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        return s0;
    }
    function peg$parsekeystring() {
        let s0, s1, s2, s3;
        s0 = peg$currPos;
        if (peg$c44.test(input.charAt(peg$currPos))) {
            s1 = input.charAt(peg$currPos);
            peg$currPos++;
        }
        else {
            s1 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c45);
            }
        }
        if (s1 !== peg$FAILED) {
            s2 = [];
            if (peg$c46.test(input.charAt(peg$currPos))) {
                s3 = input.charAt(peg$currPos);
                peg$currPos++;
            }
            else {
                s3 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c47);
                }
            }
            while (s3 !== peg$FAILED) {
                s2.push(s3);
                if (peg$c46.test(input.charAt(peg$currPos))) {
                    s3 = input.charAt(peg$currPos);
                    peg$currPos++;
                }
                else {
                    s3 = peg$FAILED;
                    if (peg$silentFails === 0) {
                        peg$fail(peg$c47);
                    }
                }
            }
            if (s2 !== peg$FAILED) {
                s1 = [s1, s2];
                s0 = s1;
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parsearray() {
        let s0, s1, s2, s3, s4, s5, s6, s7;
        s0 = peg$currPos;
        s1 = peg$parsebegin_array();
        if (s1 !== peg$FAILED) {
            s2 = peg$currPos;
            s3 = peg$parsevalue();
            if (s3 !== peg$FAILED) {
                s4 = [];
                s5 = peg$currPos;
                s6 = peg$parsevalue_separator();
                if (s6 !== peg$FAILED) {
                    s7 = peg$parsevalue();
                    if (s7 !== peg$FAILED) {
                        peg$savedPos = s5;
                        s6 = peg$c48(s3, s7);
                        s5 = s6;
                    }
                    else {
                        peg$currPos = s5;
                        s5 = peg$FAILED;
                    }
                }
                else {
                    peg$currPos = s5;
                    s5 = peg$FAILED;
                }
                while (s5 !== peg$FAILED) {
                    s4.push(s5);
                    s5 = peg$currPos;
                    s6 = peg$parsevalue_separator();
                    if (s6 !== peg$FAILED) {
                        s7 = peg$parsevalue();
                        if (s7 !== peg$FAILED) {
                            peg$savedPos = s5;
                            s6 = peg$c48(s3, s7);
                            s5 = s6;
                        }
                        else {
                            peg$currPos = s5;
                            s5 = peg$FAILED;
                        }
                    }
                    else {
                        peg$currPos = s5;
                        s5 = peg$FAILED;
                    }
                }
                if (s4 !== peg$FAILED) {
                    peg$savedPos = s2;
                    s3 = peg$c49(s3, s4);
                    s2 = s3;
                }
                else {
                    peg$currPos = s2;
                    s2 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s2;
                s2 = peg$FAILED;
            }
            if (s2 === peg$FAILED) {
                s2 = null;
            }
            if (s2 !== peg$FAILED) {
                s3 = peg$parseend_array();
                if (s3 !== peg$FAILED) {
                    peg$savedPos = s0;
                    s1 = peg$c50(s2);
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parsenumber() {
        let s0, s1, s2, s3, s4;
        peg$silentFails++;
        s0 = peg$currPos;
        s1 = peg$parseminus();
        if (s1 === peg$FAILED) {
            s1 = null;
        }
        if (s1 !== peg$FAILED) {
            s2 = peg$parseint();
            if (s2 !== peg$FAILED) {
                s3 = peg$parsefrac();
                if (s3 === peg$FAILED) {
                    s3 = null;
                }
                if (s3 !== peg$FAILED) {
                    s4 = peg$parseexp();
                    if (s4 === peg$FAILED) {
                        s4 = null;
                    }
                    if (s4 !== peg$FAILED) {
                        peg$savedPos = s0;
                        s1 = peg$c52();
                        s0 = s1;
                    }
                    else {
                        peg$currPos = s0;
                        s0 = peg$FAILED;
                    }
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        peg$silentFails--;
        if (s0 === peg$FAILED) {
            s1 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c51);
            }
        }
        return s0;
    }
    function peg$parsedecimal_point() {
        let s0;
        if (input.charCodeAt(peg$currPos) === 46) {
            s0 = peg$c53;
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c54);
            }
        }
        return s0;
    }
    function peg$parsedigit1_9() {
        let s0;
        if (peg$c55.test(input.charAt(peg$currPos))) {
            s0 = input.charAt(peg$currPos);
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c56);
            }
        }
        return s0;
    }
    function peg$parsee() {
        let s0;
        if (peg$c57.test(input.charAt(peg$currPos))) {
            s0 = input.charAt(peg$currPos);
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c58);
            }
        }
        return s0;
    }
    function peg$parseexp() {
        let s0, s1, s2, s3, s4;
        s0 = peg$currPos;
        s1 = peg$parsee();
        if (s1 !== peg$FAILED) {
            s2 = peg$parseminus();
            if (s2 === peg$FAILED) {
                s2 = peg$parseplus();
            }
            if (s2 === peg$FAILED) {
                s2 = null;
            }
            if (s2 !== peg$FAILED) {
                s3 = [];
                s4 = peg$parseDIGIT();
                if (s4 !== peg$FAILED) {
                    while (s4 !== peg$FAILED) {
                        s3.push(s4);
                        s4 = peg$parseDIGIT();
                    }
                }
                else {
                    s3 = peg$FAILED;
                }
                if (s3 !== peg$FAILED) {
                    s1 = [s1, s2, s3];
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parsefrac() {
        let s0, s1, s2, s3;
        s0 = peg$currPos;
        s1 = peg$parsedecimal_point();
        if (s1 !== peg$FAILED) {
            s2 = [];
            s3 = peg$parseDIGIT();
            if (s3 !== peg$FAILED) {
                while (s3 !== peg$FAILED) {
                    s2.push(s3);
                    s3 = peg$parseDIGIT();
                }
            }
            else {
                s2 = peg$FAILED;
            }
            if (s2 !== peg$FAILED) {
                s1 = [s1, s2];
                s0 = s1;
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        return s0;
    }
    function peg$parseint() {
        let s0, s1, s2, s3;
        s0 = peg$parsezero();
        if (s0 === peg$FAILED) {
            s0 = peg$currPos;
            s1 = peg$parsedigit1_9();
            if (s1 !== peg$FAILED) {
                s2 = [];
                s3 = peg$parseDIGIT();
                while (s3 !== peg$FAILED) {
                    s2.push(s3);
                    s3 = peg$parseDIGIT();
                }
                if (s2 !== peg$FAILED) {
                    s1 = [s1, s2];
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        return s0;
    }
    function peg$parseminus() {
        let s0;
        if (input.charCodeAt(peg$currPos) === 45) {
            s0 = peg$c59;
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c60);
            }
        }
        return s0;
    }
    function peg$parseplus() {
        let s0;
        if (input.charCodeAt(peg$currPos) === 43) {
            s0 = peg$c61;
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c62);
            }
        }
        return s0;
    }
    function peg$parsezero() {
        let s0;
        if (input.charCodeAt(peg$currPos) === 48) {
            s0 = peg$c63;
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c64);
            }
        }
        return s0;
    }
    function peg$parsestring() {
        let s0, s1, s2, s3, s4;
        peg$silentFails++;
        s0 = peg$currPos;
        if (input.charCodeAt(peg$currPos) === 34) {
            s1 = peg$c66;
            peg$currPos++;
        }
        else {
            s1 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c67);
            }
        }
        if (s1 !== peg$FAILED) {
            s2 = peg$currPos;
            s3 = [];
            s4 = peg$parsechar_double_quote();
            while (s4 !== peg$FAILED) {
                s3.push(s4);
                s4 = peg$parsechar_double_quote();
            }
            if (s3 !== peg$FAILED) {
                s2 = input.substring(s2, peg$currPos);
            }
            else {
                s2 = s3;
            }
            if (s2 !== peg$FAILED) {
                if (input.charCodeAt(peg$currPos) === 34) {
                    s3 = peg$c66;
                    peg$currPos++;
                }
                else {
                    s3 = peg$FAILED;
                    if (peg$silentFails === 0) {
                        peg$fail(peg$c67);
                    }
                }
                if (s3 !== peg$FAILED) {
                    peg$savedPos = s0;
                    s1 = peg$c68(s2);
                    s0 = s1;
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        else {
            peg$currPos = s0;
            s0 = peg$FAILED;
        }
        if (s0 === peg$FAILED) {
            s0 = peg$currPos;
            if (input.charCodeAt(peg$currPos) === 39) {
                s1 = peg$c69;
                peg$currPos++;
            }
            else {
                s1 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c70);
                }
            }
            if (s1 !== peg$FAILED) {
                s2 = peg$currPos;
                s3 = [];
                s4 = peg$parsechar_single_quote();
                while (s4 !== peg$FAILED) {
                    s3.push(s4);
                    s4 = peg$parsechar_single_quote();
                }
                if (s3 !== peg$FAILED) {
                    s2 = input.substring(s2, peg$currPos);
                }
                else {
                    s2 = s3;
                }
                if (s2 !== peg$FAILED) {
                    if (input.charCodeAt(peg$currPos) === 39) {
                        s3 = peg$c69;
                        peg$currPos++;
                    }
                    else {
                        s3 = peg$FAILED;
                        if (peg$silentFails === 0) {
                            peg$fail(peg$c70);
                        }
                    }
                    if (s3 !== peg$FAILED) {
                        peg$savedPos = s0;
                        s1 = peg$c68(s2);
                        s0 = s1;
                    }
                    else {
                        peg$currPos = s0;
                        s0 = peg$FAILED;
                    }
                }
                else {
                    peg$currPos = s0;
                    s0 = peg$FAILED;
                }
            }
            else {
                peg$currPos = s0;
                s0 = peg$FAILED;
            }
        }
        peg$silentFails--;
        if (s0 === peg$FAILED) {
            s1 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c65);
            }
        }
        return s0;
    }
    function peg$parsechar_double_quote() {
        let s0, s1;
        if (peg$c71.test(input.charAt(peg$currPos))) {
            s0 = input.charAt(peg$currPos);
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c72);
            }
        }
        if (s0 === peg$FAILED) {
            s0 = peg$currPos;
            if (input.substr(peg$currPos, 2) === peg$c73) {
                s1 = peg$c73;
                peg$currPos += 2;
            }
            else {
                s1 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c74);
                }
            }
            if (s1 !== peg$FAILED) {
                peg$savedPos = s0;
                s1 = peg$c75();
            }
            s0 = s1;
            if (s0 === peg$FAILED) {
                s0 = peg$parseescape();
            }
        }
        return s0;
    }
    function peg$parsechar_single_quote() {
        let s0, s1;
        if (peg$c76.test(input.charAt(peg$currPos))) {
            s0 = input.charAt(peg$currPos);
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c77);
            }
        }
        if (s0 === peg$FAILED) {
            s0 = peg$currPos;
            if (input.substr(peg$currPos, 2) === peg$c78) {
                s1 = peg$c78;
                peg$currPos += 2;
            }
            else {
                s1 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c79);
                }
            }
            if (s1 !== peg$FAILED) {
                peg$savedPos = s0;
                s1 = peg$c80();
            }
            s0 = s1;
            if (s0 === peg$FAILED) {
                s0 = peg$parseescape();
            }
        }
        return s0;
    }
    function peg$parseescape() {
        let s0, s1, s2, s3, s4, s5, s6, s7;
        if (input.substr(peg$currPos, 2) === peg$c81) {
            s0 = peg$c81;
            peg$currPos += 2;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c82);
            }
        }
        if (s0 === peg$FAILED) {
            if (input.substr(peg$currPos, 2) === peg$c83) {
                s0 = peg$c83;
                peg$currPos += 2;
            }
            else {
                s0 = peg$FAILED;
                if (peg$silentFails === 0) {
                    peg$fail(peg$c84);
                }
            }
            if (s0 === peg$FAILED) {
                if (input.substr(peg$currPos, 2) === peg$c85) {
                    s0 = peg$c85;
                    peg$currPos += 2;
                }
                else {
                    s0 = peg$FAILED;
                    if (peg$silentFails === 0) {
                        peg$fail(peg$c86);
                    }
                }
                if (s0 === peg$FAILED) {
                    if (input.substr(peg$currPos, 2) === peg$c87) {
                        s0 = peg$c87;
                        peg$currPos += 2;
                    }
                    else {
                        s0 = peg$FAILED;
                        if (peg$silentFails === 0) {
                            peg$fail(peg$c88);
                        }
                    }
                    if (s0 === peg$FAILED) {
                        if (input.substr(peg$currPos, 2) === peg$c89) {
                            s0 = peg$c89;
                            peg$currPos += 2;
                        }
                        else {
                            s0 = peg$FAILED;
                            if (peg$silentFails === 0) {
                                peg$fail(peg$c90);
                            }
                        }
                        if (s0 === peg$FAILED) {
                            if (input.substr(peg$currPos, 2) === peg$c91) {
                                s0 = peg$c91;
                                peg$currPos += 2;
                            }
                            else {
                                s0 = peg$FAILED;
                                if (peg$silentFails === 0) {
                                    peg$fail(peg$c92);
                                }
                            }
                            if (s0 === peg$FAILED) {
                                s0 = peg$currPos;
                                if (input.substr(peg$currPos, 2) === peg$c93) {
                                    s1 = peg$c93;
                                    peg$currPos += 2;
                                }
                                else {
                                    s1 = peg$FAILED;
                                    if (peg$silentFails === 0) {
                                        peg$fail(peg$c94);
                                    }
                                }
                                if (s1 !== peg$FAILED) {
                                    s2 = peg$currPos;
                                    s3 = peg$currPos;
                                    s4 = peg$parseHEXDIG();
                                    if (s4 !== peg$FAILED) {
                                        s5 = peg$parseHEXDIG();
                                        if (s5 !== peg$FAILED) {
                                            s6 = peg$parseHEXDIG();
                                            if (s6 !== peg$FAILED) {
                                                s7 = peg$parseHEXDIG();
                                                if (s7 !== peg$FAILED) {
                                                    s4 = [s4, s5, s6, s7];
                                                    s3 = s4;
                                                }
                                                else {
                                                    peg$currPos = s3;
                                                    s3 = peg$FAILED;
                                                }
                                            }
                                            else {
                                                peg$currPos = s3;
                                                s3 = peg$FAILED;
                                            }
                                        }
                                        else {
                                            peg$currPos = s3;
                                            s3 = peg$FAILED;
                                        }
                                    }
                                    else {
                                        peg$currPos = s3;
                                        s3 = peg$FAILED;
                                    }
                                    if (s3 !== peg$FAILED) {
                                        s2 = input.substring(s2, peg$currPos);
                                    }
                                    else {
                                        s2 = s3;
                                    }
                                    if (s2 !== peg$FAILED) {
                                        peg$savedPos = s0;
                                        s1 = peg$c95(s2);
                                        s0 = s1;
                                    }
                                    else {
                                        peg$currPos = s0;
                                        s0 = peg$FAILED;
                                    }
                                }
                                else {
                                    peg$currPos = s0;
                                    s0 = peg$FAILED;
                                }
                            }
                        }
                    }
                }
            }
        }
        return s0;
    }
    function peg$parseDIGIT() {
        let s0;
        if (peg$c96.test(input.charAt(peg$currPos))) {
            s0 = input.charAt(peg$currPos);
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c97);
            }
        }
        return s0;
    }
    function peg$parseHEXDIG() {
        let s0;
        if (peg$c98.test(input.charAt(peg$currPos))) {
            s0 = input.charAt(peg$currPos);
            peg$currPos++;
        }
        else {
            s0 = peg$FAILED;
            if (peg$silentFails === 0) {
                peg$fail(peg$c99);
            }
        }
        return s0;
    }
    peg$result = peg$startRuleFunction();
    if (peg$result !== peg$FAILED && peg$currPos === input.length) {
        return peg$result;
    }
    else {
        if (peg$result !== peg$FAILED && peg$currPos < input.length) {
            peg$fail(peg$endExpectation());
        }
        throw peg$buildStructuredError(peg$maxFailExpected, peg$maxFailPos < input.length ? input.charAt(peg$maxFailPos) : null, peg$maxFailPos < input.length
            ? peg$computeLocation(peg$maxFailPos, peg$maxFailPos + 1)
            : peg$computeLocation(peg$maxFailPos, peg$maxFailPos));
    }
}
export const parse = peg$parse;
