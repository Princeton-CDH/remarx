declare namespace tei="http://www.tei-c.org/ns/1.0";
declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method   "xml";
declare option output:indent   "yes";

(: first case: paragraphs that cross page boundaries but are contained by a single <p> :)

(: find all paragraphs anywhere in the input doc :)
let $continuing_p := (for $p in //tei:p
(: look for nested non-manuscript pb tag :)
let  $nested_pb := $p//tei:pb[not(@ed='manuscript')]
where $nested_pb
return <p>
{$p/@id}
<pb n="{$nested_pb/@n}"/>
</p>)

(: uncomment to see output with page numbers :)
(: return $continuing_p :)

(: second case: logical paragraphs that cross page boundaries but are interrupted
by footnotes and thus NOT contained by a single <p> :)

(: find all paragraphs that are followed immediately by a footnote :)
let $interrupted_p := (for $p in //tei:p
let $pb_num := $p/preceding::tei:pb[not(@ed='manuscript')][1]/@n
(: get normalized text content, but exclude footnote references and editorial content :)
let $p_text := normalize-space(string-join($p//text()[not(./parent::tei:add|./parent::tei:ref)]))
let $p_text_len := string-length($p_text)
where $p/following-sibling::*[1] = $p/following-sibling::tei:note[1]
and not(ends-with($p_text, ".") or ends-with($p_text, '.“'))
return <p>
{$p/@id}
<pb xmlns="" n="{$pb_num}"/>
{substring($p_text, $p_text_len - 50)}
</p>)


(: uncomment to see output with page numbers and last line of text:)
(: return $interrupted_p  :)


return <total>
	<paragraphs>{count(//tei:p)}</paragraphs>
	<continuing>{count($continuing_p)}</continuing>
	<interrupted>{count($interrupted_p)}</interrupted>
</total>
