#!/usr/bin/python

from bs4 import BeautifulSoup
from spiders import cf
from time import sleep
import subprocess
import requests
import argparse
import scrapy
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument('-crawl',
                    help='if yes, crawl through codeforce for submission ids, if no, use already created jsoin file',
                    action='store',
                    default='no')
args = parser.parse_args()

problem_set_discription_url = 'http://codeforces.com/problemset/problem/' # URL for problem discription
problem_set_sol_url = 'http://codeforces.com/problemset/submission/'      # URL for problem submissions

# Get the configs for the program.
with open('config.json') as config:
    configs = json.load(config)

if 'iter_lim' not in configs:
    iter_lim = -1 #Get all possible submissions
else:
    iter_lim = configs['iter_lim']

if 'sol_lim' not in configs:
    sol_lim = -1 #Get all possible problem tests
else:
    sol_lim = configs['sol_lim']

if 'language' not in configs:
    lang = c.gcc
else:
    lang = configs['language']

print('Starting crawl for submissions ids')

# Uses scraper command to grab problem indices and tags, and submission ids
# result is stored in file data.json
if args.crawl.lower() == 'yes':
    # Attempt to remove any old data file
    try:
        subprocess.run(["rm", "data.json"])

    # If file does not exist, ignore error and simply start crawling
    except subprocess.CalledProcessError as e:
        pass

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
        probID = problem.get('contestId')
        ids = problem.get('Submissions')

        # Skip problems with no useful submissions
        if ids == [] or len(ids) < 20:
            print('Problem ' + str(problem['contestId']) + problem['index'] + ' has no useful submissions.')
            print('Now moving on to the next problem.')
            continue

        problemSet = dict(problem)
        problemSet['Submissions'] = []
        problemSet['Solutions'] = []

        # New subdirectory for each problem set
        probdir = directory + '/' + str(probID) + problem['index']
        subdir = probdir + '/submissions'
        statsdir = probdir + '/stats'
        testdir = probdir + '/tests'
        soldir = probdir + '/solutions'

        #Does the directory already exist?
        if not os.path.exists(probdir):
            os.makedirs(probdir)

        #Does the directory already exist?
        if not os.path.exists(subdir):
            os.makedirs(subdir)

         #Does the directory already exist?
        if not os.path.exists(statsdir):
            os.makedirs(statsdir)

        #Does the directory already exist?
        if not os.path.exists(testdir):
            os.makedirs(testdir)
        #Does the directory already exist?
        if not os.path.exists(soldir):
            os.makedirs(soldir)

        #Download problem description page and parse it
        discription_url = problem_set_discription_url + str(probID) + '/' + problem['index']
        r = requests.get(discription_url)
        data = r.text
        soup = BeautifulSoup(data, 'html.parser')

        #Open file to store problem discription
        pr = open(probdir +'/ProblemDiscription.txt','w+')

        title = '------------ ' + soup.title.string + ' ------------\n'
        subtitle= '------------ ' + problem['name'] + ' ------------\n'
        pr.write(title)
        pr.write(subtitle)
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

            # Download page and parse it into xml
            r = requests.get(sol_url, allow_redirects=False)
            data = r.text
            soup = BeautifulSoup(data, 'html.parser')

            # Only create a solution set if it was the first time.
            if not os.path.isfile(probdir + '/' + str(probID) + problem['index'] + '.txt'):

                # Get solution set
                solutions = soup.select('[style="margin-top:2em;font-size:0.8em;"]')
                solutionSet = []

                # get each solution object
                sol_count = 0
                for sol in solutions:

                    # Only get the desired number of solution tests
                    if sol_count >= sol_lim:
                        break
                    else:
                        sol_count = sol_count + 1

                    test_number = sol.select("[class~=caption]")[0]
                    test_number = test_number.text.replace('\r','').replace('\n','').replace(' ','')
                    stats = {}
                    tag = ''
                    for io in sol.select("[class~=file]"):
                        if 'Input' in io.div.text:
                            fid = open(testdir + '/' + test_number + '.txt', 'w+')
                            fid.write(io.pre.text)
                            fid.close()
                            stats['Input'] = io.pre.text.replace('\r','+').replace('\n','')
                        if 'Jury\'s answer' in io.div.text:
                            fid = open(soldir + '/' + test_number + '.txt', 'w+')
                            fid.write(io.pre.text)
                            fid.close()
                            stats['Output'] = io.pre.text

                    solutionSet.append({test_number:stats})

                problemSet['Solutions'] = solutionSet

            # Detect if codeforce refused a request
            if soup.pre is None:
                sleep(1)

            # retry until success or 100 request attemps have been made
            count = 0
            while soup.pre is None and count < 50:
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
            if count == 50:
                print('unable to get submission... moving on to next one!')
                continue

            #count the number of submissions actually added to the dataset
            submission_count = submission_count + 1

            # Get html block that has runtime and memory size
            tr = soup.find_all('tr')

            # tr[0] has the html style configs and tr[1] has actual data
            td = tr[1].find_all('td')

            # Store scraped code into json data structure, td[5] has the runtime, and td[6]
            # has the memory size
            problemSet['Submissions'].append({subID:{'Code':soup.pre.contents, 'Time':td[5].string, 'Size':td[6].string}})

            print('storing submission: ' + str(subID))
            # Store submission code into its own file
            fid = open(subdir + '/' + subID+'.c', 'w+')
            fid.write(''.join(soup.pre.contents))
            fid.close()
            print('submission ' + str(subID) + ' has been stored!')

            # Store statistics into its own file
            fid = open(statsdir + '/' + subID+'.txt', 'w+')
            fid.write(''.join([td[5].string, td[6].string]))
            fid.close()

            pos = pos + 1

        if os.listdir(subdir) == []:
            print('directory was empty... now removing to mantain neatness')
            subprocess.run(["rm", "-R", probdir])

        if len(problemSet['Submissions']) >= 20:
            dataset.append(problemSet)
            print('Finished crawling problem: '+ problem['name'])
            print('Current submission count is: ' + str(submission_count))
        else:
            print(str(probID) + problem['index'])
            print('Not enough submissions found... removing problem from dataset')
            subprocess.run(["rm", "-R", probdir])

print('Done')
print('Complete submission count is: ' + str(submission_count))

fid = open(directory + '/processed_data.json','w+')
fid.write(json.dumps(dataset))
fid.close()


