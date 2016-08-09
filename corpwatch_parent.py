#! python3

import requests, re, bs4, json

# inputs

companies = [] #['taco bell', 'google inc', 'jollibee']
companies_txt = open('companies.txt' , 'r') 
for line in companies_txt:
	companies.append(line.strip())
companies_txt.close()

# static variables
query_URL = 'http://api.corpwatch.org/companies.json?company_name=$company'
cw2name_URL = 'http://api.corpwatch.org/companies/$cw_no/names.json'

# clean company names
companies_cleaned = { name:re.sub(' +', '+', re.sub('[^a-zA-Z0-9_ ]', '',name)) for name in companies}

result_dict = {}
for company_raw in companies:
	company = companies_cleaned[company_raw]
	# request page
	query_res = requests.get(re.sub('\$company',company,query_URL))
	try:
		query_res.raise_for_status()
	except Exception as exc:
		print('There was a problem parsing %s: %s' % (company_raw, exc))
		result_dict[company] = str(exc)
		continue

	# get most frequently occuring cw_no for top_parent_id from results
	parsed_query_res = json.loads(query_res.text)
	search_results = parsed_query_res['result']['companies']
	parent_cw_dict = {}
	for result in search_results:
		if search_results[result]['num_parents'] != "0":
			current_cw = search_results[result].get('top_parent_id')
			if current_cw in parent_cw_dict:
				parent_cw_dict[current_cw] += 1
			else:
				parent_cw_dict[current_cw] = 1

	# check if there is a parent
	if len(parent_cw_dict) == 0:
		result_dict[company] = "no parent found"
		continue
	else:
		v=list(parent_cw_dict.values())
		k=list(parent_cw_dict.keys())
		parent_cw = k[v.index(max(v))]

	# translate cw_no to an actual name
	cw2name_res = requests.get(re.sub('\$cw_no',parent_cw,cw2name_URL))
	try:
		cw2name_res.raise_for_status()
	except Exception as exc:
		print('There was a problem parsing %s: %s' % (company_raw, exc))
		result_dict[company] = str(exc)
		continue

	parsed_cw2name_res = json.loads(cw2name_res.text)
	cw2name_results = parsed_cw2name_res['result']['names']

	for name in cw2name_results:
		if name['source'] == 'filer_match_name':
			result_dict[company_raw] = name['company_name']
			break

# Export to txt
results_parents = open('results_parents.txt' , 'w') 
results_parents.write('Company|Parent\n')
for company in companies:
	results_parents.write(company +'|' + result_dict[company] +'\n')
results_parents.close()

print('Done!')