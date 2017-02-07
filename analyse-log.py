# -*- coding: UTF-8 -*-
__author__ = 'liown.xie'
import os
import sys
import re
import json
import logging
import mysql.connector
from datetime import datetime
from ctypes import cdll, c_char_p
from subprocess import PIPE, Popen
from multiprocessing import Queue, Process

PARAM_COUNT = 2
THREADS = 10
LOCAL_BRANCH = ""

fmt = '%(asctime)s %(levelname)-5s [pid:%(process)d] [%(threadName)s] [%(funcName)s:%(lineno)d] %(message)s'
logging.basicConfig(level=logging.DEBUG,
                     format=fmt,
                     filename='analyse.log')

def getMysqlConf(router=False):
    try:
        with open('conf.json') as f:
            data = json.load(f)
            if router:
                return data.get("ROUTER_CONF", {})
            return data.get("CONF", {})
    except IOError as e:
        logging.error("get conf failed.{}".format(e))
        sys.exit()

def getStatByMerge(mergeHash):
    # 通过merge的Hash值获取本次merge的统计信息
    logging.info("get stat by merge hash.")
    commit1, commit2 = mergeHash.split(" ")
    changeInfo = []
    try:
        statHandle = os.popen("git diff %s %s --stat" % (commit1, commit2))
        ret = statHandle.readlines()
        if len(ret) > 1:
            normal = re.findall(r"^(\d+) \D+, (\d+) \D+\(\+\), (\d+) \D+\(\-\)$", ret[-1].strip())
            insertions = re.findall(r"^(\d+) \D+, (\d+) \D+\(\+\)$", ret[-1].strip())
            deletions = re.findall(r"^(\d+) \D+, (\d+) \D+\(\-\)$", ret[-1].strip())
            if normal:
                changeInfo = [normal[0][0], normal[0][1], normal[0][2]]
            elif insertions:
                changeInfo = [insertions[0][0], insertions[0][1], "0"]
            elif deletions:
                changeInfo = [deletions[0][0], "0", deletions[0][1]]
    except Exception,e:
        logging.error("get stat failed!{}".format(e))
    return changeInfo


def getFileFunc(mergeHash):
    # 通过commit的hash值获取本次变更的文件与函数的对应关系
    logging.info("get funcName for merge request.")
    commit1, commit2 = mergeHash.split(" ")
    diffPattern = re.compile(r"^diff --git .+(\.c|\.cpp|\.hpp)$")
    filePattern = re.compile(r"^diff --git .+\.h$")
    linePattern = re.compile(r"^@@ -(\d+),(\d+) \+(\d+),(\d+) @@")
    mydll = cdll.LoadLibrary("GetFuncInfo.dll")
    diffHandle = Popen("git diff %s %s" % (commit1, commit2), stdout=PIPE).stdout
    fileName = ""
    fileFuncDict = {}
    # 找出文件与改变行号的对应关系
    for line in diffHandle:
        if diffPattern.match(line):
            fileName = line.split(" b/")[1].strip()
            if os.path.exists(fileName):
                fileFuncDict.setdefault(fileName, set())
        elif filePattern.match(line):
            _fileName = line.split(" b/")[1].strip()
            if os.path.exists(_fileName):
                fileFuncDict.setdefault(_fileName, [])
        lineList = linePattern.findall(line)
        if os.path.exists(fileName) and lineList:
            _start = int(lineList[0][2]) + 3
            _end = int(lineList[0][2]) + int(lineList[0][3]) - 2
            for i in range(_start, _end):
                filePath = c_char_p(fileName)
                version = c_char_p("217402")
                lineNum = c_char_p(str(i))
                ret = mydll.GetFuncName(filePath, version, lineNum)
                if c_char_p(ret).value and c_char_p(ret).value != "unkown":
                    fileFuncDict.setdefault(fileName, set()).add(c_char_p(ret).value)
            fileName = ""

    return fileFuncDict
    # fileLineDict.setdefault(fileName, []).append((int(lineList[0][2]), int(lineList[0][3])))

    # 根据行号查出对应的函数名称
    # for fName, lines in fileLineDict.items():
    # for line in lines:
    # for i in range(line[0] + 3, line[0] + line[1] - 2):
    # filePath = c_char_p(fName)
    # version = c_char_p("217402")
    #             lineNum = c_char_p(str(i))
    #             ret = mydll.GetFuncName(filePath, version, lineNum)
    #             if c_char_p(ret).value and c_char_p(ret).value != "unknown":
    #                 fileFuncDict.setdefault(fName, set()).add(c_char_p(ret).value)
    # return fileFuncDict


