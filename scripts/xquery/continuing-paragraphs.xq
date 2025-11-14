declare namespace tei="http://www.tei-c.org/ns/1.0";
declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method   "xml";
declare option output:indent   "yes";

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

(: TODO: these are the easy ones to find.
How to find logical continuation interrupted by a footnote that is not
marked up as a single paragraph? Maybe can infer based on end punctuation? :)

return <total>
	<paragraphs>{count(//tei:p)}</paragraphs>
	<continuing>{count($continuing_p)}</continuing>
</total>
