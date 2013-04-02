#!/bin/sed -f
 
## Markdown2Dokuwiki - reformat Markdown to Dokuwiki
## Copyright (C) 2012 Matous J. Fialka, <http://mjf.cz/>
## Released under the terms of The MIT License

## TODO: many things yet...
 
# reformatovani nadpisu
s/^#####/==/
s/^####/===/
s/^###/====/
s/^##/=====/
s/^#/======/
 
# doplneni prave casti nadpisu
/^=/ {
	s/^\(=\+\)\(.*\)/\1\2 \1/
}
 
# reformatovani cislovanych seznamu
s/^[ \t]*[0-9]\.[ \t]\+\(.*\)/  - \1/