def getIssuesInfo():
    # 查询输入分支的日志，过滤出带issues的合并信息
    logging.info("BEGIN: get issues info by git log.")
    commitIssues = {}
    commitHash = ""
    descList = []
    ret = Popen('git log --grep="Issues info"', stdout=PIPE)
    for line in ret.stdout:
        if commitPattern.match(line):
            commitHash = line.split(" ")[1].strip()
            commitIssues.setdefault(commitHash, {})
        elif commitHash and mergePattern.match(line):
            mergeHash = line.split(":")[1].strip()
            commitIssues.setdefault(commitHash, {})["Merge"] = mergeHash
        elif commitHash and authorPattern.match(line):
            _author = line.split(":")[1].strip().split("<")[0].strip()
            commitIssues.setdefault(commitHash, {})["Author"] = _author
        elif commitHash and datePattern.match(line):
            _date = line.split("   ")[1].strip()
            commitIssues.setdefault(commitHash, {})["Date"] = _date
        elif commitHash and titlePattern.match(line):
            title = line.split(":")[1].strip()
            commitIssues.setdefault(commitHash, {})["Title"] = title
        elif commitHash and descPattern.match(line):
            desc = line.split(":")[1]
            descList.append(desc)
        elif commitHash and descList and issuesPattern.match(line):
            commitIssues.setdefault(commitHash, {})["Desc"] = "".join(descList).strip()
            commitHash = ""
            descList = []
        elif commitHash and descList:
            descList.append(line)
    logging.info("END: get issues info by git log.")
    return commitIssues


def getDTSAndRallyInfo():
    # 过滤出DTS and Rally相关信息
    commitIssues = {}
    commitHash = ""
    descList = []
    logging.info("BEGIN: get DTS and Rally info by git log.")
    ret = Popen('git log --grep="DTS and Rally info"', stdout=PIPE)
    for line in ret.stdout:
        if commitPattern.match(line):
            commitHash = line.split(" ")[1].strip()
            commitIssues.setdefault(commitHash, {})
        elif commitHash and mergePattern.match(line):
            mergeHash = line.split(":")[1].strip()
            commitIssues.setdefault(commitHash, {})["Merge"] = mergeHash
        elif commitHash and authorPattern.match(line):
            _author = line.split(":")[1].strip().split("<")[0].strip()
            commitIssues.setdefault(commitHash, {})["Author"] = _author
        elif commitHash and datePattern.match(line):
            _date = line.split("   ")[1].strip()
            commitIssues.setdefault(commitHash, {})["Date"] = _date
        elif commitHash and tracePattern.match(line):
            title = line.split(":")[1].strip()
            commitIssues.setdefault(commitHash, {})["TraceNo"] = title
        elif commitHash and createPattern.match(line):
            creator = line.split(":")[1].strip()
            commitIssues.setdefault(commitHash, {})["Creator"] = creator
        elif commitHash and _descPattern.match(line):
            desc = line.split(":")[1]
            descList.append(desc)
        elif commitHash and descList and smrPattern.match(line):
            commitIssues.setdefault(commitHash, {})["Desc"] = "".join(descList).strip()
            commitHash = ""
            descList = []
        elif commitHash and descList:
            descList.append(line)
    logging.info("END: get DTS and Rally info by git log.")
    return commitIssues


