import os
import re

CYPRESS_DIR = r"/home/gdaguet/src/tests-neadvr/cypress/cypress"
# iterate each file in a directory
testcase_id = []
cypress_testcase_list = []
for dir_path, dir_names, file_names in os.walk(CYPRESS_DIR):
    # res.extend(file_names)
    for file in file_names:
        if file.endswith("cy.js"):
            filepath = os.path.join(dir_path, file)
            # print(filepath)
            with open(filepath, encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    testcase = re.search(r"DVR-[0-9]+", line)
                    if testcase is not None:
                        cypress_testcase_list.append(testcase.group())
                        # print(m.group())
testcase_id.append(cypress_testcase_list)
print(f"Found {len(cypress_testcase_list)} test cases (cypress) to push to Xray")
