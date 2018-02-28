import os
import re
import ntpath
import threading
import sys

if len(sys.argv) != 1:
    print("Need file path and report name!!!")
    sys.exit()

path = sys.argv[1]
report_path = sys.argv[2]

phantom_version = ["1.9.7", "2.1.1"]
result_list = []
include_php_file_list = []
pattern_phantom_js = re.compile(".*USE_NEW_PDF_FUNCTION.*")
pattern_pahntom_version = re.compile(".*USE_PHANTOMJS_LOCAL_VERSION.*")

result = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if os.path.splitext(f)[1] == '.php']

def get_include_file(include_php_file_list):
    """
        Prepare list include file tempate
    """

    def search_include_path(include_file_name, tempalte_list, temp_dict):
        """
            Search include file of root path from file name
        """
        for one_file in tempalte_list:
            if ntpath.basename(one_file) == include_file_name:
                temp_dict["include_path"] = one_file
                break

    for parse_code in result:
        with open(parse_code, "r") as php_include_file:
            match = re.findall(r".*include.*\/([A-Za-z1-9].*php)", php_include_file.read())
            if match:
                for include_file_name in match:
                    temp_dict = {"source": None, "include_name": None, "include_path": None}
                    search_worcker = threading.Thread(target=search_include_path, args=(include_file_name, result, temp_dict,))
                    search_worcker.start()
                    if search_worcker.isAlive():
                        search_worcker.join()
                    
                    temp_dict["source"] = parse_code
                    temp_dict["include_name"] = include_file_name                    

                    include_php_file_list.append(temp_dict)
                    del temp_dict
    

def is_match(file_resource, pattern):
    """
        Parse match file by regexp
    """
    result = False
    if pattern.findall(file_resource):
        result = True

    return result


collection_worcker = threading.Thread(target=get_include_file, args=(include_php_file_list, ))
collection_worcker.start()

report_file = open(report_path, "w")
count = {"phantom_1": 0, "phantom_2": 0}

threading.Thread(target=lambda:print("Begin...")).start()

for template in result:
    with open(template, "r") as temp_file:
        
        if collection_worcker.isAlive():
            collection_worcker.join()

        search_file = [file_path for file_path in include_php_file_list if file_path["include_path"] == template]
        if next(iter(search_file or []), None):
            continue
        
        result_struct = {"phantom_version": None, "template_path": None}
        file_source = temp_file.read()

        if is_match(file_source, pattern_phantom_js):
            if is_match(file_source, pattern_pahntom_version):
                result_struct["phantom_version"] = phantom_version[1]
                count["phantom_2"] += 1
            else:
                count["phantom_1"] += 1
                result_struct["phantom_version"] = phantom_version[0]

            result_struct["template_path"] = template
        else:
            if collection_worcker.isAlive():
                collection_worcker.join()
            search_file = [file_path for file_path in include_php_file_list if file_path["source"] == template]
            
            if len(search_file) == 0:
                continue
            
            for one_file in search_file:
                with open(one_file["include_path"]) as include_file:
                    file_resource = include_file.read()
                    if is_match(file_resource, pattern_phantom_js):
                        if is_match(file_resource, pattern_pahntom_version):
                            result_struct["phantom_version"] = phantom_version[1]
                            count["pahntom_2"] += 1
                        else:
                            result_struct["phantom_version"] = phantom_version[0]
                            count["phantom_1"] += 1
                    else:
                        continue

                    result_struct["template_path"] = one_file["source"]    

    if result_struct["template_path"] != None:
        result_list.append(result_struct)
        del result_struct


for line in sorted(result_list, key = lambda sort_string: sort_string['phantom_version']): 
    file_line = "Version: {}, Path: {}".format(line['phantom_version'], line['template_path'])
    report_file.write(file_line + "\n")

report_file.write("\n")
report_file.write("Total file: {} version: {}".format(count["phantom_1"], phantom_version[0]))
report_file.write("\n")
report_file.write("Total file: {} version: {}".format(count["phantom_2"], phantom_version[1]))

report_file.close()
threading.Thread(target=lambda:print("Finish!\nFile report in: {}".format(os.path.abspath(report_path)))).start()
