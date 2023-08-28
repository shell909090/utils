### Makefile --- 

## Author: shell@dsk
## Version: $Id: Makefile,v 0.0 2019/09/02 17:53:14 shell Exp $
## Keywords: 
## X-URL: 

clean:
	rm -f routes.txt aws-cn.txt routes.list.gz routes.sh

define PYTHON_APNIC_ROUTE1
import sys, math
for line in sys.stdin:
  i = line.strip().split('|')
  print(f'{i[3]}/{32-math.floor(math.log2(int(i[4])))}')
endef

export PYTHON_APNIC_ROUTE1
apnic:
	curl -s 'https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest' | grep -i 'apnic|cn|ipv4' | python3 -c "$$PYTHON_APNIC_ROUTE1" > routes.txt

chnroutes2:
	curl -s 'https://raw.githubusercontent.com/misakaio/chnroutes2/master/chnroutes.txt' | grep -v '^#' > routes.txt

aws-cn.txt:
	curl -s 'https://ip-ranges.amazonaws.com/ip-ranges.json' | jq -r '.prefixes[] | select(.region | startswith("cn-north")) | .ip_prefix' | python3 ip-merger.py > aws-cn.txt

add-aws-cn: aws-cn.txt
	cat routes.txt aws-cn.txt | python3 ip-merger.py > route1.txt
	mv route1.txt routes.txt

define ROUTES_LIST_EXTRA
127.0.0.0/8
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
endef

export ROUTES_LIST_EXTRA
routes.list.gz: routes.txt
	echo "$$ROUTES_LIST_EXTRA" > extra_routes.list
	cat routes.txt extra_routes.list | python3 ip-merger.py | gzip > routes.list.gz
	rm extra_routes.list

define PYTHON_ROUTES_SH
import sys
print('''#!/bin/bash
''')
for line in sys.stdin:
  print(f'ip route add {line.strip()} table fout dev ppp0')
endef

export PYTHON_ROUTES_SH
routes.sh:
	cat routes.txt | python3 ip-merger.py | python3 -c "$$PYTHON_ROUTES_SH" > routes.sh

### Makefile ends here
