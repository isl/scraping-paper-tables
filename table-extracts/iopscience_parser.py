import re
import requests
import os
import astropy.io.ascii as ascii
import pandas

# Value used to replace undesired word occurences in datasets
EMPTY = '' 

# Find iopscience footnotes using regex 
# They are declared using '^', an empty space ' ' and a letter
def find_iopscience_footnotes(string):
    pattern = r'\^ [a-zA-Z]'
    matches = re.findall(pattern, string)
    return matches

# Search for footnote in IOPscience list of data and if found, add it to the json object the entry belongs to
def search_and_add_iopscience_footnote_to_obj(footnotes, data, json_obj, key_prefix):
    for footnote in footnotes:
        index = footnotes.index(footnote)
        for key in footnote.keys():
            actual_key= key.replace(' ','')
            if actual_key in data:
                json_obj['content'] = json_obj['content'].replace(f'{actual_key}', '')
                note = footnotes[index]
                note[key] = note[key].replace('Note. ', '')
                position = note[key].find(key)
                json_obj['note'] = note[key][position + 1 : len(note[key])]
                if 'headers' in key_prefix:
                    footnotes.remove(footnote)
    
# If notes include footnote value, remove notes
# because the information is present in table cells
def remove_footnote_from_notes(res, table_info):
    for note in table_info['notes']:
        if res in note:
           index = table_info['notes'].index(note)
           table_info['notes'][index] = ''

# Identify footnotes in iopscience journal and if they belong to a header,
# then remove them because they are only encountered once
# However, if they belong to rows containing table data they are likely encountered multiple
# times. Hence, we should keep this information
def identify_iopscience_footnotes(small_tag, footnotes, table_info):
    footnote_value = small_tag.get_text().replace('\n', '').replace('  ', '')
    result = find_iopscience_footnotes(footnote_value)
    for res in result:
        index = footnote_value.find(res)
        if result.index(res) == len(result) - 1:
         footnotes.append({res: footnote_value[index + 3: len(footnote_value)]})
        else:
            tmp = footnote_value.replace(res, '')
            next_index = tmp[index:len(tmp)].find(result[result.index(res) + 1])
            footnotes.append({res: footnote_value[index + 3: next_index]})
        # remove_footnote_from_notes(res, table_info)
    return footnotes

# Search for footnotes in iopscience journal
def search_iopscience_footnotes(soup_content, table_info):
    small_tags = soup_content.find_all('small')
    if small_tags == None:
        return
    
    footnotes = []
    for small_tag in small_tags:
        sup_tag = small_tag.find('sup')
        if sup_tag == None:
            continue
        sup_text = sup_tag.get_text().replace(' ', '').replace('\n', '')
        if sup_text == None:
            continue
        sup_value = sup_text.replace('^', '')
        if sup_value.isalpha():
            identify_iopscience_footnotes(small_tag, footnotes, table_info)
           
    return footnotes

# Search for table notes in iopscience journal
def search_iopscience_table_notes(soup_content):
    p_tags = soup_content.find_all('p')
    notes = []
    for p_tag in p_tags:
        small_tag = p_tag.find('small')
        if small_tag == None:
            continue
        strong_tag = small_tag.find('strong')
        if strong_tag == None:
            notes.append('')
            continue 
        notes.append(small_tag.get_text().replace('\n', '').replace('  ', ''))

    return notes

# Search for table captions in iopscience journal
def search_iopscience_table_captions(soup_content):
    p_tags = soup_content.find_all('p')
    captions = []
    for p_tag in p_tags:
        b_tag = p_tag.find('b')
        if b_tag == None:
            continue
        if 'Table' not in b_tag.get_text():
            continue
        p_text = p_tag.get_text().replace(b_tag.get_text(), '').replace('\xa0', EMPTY)
        captions.append(p_text)
    return captions

# Search for table info in iopscience journal, including notes and caption
def search_iopscience_table_info(soup_content):
    table_info = {}
    table_info['notes'] = search_iopscience_table_notes(soup_content)
    table_info['caption'] = search_iopscience_table_captions(soup_content)
    return table_info

# Write mrt file containing full versions for tables of iopscience journals
def write_mrt_file(directory_name, title, content):
    if not os.path.isdir(directory_name):
        os.mkdir(directory_name)
    path_to_mrt = os.path.join(directory_name, f'{title}.txt')
    file = open(path_to_mrt, 'wb')
    file.write(content)

# Convert mrt table data to json format
def convert_mrt_to_json(mrt_table):
    json_data = {}
    keys = []
    key_indexes = {}
    key_count = 0
    for key in mrt_table:
        key_count += 1
        keys.append({'content': key, 'header': 'true'})
        key_indexes[key] = key_count
        
    for key in keys:
        key_index = keys.index(key)
        keys[key_index] = {f'col{key_index + 1}': keys[key_index]}
    json_data['row1'] = keys

    data = []
    for key in mrt_table:
        values = [mrt_table[key]]
        col_index = key_indexes[key]  
        for value in values:
            value_index = values.index(value) 
            data.append({f'col{str(col_index)}':{'content' : values[value_index][value_index]}})
    json_data[f'row{value_index + 2}'] = data # + 1 for header row, + 1 for readability
    print(json_data)
    
# Extract mrt files containing full versions for tables of iopscience journals from their html content
# and write the data in bytes in local mrt files
def extract_iopscience_mrt_tables(soup_content, directory_name):
    web_refs = soup_content.find_all("a", {"class": "webref"})

    for web_ref in web_refs:
        if 'machine-readable' in web_ref.get_text():
            href = web_ref['href'] 
            mrt_html = requests.get(href)
            title = mrt_title(href)
            content = mrt_html.content
            # write_mrt_file(directory_name, title, content)
            title = 'ajacdd6ft1_mrt'
            path_to_mrt = os.path.join(directory_name, f'{title}.txt')
            print(f'Data for : {path_to_mrt}')
            data = ascii.read(path_to_mrt, format='mrt')
            df = data.to_pandas()
            table = df.to_dict()
            json_data = convert_mrt_to_json(table)
            
                  
# Extract title from href pointing to the mrt file
def mrt_title(href):
    revision_index = href.find('revision1/')
    txt_index = href.find('.txt')
    title = href[revision_index + len('revision1/') : txt_index]
    return title