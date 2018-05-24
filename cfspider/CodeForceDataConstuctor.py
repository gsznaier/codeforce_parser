#!/usr/bin/python

from bs4 import BeautifulSoup
from spiders import cf
from time import sleep
import subprocess
import requests
import scrapy
import json
import os

problem_set_discription_url = 'http://codeforces.com/problemset/problem/' # URL for problem discription
problem_set_sol_url = 'http://codeforces.com/problemset/submission/'      # URL for problem submissions

# Get the configs for the program.
with open('config.json') as config:
    configs = json.load(config)

if 'iter_lim' not in configs:
    iter_lim = -1 #effectively means get all possible submissions
else:
    iter_lim = configs['iter_lim']

if 'language' not in configs:
    lang = c.gcc
else:
    lang = configs['language']

print('Starting crawl for submissions ids')

# Uses scraper command to grab problem indices and tags, and submission ids
# result is stored in file data.json
subprocess.run(["scrapy", "crawl","cfSpider", "-o", "data.json", "-a", "lang="+lang])

print('Crawl finished')

with open('data.json') as data:
    jdata = json.load(data)

# All database files will be stored in here.
directory = 'CodeForceDataSet'

# Does the directory already exist?
if not os.path.exists(directory):
    os.makedirs(directory)

# Grab list of problems to create the dataset from
fid = open('ProblemSetList.txt','r')
problem_list = fid.readlines()
fid.close()

if problem_list is not None:
    # Remove newline characters
    for i in range(0,len(problem_list)):
        problem_list[i] = problem_list[i].strip('\n')


print('Starting crawl for submission solutions')

dataset = [] #will hold the completed dataset
submission_count = 0
for problem in jdata:

    prb = str(problem['contestId']) + problem['index']

    # check if any problems are left to check
    if  prb not in problem_list and len(problem_list) != 0:
        continue
    elif prb not in problem_list and len(problem_list) == 0:
        break;
    else:
        problem_list.remove(prb)
        print(problem)
        probID = problem.get('contestId')
        ids = problem.get('Submissions')

        problemSet = dict(problem)
        problemSet['Submissions'] = []
        problemSet['Solutions'] = []

        # New subdirectory for each problem set
        subdir = directory + '/' + problem['name'] + '_' + str(probID) + problem['index']

        #Does the directory already exist?
        if not os.path.exists(subdir):
            os.makedirs(subdir)

        #Download problem description page and parse it
        discription_url = problem_set_discription_url + str(probID) + '/' + problem['index']
        r = requests.get(discription_url)
        data = r.text
        soup = BeautifulSoup(data, 'html.parser')

        #Open file to store problem discription
        pr = open(subdir +'/ProblemDiscription.txt','w')

        title = '------------ ' + soup.title.string + ' ------------\n'
        pr.write(title)
        paragraph = soup.find_all('p')
        paragraph = [par.string for par in paragraph]

        # stores each line of the problem discription into the problemset discription file
        for par in paragraph:
            if par is None:
                continue

            pr.write(par + '\n')

        pr.close()

        # Get the code of each accepted submission for a given problem
        print('Getting submissions for problem: ' + problem['name'] + ' id: ' + str(probID) + problem['index'])
        pos = 0
        for id in ids:

            # Only get desired amount
            if iter_lim != -1:
                if pos >= iter_lim:
                    break

            subID = id
            url = str(probID) +'/'+ str(subID)
            sol_url = problem_set_sol_url + url;

            #Download page and parse it into xml
            r = requests.get(sol_url, allow_redirects=False)
            data = r.text
            soup = BeautifulSoup(data, 'html.parser')

            # Detect if codeforce refused a request
            if soup.pre is None:
                sleep(1)

            # retry until success or 100 request attemps have been made
            count = 0
            while soup.pre is None and count < 100:
                sleep(0.1)
                r = requests.get(sol_url, allow_redirects=False)
                data = r.text
                soup = BeautifulSoup(data, 'html.parser')
                count = count + 1

            # If unable to get the requested page with the code submission, skip data processing
            # this includes pages with incorrect urls. For example:
            # http://codeforces.com/problemset/submission/963/37672238 versus
            # http://codeforces.com/problemset/submission/964/37672238,
            # which have the same result
            if count == 100:
                continue

            #count the number of submissions actually added to the dataset
            print('url: ' + sol_url)
            print('probID: ' + str(probID) + problem['index'])
            print('submission ids: ' + str(ids))
            print('submission id: ' + str(id))
            print('submission_count: ' + str(submission_count))
            submission_count = submission_count + 1

            # Get html block that has runtime and memory size
            tr = soup.find_all('tr')

            # tr[0] has the html style configs and tr[1] has actual data
            td = tr[1].find_all('td')

            # Store scraped code into json data structure, td[5] has the runtime, and td[6]
            # has the memory size
            problemSet['Submissions'].append({subID:[soup.pre.contents, td[5].string, td[6].string]})

            # Store submission code into its own file
            fid = open(subdir + '/' + subID+'.c', 'w')
            fid.write(''.join(soup.pre.contents))
            fid.close()

            # Store statistics into its own file
            fid = open(subdir + '/' + subID+'_stats.c', 'w')
            fid.write(''.join([td[5].string, td[6].string]))
            fid.close()

            solutionSet = []
            solutions = soup.select('[style="margin-top:2em;font-size:0.8em;"]')
            for sol in solutions:
                temp = sol.select("[class~=caption]")[0]
                sid = temp.text.replace('\r','').replace('\n','').replace(' ','')
                solutionSet.append(sol.text)

            problemSet['Solutions'].append({subID:solutionSet})

            # Store submission code into its own file
            fid = open(subdir + '/' + subID+'_sol.txt', 'w')
            fid.write(''.join(solutionSet))
            fid.close()

            pos = pos + 1

        dataset.append(problemSet)
        print('Finished crawling problem: '+ problem['name'])
        print('Current submission count is: ' + str(submission_count))

print('Done')
print('Complete submission count is: ' + str(submission_count))

fid = open(directory + '/processed_data.json','w')
fid.write(json.dumps(dataset))
fid.close()

# Remove the temporary data file
#subprocess.run(["rm", "data.json"])
