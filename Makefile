### Makefile --- 

## Author: shell@dskvmdeb.lan
## Version: $Id: Makefile,v 0.0 2017/04/20 15:45:58 shell Exp $
## Keywords: 
## X-URL: 

install: install-bash install-bin

clean: clean-bash clean-bin

install-bash:
	ln -s `pwd`/bash_aliases ~/.bash_aliases
	ln -s `pwd`/bash_funces ~/.bash_funces

clean-bash:
	rm -f ~/.bash_aliases
	rm -f ~/.bash_funces

install-bin:
	ln -s `pwd`/7zptocmx ~/bin/7zptocmx
	ln -s `pwd`/anki.py ~/bin/anki.py
	ln -s `pwd`/bm.py ~/bin/bm.py
	ln -s `pwd`/dictcn.py ~/bin/dictcn.py
	ln -s `pwd`/md2slide ~/bin/md2slide
	ln -s `pwd`/packpy ~/bin/packpy
	ln -s `pwd`/scandeb ~/bin/scandeb

clean-bin:
	rm -f ~/bin/7zptocmx
	rm -f ~/bin/anki.py
	rm -f ~/bin/bm.py
	rm -f ~/bin/dictcn.py
	rm -f ~/bin/md2slide
	rm -f ~/bin/packpy
	rm -f ~/bin/scandeb

### Makefile ends here
