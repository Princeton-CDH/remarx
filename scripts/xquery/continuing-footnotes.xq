declare namespace tei="http://www.tei-c.org/ns/1.0";
declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
declare option output:method   "xml";
declare option output:indent   "yes";

(: look for all notes anywhere in the doc :)
let $continuing_notes := (for $n in //tei:note
(: look for a preceding note with the same label :)
let $prev_n := $n/preceding::tei:note[tei:label = $n/tei:label][1]
where $prev_n
(: for debugging, output note with id, label, and previous note id/label :)
return <note xmlns="">
	{$n/@xml:id}
	{string($n/tei:label)}
	<prev xmlns="">
	{$prev_n/@xml:id}
	{string($prev_n/tei:label)}
	</prev>
</note>)

(: uncomment to see all output :)
(: return $continuing_notes :)

return <total>
	<footnotes>{count(//tei:note)}</footnotes>
	<continuing>{count($continuing_notes)}</continuing>
</total>
