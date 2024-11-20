#!/usr/bin/env python3
import xml.etree.ElementTree as ET

xml_string = '<?xml version="1.0" encoding="utf-8"?><tt xmlns="http://www.w3.org/ns/ttml" xmlns:tts="http://www.w3.org/ns/ttml#styling" xmlns:ttp="http://www.w3.org/ns/ttml#parameter" xml:lang="" ttp:cellResolution="40 24"><head><styling><style xml:id="speakerStyle" tts:fontFamily="proportionalSansSerif" tts:fontSize="83.33%" tts:lineHeight="120.00%" tts:overflow="visible" tts:backgroundColor="transparent" tts:displayAlign="after" tts:color="white" tts:textOutline="black 2px" /><style xml:id="speakerStyleDoubleHeight" tts:fontFamily="proportionalSansSerif" tts:fontSize="166.66%" tts:lineHeight="83.33%" tts:overflow="visible" tts:backgroundColor="transparent" tts:displayAlign="after" tts:color="white" tts:textOutline="black 2px" /></styling><layout><region xml:id="speaker_1" tts:origin="8.33% 79.86%" tts:extent="83.33% 7.29%" tts:textAlign="center" style="speakerStyle" tts:zIndex="1" /><region xml:id="speaker_2" tts:origin="8.33% 87.15%" tts:extent="83.33% 7.29%" tts:textAlign="center" style="speakerStyle" tts:zIndex="1" /></layout></head><body><div><p begin="79091:02:32.649" end="79091:02:33.369" region="speaker_1"><span tts:backgroundColor="#101010"><span tts:color="#0CC6C5" tts:fontStyle="normal" tts:fontWeight="normal" tts:textDecoration="none">2 jours plus tard, il envoyait</span></span></p><p begin="79091:02:32.649" end="79091:02:33.369" region="speaker_2"><span tts:backgroundColor="#101010"><span tts:color="#0CC6C5" tts:fontStyle="normal" tts:fontWeight="normal" tts:textDecoration="none">son armÃ©e de l&apos;air en Syrie.</span></span></p></div></body></tt>'
# xml_string = '<?xml version="1.0" encoding="UTF-8"?><produit><Software ><item nom="ABC">Convertisseur PDF</item><prix>100</prix><version>1.2</version></Software><Hardware ><item nom="XYZ">Clavier</item><prix>20</prix><garantie>2 ans</garantie></Hardware></produit>'

root = ET.fromstring(xml_string)

for balise in root.iter():
    print("balise:", balise.tag, balise.attrib, balise.text)

for style in root.iter("{http://www.w3.org/ns/ttml}style"):
    print("style:", style.attrib)

for region in root.iter("{http://www.w3.org/ns/ttml}region"):
    print("region:", region.attrib, region.text)

for p in root.iter("{http://www.w3.org/ns/ttml}p"):
    print("p:", p.attrib, p.text)


for span in root.iter("{http://www.w3.org/ns/ttml}span"):
    print("span:", span.attrib, span.text)


# tree = ET.parse("in/ttml.xml")
# rootf = tree.getroot()

# print(rootf.attrib)
