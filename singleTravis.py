import travispy
from dotenv import load_dotenv
load_dotenv('.env')
import os
import csv
from bs4 import BeautifulSoup
#need to install beautiful soup
#pip install bs4
#pip install lxml

#start grading with "ipython -i -c "from singleTravis import *"
#then call gradeAssignments('lab1')


myToken2= os.getenv('TravisToken')
className=os.getenv('CLASS_NAME')
stuPath = os.getenv('StudentCSV')
projPath = os.getenv('projectCSV')

def loadStudents(path):
    students=[]
    with open(path,'r') as f:
        reader = csv.DictReader(f)
        for ln in reader:
            if len(ln['github_username'])>0:
                students.append(ln['github_username'])
    return students
    
def loadProjects(path):
    projects=[]
    with open(path,'r') as f:
        reader = csv.DictReader(f)
        for ln in reader:
            if len(ln['projectName'])>0:
                projects.append(ln['projectName'])
    return projects

def gradeAssignments(repoName, exportToCSV=True):
    scores=[]
    for stu in students:
        try:
            scores.append(getScore(stu,repoName))
        except Exception as e:
            print ("{0:20}: {1}".format(stu,"DNE"))

    if exportToCSV == True:
        with open(repoName + 'Scores.csv', 'w') as csvFile:
            csvWriter = csv.writer(csvFile, delimiter=',', lineterminator='\n')
            for stu, score in zip(students, scores):
                csvWriter.writerow([stu, score])



def getScore(student,project,classname=className):
    
    repoName=project
    #projectName=project[1]
    repos = travis.repos(owner_name=classname,search=repoName,member=student)
    if len(repos)==0:
       raise Exception("repo does not exist class:{2}, student:{0}, project:{1}".format(student, repoName, classname)) 
    else:    
        repo = repos[0]
        #TODO: find repo/job in a smarter way
        # only get the repo that happened before the due date.
        last_build = repo.last_build
        last_job = last_build.jobs[0]
        
        #must edit travispy file for this to not crash...
        #https://github.com/menegazzo/travispy/issues/58
        last_log =  last_job.log
        
        findString = ".Tests/TestResults/temp.trx"
        xmlstring = last_log.body[last_log.body.find(findString)+len(findString)+5:]
        score = parseLog(xmlstring)
    print("{0:20}: {1}".format(student,score))
    return score





def parseLog(xmlstring,debugOutput=False):
    totalScore=0
    y=BeautifulSoup(xmlstring,"lxml")
    if y.results is None: return 0
    for res in y.results.findAll('unittestresult'):
        scorestring=""
        
        if res.stdout is None:
            scorestring='FAIL'
        else:
            scorestring=res.stdout.contents[0]
            totalScore+=int(scorestring[scorestring.find(':')+1:])
        if debugOutput:print("{0:12} - {1}".format(scorestring,res['testname']))
    if debugOutput:print("totalScore = {0}".format(totalScore))   
    return totalScore
    
def listRepos(searchStr,clsName=className,student=None):
    repos = travis.repos(owner_name=clsName,search=searchStr,member=student)
    for r in repos:
        yield r.slug
       
       

students = loadStudents(stuPath)
projects = loadProjects(projPath)

travis = travispy.TravisPy(myToken2,travispy.travispy.PRIVATE)

