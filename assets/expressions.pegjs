// Simple Arithmetics Grammar
// ==========================
//
// Accepts expressions like "2 * (3 + 4)" and computes their value.
// "a"+"v"+(6+9)+"e"=="av15e" return true
// 1.5 == 3/2 returns true

{
    const callVariable = (variableName) => {
        console.log(variableName);
        return 5;
    };
}

Expression
  = CompareTerms
  / Term
  / _ { return false; }

CompareTerms
  = _ head:Term _ op:ComparisonOperator _ tail:Term _ {
    switch (op) {
      case '===':
        return head === tail;
      case '==':
        return head == tail;
      case '!==':
        return head !== tail;
      case '!=':
        return head != tail;
      case '<=':
        return head <= tail;
      case '>=':
        return head >= tail;
      case '<':
        return head < tail;
      case '>':
        return head > tail;
    }
  }

ComparisonOperator
  = "==="
  / "=="
  / "!=="
  / "!="
  / "<="
  / ">="
  / "<"
  / ">"

Term
  = BooleanTerm
  / AdditiveTerm
  / MultiplicativeTerm
  / Factor

Factor
  = "(" _ expr:Expression _ ")" { return expr; }
  / number
  / LowerCase
  / UpperCase
  / string
  / variable

BooleanTerm
  = _ head:boolean tail:(_ ("&&" / "||") _ Term)* _ {
      return tail.reduce(function(result, element) {
        if (element[1] === "&&") { return result && Boolean(element[3]); }
        if (element[1] === "||") { return result || Boolean(element[3]); }
      }, head);
    }
  / _ "!" _ term:Term { return !term; }


AdditiveTerm
  = _ head:MultiplicativeTerm tail:(_ ("+" / "-") _ MultiplicativeTerm)* _ {
      return tail.reduce(function(result, element) {
        if (element[1] === "+") { return result + element[3]; }
        if (element[1] === "-") { return result - element[3]; }
      }, head);
    }

MultiplicativeTerm
  = _ head:Factor tail:(_ ("*" / "/") _ Factor)* {
      return tail.reduce(function(result, element) {
        if (element[1] === "*") { return result * element[3]; }
        if (element[1] === "/") { return result / element[3]; }
      }, head);
    }

// ----- 6. Numbers -----

number "number"
  = minus? int frac? exp? {
    return parseFloat(text());
  }

decimal_point = '.'

digit1_9 = [1-9]

e = [eE]

exp = e (minus / plus)? DIGIT+

frac = decimal_point DIGIT+

int = zero / (digit1_9 DIGIT*)

minus = '-'

plus = '+'

zero = '0'

// ----- 7. Strings -----

string "string"
  = '"' chars:$char_double_quote* '"' { return chars; }
  / "'" chars:$char_single_quote* "'" { return chars; }

UpperCase
  = s:string '.toUpperCase()' {
    return s.toUpperCase();
  }

LowerCase
  = s:string '.toLowerCase()' {
    return s.toLowerCase();
  }

char_double_quote
  = [^\0-\x1F\x22\x5C]
  / '\\"' { return '"' }
  / escape

char_single_quote
  = [^\0-\x1F\x27\x5C]
  / "\\'" { return "'" }
  / escape

escape
  = '\\\\' / '\\b' / '\\f' / '\\n' / '\\r' / '\\t'
  / '\\u' digits:$(HEXDIG HEXDIG HEXDIG HEXDIG)
  { return String.fromCharCode(parseInt(digits, 16)); }

// ----- 8. Boolean ----

boolean "boolean"
  = TRUE { return true; }
  / FALSE { return false; }
  / NULL { return null; }

// ----- 9. Variables -----
variable
  = _ variableName:[$a-zA-Z_][$a-zA-Z0-9_]* {
      return callVariable(variableName);
    }

// ----- Core ABNF Rules -----

// See RFC 4234, Appendix B (http://tools.ietf.org/html/rfc4234).
DIGIT  = [0-9]
HEXDIG = [0-9a-f]i
FALSE = 'false'
TRUE = 'true'
NULL = 'null'

_ "whitespace" = [ \t\n\r]*
