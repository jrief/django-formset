// Prepare code to be loaded by Javascript's Function
// Remove all newlines, reduce tabs to one space and eliminate line comments

FunctionCode
  = lines
  / last:last_line
  { return last.replaceAll(new RegExp('[\t]+', 'g'), ' '); }

lines
  = line:line remain:lines* last:last_line
  {
    if (last)
      remain.push(last);
    const result = remain.reduce((lines, l) => `${lines} ${l}`, line);
    return result.replaceAll(new RegExp('[\t]+', 'g'), ' ');
  }

line
  = c:line_comment terminator
  { return c; }
  / c:chars terminator
  { return c; }

last_line
  = line_comment
  / last:chars

line_comment
  = c:$(!start_comment !terminator .)* start_comment chars
  { return c; }

start_comment
  = "//"

chars
  = $(!terminator+ .)*

terminator
  = [\n\r\u2028\u2029]+
