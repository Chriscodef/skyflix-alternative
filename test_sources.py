import sys
import traceback
from netcine import HOSTS, ntc_search_catalog

queries = ["matrix", "avatar", "one piece"]

print('Testing hosts:', len(HOSTS))
for h in HOSTS:
    print('\n--- Host:', h)
    for q in queries:
        try:
            items = ntc_search_catalog(q, host=h)
            print(f' Query="{q}": {len(items)} results')
            if items:
                # print a compact sample
                it = items[0]
                print('  sample id:', it.get('id'))
                print('  sample title:', it.get('title'))
        except Exception as e:
            print(' Error querying host for', q)
            traceback.print_exc(file=sys.stdout)

print('\nDone')
