from password import get_password
import requests
from urllib.parse import urlencode

format = 'HTML'
    
# get token for nasa api
token=get_password('nasa_ads_token.txt')

# It is necessary that all of the arguments are provided and in a valid way
# For more info about what can be used as a query, use this guide: https://ui.adsabs.harvard.edu/help/search/

# Search ads journal by keyword
# Return value is what the user wants to retrive, e.g. title, bibcode, etc.
# whilst results is the number of results (up to 2000)
def search_ads_by_keyword(keyword,  return_value, results):
    query = {"q": "abs:" + keyword, "fl": return_value, "rows": results}
    encoded_query = urlencode(query)
    query_results = get_ads_query_results(encoded_query)
    bibcodes = extract_bibcode_from_results(query_results, results)
    urls = extract_urls_from_bibcodes(bibcodes, format)
    return urls


# Search ads journal by its abbreviation for ads
# which can be found here: https://adsabs.harvard.edu/abs_doc/journals1.html#
# Return value is what the user wants to retrive, e.g. title, bibcode, etc.
# whilst results is the number of results (up to 2000)
def search_ads_by_journal(journal_abbr, return_value, results):
    query = {"q": "bibstem:" + journal_abbr, "fl": return_value, "rows": results}
    encoded_query = urlencode(query)
    query_results = get_ads_query_results(encoded_query)
    bibcodes = extract_bibcode_from_results(query_results, results)
    print(bibcodes)
    urls = extract_urls_from_bibcodes(bibcodes, format)
    return urls


# Search ads journal by its abbreviation for ads in specific period of time
# which can be found here: https://adsabs.harvard.edu/abs_doc/journals1.html#
# Return value is what the user wants to retrive, e.g. title, bibcode, etc.
# whilst results is the number of results (up to 2000)
def search_ads_journal_by_period_of_time(journal_abbr, start_year, end_year, return_value, results):
    period_of_time = f'year:[{str(start_year)} TO {str(end_year)}]'
    query = {"q": "bibstem:"+ journal_abbr, "fq": period_of_time, "fl": return_value, "rows": results}
    encoded_query = urlencode(query)
    query_results = get_ads_query_results(encoded_query)
    bibcodes = extract_bibcode_from_results(query_results, results)
    urls = extract_urls_from_bibcodes(bibcodes, format)
    return urls  

# Execute ads query and return the results
def get_ads_query_results(encoded_query):
    query_results = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query), \
                        headers={'Authorization': 'Bearer ' + token})
    return query_results

# Extract bibcode from ads query json results
# Number of results is the amount of results expected from previous query 
def extract_bibcode_from_results(query_results, number_of_results):
    bibcodes = []
    json_results = query_results.json()
    json_response = json_results['response']
    json_docs = json_response['docs']
    # extract bibcode bibcode kv is in the form:
    # { "bibcode" : 'xxxxxxxxxx'}
    for i in range(number_of_results):
        bibcode_kv = str(json_docs[i])
        position = bibcode_kv.find(": '")
        final_bibcode = bibcode_kv[position + 3 : bibcode_kv.find("'}")]
        bibcode_kv.replace(final_bibcode,'')
        bibcodes.append(final_bibcode)
        i += 1
    return bibcodes


# Extract single ads url for given bibcode and format
# Note: format should either be "HTML" or "PDF" (Use capital letters in order for api to work)
def extract_url_from_bibcode(bibcode, format):
    generated_url = f'https://ui.adsabs.harvard.edu/link_gateway/{bibcode}/PUB_{format}'
    url_results = requests.get(generated_url)
    if url_results.url == generated_url:
        print('There is no available html for this journal.') 
        return None
    return url_results.url

# Extract ads urls for given bibcodes and format
# Bibcodes is a list with bibcodes to be extracted
# Note: format should either be "HTML" or "PDF" (Use capital letters in order for api to work)
def extract_urls_from_bibcodes(bibcodes, format):
    urls = []
    for bibcode in bibcodes:
        url = extract_url_from_bibcode(bibcode, format)
        urls.append(url)
    return urls

# A simple example of building an ads query to get url for an aanda journal published 
# between 2020 and 2023
def main():
    number_of_results = 1
    
    # print('Searching by keyword...')
    # keyword_results = search_ads_by_keyword('SNR', 'bibcode', number_of_results)
    # print(keyword_results)
    
    print('Searching by journal...')
    journal_results = search_ads_by_journal('A&A', 'bibcode', number_of_results)
    print(journal_results)
    
    # print('Searching by journal in specific period of time...')
    # journal_time_results = search_ads_journal_by_period_of_time('A&A', 2020, 2023, 'bibcode', number_of_results)
    # print(journal_time_results)
    
    
main()