// Simple Arithmetics Grammar
// ==========================
//

Expression
  = _ head:Term _ op:ComparisonOperator _ tail:Term _ {
      return head + op + tail;
  }
  / _ head:Term _ {
      return head;
  }
  / _ { return 'false'; }

Term
  = _ head:Factor _ op:BinaryOperator _ tail:Term _ {
      return head + op + tail;
  }
  / head:Factor {
      return head;
  }
  / op:UnaryOperator head:Factor {
      return op + head;
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

BinaryOperator
  = "+"
  / "-"
  / "*"
  / "/"
  / "&&"
  / "&"
  / "||"
  / "|"

UnaryOperator
  = "!"

Factor
  = "(" _ expr:Expression _ ")" { return '(' + expr + ')'; }
  / number
  / boolean
  / getDataValue
  / s:string { return '\'' + s + '\''; }

getDataValue
  = path:PATH {
    return 'this.getDataValue(\'' + path + '\')';
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
PATH
  = head:VARIABLE tail:('.' VARIABLE)* {
      return tail.reduce(function(result, element) {
          return result + '.' + element[1];
      }, head);
  }


VARIABLE
= var_starter:VAR_STARTER var_remainder:VAR_REMAINDER {
   return var_starter + var_remainder;
}

VAR_STARTER = [$a-zA-Z_]

VAR_REMAINDER
  = identifier:[$a-zA-Z0-9_]* {
    return identifier instanceof Array ? identifier.join('') : identifier;
  }


// ----- Core ABNF Rules -----

// See RFC 4234, Appendix B (http://tools.ietf.org/html/rfc4234).
DIGIT  = [0-9]
HEXDIG = [0-9a-f]i
FALSE = 'false'
TRUE = 'true'
NULL = 'null'

_ "whitespace" = [ \t\n\r]*
