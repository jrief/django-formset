// PEG.js grammar to remove comments and newlines from JavaScript to be parsable by `Function()`.

JavaScript
  = parts:(Code / StringLiteral / SingleLineComment / MultiLineComment / RegexLiteral / WhiteSpace)* {
    return parts.join('').replace(/\s+/g, ' ').trim();
  }

Code
  = $(
    !("//" / "/*" / "\"" / "'" / "/" / WhiteSpace) .
  )+

StringLiteral
  = "\"" chars:DoubleStringCharacter* "\"" {
    return '"' + chars.join('') + '"';
  }
  / "'" chars:SingleStringCharacter* "'" {
    return "'" + chars.join('') + "'";
  }

DoubleStringCharacter
  = !("\"") char:SourceCharacter {
    return char;
  }

SingleStringCharacter
  = !("'") char:SourceCharacter {
    return char;
  }

RegexLiteral
  = "/" body:RegexBody "/" flags:[a-zA-Z]* {
    return '/' + body + '/' + flags.join('');
  }

RegexBody
  = $([^\n\r/\\] / "\\" .)+

SingleLineComment
  = "//" (!LineTerminator .)* LineTerminator? {
    return "\n";
  }

MultiLineComment
  = "/*" (!"*/" .)* "*/" {
    return "";
  }

WhiteSpace
  = [ \n\r\t\u2028\u2029]+ {
    return " ";
  }

SourceCharacter
  = .

LineTerminator
  = "\n"
  / "\r"
  / "\u2028"
  / "\u2029"
