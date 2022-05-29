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
	ln -s `pwd`/7z/7zdes ~/bin/7zdes
	ln -s `pwd`/7z/7zenc ~/bin/7zenc
	ln -s `pwd`/7z/gpg-sign-dir ~/bin/gpg-sign-dir
	ln -s `pwd`/7z/un7zd ~/bin/un7zd
	ln -s `pwd`/dictcn.py ~/bin/dictcn.py
	ln -s `pwd`/kp2pass ~/bin/kp2pass
	ln -s `pwd`/md2slide ~/bin/md2slide
	ln -s `pwd`/packpy ~/bin/packpy
	ln -s `pwd`/scandeb ~/bin/scandeb

clean-bin:
	rm -f ~/bin/7zdes
	rm -f ~/bin/7zenc
	rm -f ~/bin/gpg-sign-dir
	rm -f ~/bin/un7zd
	rm -f ~/bin/dictcn.py
	rm -f ~/bin/kp2pass
	rm -f ~/bin/md2slide
	rm -f ~/bin/packpy
	rm -f ~/bin/scandeb

### Makefile ends here
