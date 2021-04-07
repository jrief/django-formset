// PEG rules to create parser for <button click="..."> action chain
// Build file `client/components/django-formset/actions.ts` using `npm run pegjs`

// ----- 1. Actions -----

actions
  = successChain:chain _ '!~' _ rejectChain:chain _
  { return { successChain: successChain, rejectChain: rejectChain } }
  / successChain:chain
  { return { successChain: successChain, rejectChain: [] } }

chain
  = lhs:function _ '=>' _ rhs:chain _
  { return [lhs].concat(rhs) }
  / func:function
  { return [func] }

function
  = _ funcname:$keystring '(' args:arglist ')' _
  { return { funcname: funcname, args: args } }
  / funcname:$keystring '()'
  { return { funcname: funcname, args: [] } }
  / funcname:$keystring
  { return { funcname: funcname, args: [] } }

arglist
  = lhs:argument _ ',' _ rhs:arglist
  { return [lhs].concat(rhs) }
  / arg:argument
  { return [arg] }

argument
  = number
  / string
  / object
  / array

_ = [ \t\n\r]*


//
// Adopted from https://github.com/pegjs/pegjs/blob/master/examples/json.pegjs
//
// ----- 2. POJO Grammar -----

begin_array     = _ '[' _
begin_object    = _ '{' _
end_array       = _ ']' _
end_object      = _ '}' _
name_separator  = _ ':' _
value_separator = _ ',' _

// ----- 3. Values -----

value
  = false
  / null
  / true
  / object
  / array
  / number
  / string

false = "false" { return false; }
null  = "null"  { return null;  }
true  = "true"  { return true;  }

// ----- 4. Objects -----

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

keystring
  = [$A-Za-z_] [$0-9A-Za-z_]*

// ----- 5. Arrays -----

array
  = begin_array
    values:(
      head:value
      tail:(value_separator v:value { return v; })*
      { return [head].concat(tail); }
    )?
    end_array
    { return values !== null ? values : []; }

// ----- 6. Numbers -----

number "number"
  = minus? int frac? exp?
  { return parseFloat(text()); }

decimal_point
  = "."

digit1_9
  = [1-9]

e
  = [eE]

exp
  = e (minus / plus)? DIGIT+

frac
  = decimal_point DIGIT+

int
  = zero / (digit1_9 DIGIT*)

minus
  = '-'

plus
  = '+'

zero
  = '0'

// ----- 7. Strings -----

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

// ----- Core ABNF Rules -----

// See RFC 4234, Appendix B (http://tools.ietf.org/html/rfc4234).
DIGIT  = [0-9]
HEXDIG = [0-9a-f]i