def dataIntoDB(merge, dataList):
    # 将数据插入到数据库中
    logging.info("data to DB.")
    try:
        cnn = mysql.connector.connect(**getMysqlConf())
        cour = cnn.cursor()
        sql = """INSERT IGNORE INTO merge_info (product_version,branch,merge_hash,statistics,merge_ower,merge_time,title,trance_num,creator,description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        cour.execute(sql, merge)
        cour.execute("SELECT LAST_INSERT_ID()")
        ret = cour.fetchone()
        for value in dataList:
            modi_sql = "INSERT IGNORE INTO modi_info (merge_id,file_url,modi_func,stat) VALUES (%s,%s,%s,%s)"
            vm = (ret[0],value[0],value[1],value[2])
            cour.execute(modi_sql,vm)
        cnn.commit()
    except mysql.connector.Error as e:
        logging.error('connect fails!{}'.format(e))
    except Exception as e:
        logging.error("DML failed!{}".format(e))
    finally:
        cour.close()
        cnn.close()


def gitPath():
    try:
        p = Popen("gitPath.bat", stdout=PIPE, shell=True)
        gp = p.stdout.readlines()[0].strip() + "bin\\sh.exe"
        sh_path = gp.split("Found Git at ")[1]
        return sh_path
    except IndexError:
        logging.error("Can't find git path")
        sys.exit()


def doPrepare():
    # 解析log日志前的准备工作
    # 参数判断，入参为分支名称
    param = sys.argv[1:]
    if len(param) != PARAM_COUNT:
        print "Usage:"
        print "\tpython getFeatureByCode.py git_url git_branch"
        sys.exit()
    # 根据GIT库路径获取版本信息
    ret = getVersion(param[0])
    if not ret:
        print "product version not found"
        logging.error("product version not found")
        sys.exit()
    # 将git的安装目录添加到系统环境变量中
    sh_path = gitPath()
    # 保存当前分支名称，程序结束时还原分支。
    global LOCAL_BRANCH
    branchHandle = os.popen("git branch")
    for branch in branchHandle:
        if re.search(r"\* ", branch):
            LOCAL_BRANCH = branch.split(" ")[1].strip()
            break
    # 更新远程分支列表
    child = Popen('"%s" --login -i' % sh_path, stdin=PIPE)
    child.communicate('git fetch')
    if child.returncode != 0:
        print "Fetch branch failed."
        sys.exit()
    remoteBranch = os.popen("git branch -r")
    inputBranch = ""
    for branch in remoteBranch.readlines():
        if branch.strip() == "origin/%s" % param[1]:
            inputBranch = "remotes/origin/%s" % param[1]
            break
    if not inputBranch:
        print "Can't find the branch:%s" % param[1]
        logging.error("Can't find the branch:%s" % param[1])
        sys.exit()
    # 切换分支
    retCode = os.system("git checkout -f %s" % inputBranch)
    if retCode != 0:
         print "Checkout branch failed."
         sys.exit()
    return ret[0], param[1]


def getVersion(url):
    # 根据GIT库路径获取版本信息
    ret = []
    try:
        cnn = mysql.connector.connect(**getMysqlConf(router=True))
        cour = cnn.cursor()
        sql = """SELECT product_version FROM  version_info WHERE repo_url='%s'""" % url
        cour.execute(sql)
        ret = cour.fetchone()
    except mysql.connector.Error as e:
        print('connect fails!{}'.format(e))
    finally:
        cour.close()
        cnn.close()
    return ret


def restoreBranch():
    # 还原本地分支
    global LOCAL_BRANCH
    if LOCAL_BRANCH:
        resCode = os.system("git checkout -f %s" % LOCAL_BRANCH)
        if resCode != 0:
            print "Restore the branch failed."


def deal_with_info(version, branch, queue):
    # 遍历每个变更节点，获取节点间变更文件和函数的对应关系
    while 1:
        if queue.empty():
            logging.info('queue is empty, exit the process.')
            break
        item = queue.get()
        merge = item.get("Merge")
        if merge:
            changeList = getStatByMerge(merge)
            fileFuncDict = getFileFunc(merge)
            merge_info, dataList = getDataSeq(version, branch, item, changeList, fileFuncDict)
            dataIntoDB(merge_info, dataList)


def Rdeal_with_info(commitIssues):
    # 遍历每个变更节点，获取节点间变更文件和函数的对应关系
    for item in commitIssues:
        merge = commitIssues[item].get("Merge")
        if merge:
            changeList = getStatByMerge(merge)
            fileFuncDict = getFileFunc(merge)
            merge_info, dataList = getDataSeq(commitIssues[item], changeList, fileFuncDict)
            dataIntoDB(merge_info, dataList)


def getDataSeq(version, branch, commitDict, changeList, fileFuncDict):
    # 数据处理，方便插入数据库
    logging.info("deal with merge info for database.")
    _merge_hash = commitDict.get("Merge", "")
    _author = commitDict.get("Author", "")
    date = commitDict.get("Date", "")
    _date = datetime.strptime(date[:-6], "%a %b %d %H:%M:%S %Y")
    _trace = commitDict.get("TraceNo", "")
    _creator = commitDict.get("Creator", "")
    _title = commitDict.get("Title", "")
    _desc = commitDict.get("Desc", "")
    _stat = ",".join(changeList)
    merge_info = (version, branch, _merge_hash, _stat, _author, _date, _title, _trace, _creator, _desc)
    dataList = []
    for fp in fileFuncDict:
        changeStat = mergerFileStat(_merge_hash, fp)
        temp = (fp, ','.join(fileFuncDict.get(fp, [])), ','.join(changeStat))
        dataList.append(temp)
    return merge_info, dataList

def mergerFileStat(mergeHash, filePath):
    commit1, commit2 = mergeHash.split(" ")
    statHandle = os.popen('git diff %s %s --stat "%s"' % (commit1, commit2, filePath))
    changeStat = []
    ret = statHandle.readlines()
    if len(ret) > 1:
        normal = re.findall(r"^(\d+) \D+, (\d+) \D+\(\+\), (\d+) \D+\(\-\)$", ret[-1].strip())
        insertions = re.findall(r"^(\d+) \D+, (\d+) \D+\(\+\)$", ret[-1].strip())
        deletions = re.findall(r"^(\d+) \D+, (\d+) \D+\(\-\)$", ret[-1].strip())
        if normal:
            changeStat = [normal[0][0], normal[0][1], normal[0][2]]
        elif insertions:
            changeStat = [insertions[0][0], insertions[0][1], "0"]
        elif deletions:
            changeStat = [deletions[0][0], "0", deletions[0][1]]
    return changeStat

def putDataToQ(queue, merge_info):
    logging.info("put data to queue.")
    for m in merge_info:
        queue.put(merge_info[m])

def MyThread(version, branch, queue):
    p_list = []
    for i in range(THREADS):
        t = Process(target=deal_with_info, args=(version, branch, queue))
        t.start()
        p_list.append(t)
    for p in p_list:
        p.join()
    logging.info("All data processing is complete.")


if __name__ == "__main__":
    queue = Queue()
    version, branch = doPrepare()
    commitPattern = re.compile(r"^commit ")
    mergePattern = re.compile(r"^Merge: ")
    authorPattern = re.compile(r"^Author: ")
    datePattern = re.compile(r"^Date: ")
    titlePattern = re.compile(r"^\s{4}Title :")
    descPattern = re.compile(r"^\s{4}Description :")
    issuesPattern = re.compile(r"^\s{4}Issue url :")
    tracePattern = re.compile(r"^\s{4}TraceNo\.:")
    createPattern = re.compile(r"^\s{4}Author:")
    smrPattern = re.compile(r"^\s{4}See merge request")
    _descPattern = re.compile(r"^\s{4}Description:")
    # 查询输入分支的日志，过滤出带issues的合并信息
    #commitIssues = getIssuesInfo()
    # 过滤出DTS and Rally相关信息
    dtsAndRallyInfo = getDTSAndRallyInfo()
    #commitIssues.update(dtsAndRallyInfo)
    # Rdeal_with_info(commitIssues)
    putDataToQ(queue, dtsAndRallyInfo)
    MyThread(version, branch, queue)
    restoreBranch()
