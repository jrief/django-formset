successchain =
  lhs:function _ '=>' _ rhs:successchain
  { return [lhs].concat(rhs) }
  / function

function =
  _ funcname:funcname '(' args:args ')' _
  { return { funcname: funcname, args: args } }
  / funcname:funcname '()'
  { return { funcname: funcname, args: [] } }
  / funcname:funcname
  { return { funcname: funcname, args: [] } }

funcname = funcname:$[a-z]i+

args =
  lhs:arg _ ',' _ rhs:args
  { return [lhs].concat(rhs) }
  / arg

arg =
  numarg:$([0-9]* '.' [0-9]+)
  { return parseFloat(numarg) }
  / numarg:$[0-9]+
  { return parseInt(numarg) }
  / '"' strarg:$[^"]* '"'
  { return strarg }
  / "'" strarg:$[^']* "'"
  { return strarg }

_ = [ \n]*
