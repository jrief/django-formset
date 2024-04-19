// PEG rules to create parser for various HTML attributes used by django-formset
// Build file `client/components/django-formset/actions.ts` using `npm run pegjs`

// ----- A. OperabilityExpression -----
// The starting rule for `<ANY df-show="..."` …>`, `<ANY df-hide="..." …>`, `<ANY df-disable="..." …>`
// and the ternary operator in <button df-click="condition ? ... : ...">.

OperabilityExpression
  = _ head:Factor _ tail:(_ Operator _ OperabilityExpression)* _ {
      return tail.reduce((result, element) => result + element[1] + element[3], head);
  }
  / _ { return 'false'; }

Operator
  = "==="
  / "=="
  / "!=="
  / "!="
  / "<="
  / ">="
  / "<"
  / ">"
  / "+"
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
  = "(" _ expr:OperabilityExpression _ ")" { return `(${expr})`; }
  / scalar
  / getDataValue

getDataValue
  = path:PATH {
      const parts = path.split('.').map(part => `'${part}'`);
      return `this.getDataValue([${parts.join(',')}])`;
  }


// ----- B. InduceExpression -----
// The starting rule for `<ANY df-induce="..."` …>`.

InduceExpression
  = _ head:InduceFactor _ tail:(_ Operator _ InduceExpression)* _ {
      return tail.reduce((result, element) => result + element[1] + element[3], head);
  }
  / _ { return 'false'; }

InduceFactor
  = "(" _ expr:InduceExpression _ ")" { return `(${expr})`; }
  / isButtonActive
  / getDataValue
  / scalar

isButtonActive
  = path:PATH ":" action:VARIABLE {
      const parts = path.split('.').map(part => `'${part}'`);
      return `this.isButtonActive([${parts.join(',')}],'${action}')`;
  }


// ----- C. Actions -----
// The starting rule for <button `df-click="..."` …>.

Actions
  = successChain:ternary _ '!~' _ rejectChain:ternary _ {
    return { successChain: successChain, rejectChain: rejectChain };
  }
  / successChain:ternary {
    return { successChain: successChain, rejectChain: [] };
  }

ternary
  = _ condition:OperabilityExpression _ "?" _ fulfilled:ternary _ ":" _ otherwise:ternary _ {
    return condition ? fulfilled : otherwise;
  }
  / chain

chain
  = lhs:function _ '->' _ rhs:chain _ { return [lhs].concat(rhs) }
  / func:function { return [func] }

function
  = _ funcname:$keystring '(' args:arglist ')' _ {
    return { funcname: funcname, args: args };
  }
  / funcname:$keystring '()' {
    return { funcname: funcname, args: [] };
  }
  / funcname:$keystring {
    return { funcname: funcname, args: [] };
  }

scalar
  = number
  / boolean
  / s:string { return `'${s}'`; }

arglist
  = lhs:argument _ ',' _ rhs:arglist { return [lhs].concat(rhs) }
  / arg:argument { return [arg] }

argument
  = number
  / string
  / object
  / array


// ----- D. JSON -----

JSON_text = _ @value _

//
// Adopted from https://github.com/peggyjs/peggy/blob/main/examples/json.pegjs
//
// ----- 1. POJO Grammar -----

begin_array     = _ '[' _
begin_object    = _ '{' _
end_array       = _ ']' _
end_object      = _ '}' _
name_separator  = _ ':' _
value_separator = _ ',' _


// ----- 2. Values -----

value
  = boolean
  / object
  / array
  / number
  / string


// ----- 3. Objects -----

object
  = begin_object
    members:(
      head:member
      tail:(value_separator m:member { return m; })*
      {
        var result = {};

        [head].concat(tail).forEach(function(element) {
          result[element.name] = element.value;
        });

        return result;
      }
    )?
    end_object
    { return members !== null ? members: {}; }

member
  = name:string name_separator value:value
  { return { name: name, value: value } }
  / name:$keystring name_separator value:value
  { return { name: name, value: value } }

keystring = [$A-Za-z_][$0-9A-Za-z_]*

// ----- 4. Arrays -----

array
  = begin_array
    values:(
      head:value
      tail:(value_separator v:value { return v; })*
      { return [head].concat(tail); }
    )?
    end_array
    { return values !== null ? values : []; }


// ----- 5. Numbers -----

number "number"
  = minus? int frac? exp?
  { return parseFloat(text()); }

decimal_point = "."
digit1_9 = [1-9]
e = [eE]
exp = e (minus / plus)? DIGIT+
frac = decimal_point DIGIT+
int = zero / (digit1_9 DIGIT*)
minus = '-'
plus = '+'
zero = '0'


// ----- 6. Strings -----

string "string"
  = '"' chars:$char_double_quote* '"' { return chars }
  / "'" chars:$char_single_quote* "'" { return chars }

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
  { return String.fromCharCode(parseInt(digits, 16)) }


// ----- 7. Boolean ----

boolean "boolean"
  = TRUE { return true; }
  / FALSE { return false; }
  / NULL { return null; }

FALSE = 'false'
TRUE = 'true'
NULL = 'null'


// ----- 8. Variables -----

PATH
  = head:VAR_PREFIX tail:('.' (VARIABLE / DIGIT+))* {
      return tail.reduce(function(result, element) {
          return result + '.' + element[1];
      }, head);
  }

VAR_PREFIX
  = prefix:('...' / '..' / '.') variable:VARIABLE {
      return prefix + variable;
  }
  / VARIABLE

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
_ = [ \t\n\r]*
DIGIT  = [0-9]
HEXDIG = [0-9a-f]i
