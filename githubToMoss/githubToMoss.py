# Libs
import github # To install: "pip install PyGitHub"
import sys
import os
import csv
import mosspy # To install: "pip install mosspy"
from dotenv import load_dotenv # To install: "pip install -U python-dotenv"

# Get from .env
load_dotenv('GithubToMoss.env')
gitTok = os.getenv('GithubToken')
gitOrgName = os.getenv('GithubOrg')
mossUserId = os.getenv('MossUserID')
studentsCSV = os.getenv('StudentsCSV')
assignmentName = os.getenv('AssignmentName')
gitFileNamesString = os.getenv('Files')
gitFilePathsString = os.getenv('FilePaths')

# Get the Github organization
gitOrg = github.Github(gitTok).get_organization(gitOrgName)

# Pull the GitHub usernames from the file specified by the StudentsCSV env var
def getGithubUsernames(path):
    usernames=[]
    with open(path,'r') as fd:
        reader = csv.DictReader(fd)
        for line in reader:
            if len(line['github_username']) > 0:
                usernames.append(line['github_username'])
    return usernames

# Concat assignment name with usernames to get repo names
def getRepoNamesForAssignment(studentsCSV, assignmentName):
    usernames = getGithubUsernames(studentsCSV)
    repoNames = []
    for username in usernames:
        repoNames.append(assignmentName + username)
    return repoNames

# Creates a directory sets it as the current working directory
# Todo: Do something if the directory already exists
def createDirAndSetAsWorking(dirName):
    os.mkdir(dirName)
    currDir = os.getcwd()
    os.chdir(currDir + '/' + dirName)

# Get the file(s) of interest from each student and make
# local copies of them
def getFilesGithubAndMossCheck(gitOrg, mossUserId, studentsCSV, assignmentName, gitFileNamesString, gitFilePathsString):
    repoNames = getRepoNamesForAssignment(studentsCSV, assignmentName)

    # Separates the file names and file paths obtained from the env vars
    # into separate file names and paths per the ";" delimiter
    # Todo: Probably want to change it so path and filename are obtained from one env var
    gitFileNamesList = gitFileNamesString.split('; ')
    gitFilePathsList = gitFilePathsString.split('; ')

    # Create a diretcory to store all of the copied files
    createDirAndSetAsWorking(assignmentName + 'MossCheck')

    for gitFilePath, gitFileName in zip(gitFilePathsList, gitFileNamesList):
        # Create a diretcory to store all of the student files
        createDirAndSetAsWorking(assignmentName  + gitFileName)
        
        # Assemble the path with the file name
        if gitFilePath == '':
            gitFilePathAndName = gitFileName
        elif gitFilePath.endswith('/'):
            gitFilePathAndName = gitFilePath + gitFileName
        else:
            gitFilePathAndName = gitFilePath + '/' + gitFileName

        # Setup for a Moss check
        m = mosspy.Moss(mossUserId, "python")

        print('Getting ' + gitFilePathAndName + ' from each student...')
        sys.stdout.flush()
        for repoName in repoNames:
            try:
                repo = gitOrg.get_repo(repoName)

                try:
                    file_contents = repo.get_file_contents(gitFilePathAndName)
                    fd = open(repoName + '-' + gitFileName,'w')
                    fd.write(file_contents.decoded_content.decode('utf-8-sig'))
                    fd.close()

                except github.GithubException as e:
                    print('Error occurred getting ' + gitFilePathAndName + 'from ' + repoName + ':\n' + e)

            except github.GithubException as e:
                print('Error occurred while getting repository ' + repoName + ': ' + str(e.status))

        print('Done getting ' + gitFilePathAndName + '\n')

        # Add base file so Moss ignores all of the code that was originally
        # provided to the students
        #m.addBaseFile("submission/a01.py")

        # Add all the students files in the current directory to the Moss session
        print('Adding files to Moss session...')
        m.addFilesByWildcard(assignmentName + '*')

        # Send the files to be checked by Moss
        print('Sending files to Moss server... Awaiting results (this may take a while)... ')
        reportUrl = m.send()

        # Save the HTML report in the current folder and download the webpage
        m.saveWebPage(reportUrl, assignmentName + "Report.html")
        mosspy.download_report(reportUrl, "report/", connections=8, log_level=20) # log_level=10 for debug (20 to disable)

        # Leave the created directory
        os.chdir('..')

        print('Moss check complete!!!')
    
    # Go back to the active working directory before the fn was called
    os.chdir('..')

getFilesGithubAndMossCheck(gitOrg, mossUserId, studentsCSV, assignmentName, gitFileNamesString, gitFilePathsString)