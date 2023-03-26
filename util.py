#!python3
# -*- coding: utf-8 -*-
# author: yinkaisheng@foxmail.com
import os
import io
import sys
import time
import json
import ctypes
import pickle
import shutil
# import socket
import zipfile
import datetime
from typing import Any, Callable, Deque, Dict, Iterator, List, Tuple


IsPy38OrHigher = sys.version_info[:2] >= (3, 8)
_SelfFileName = os.path.split(__file__)[1]


def printx(*values, sep: str = ' ', end: str = None, flush: bool = False, caller: bool = True) -> None:
    t = datetime.datetime.now()
    if caller:
        frameCount = 1
        while True:
            frame = sys._getframe(frameCount)
            scriptFileName = os.path.basename(frame.f_code.co_filename)
            if scriptFileName != _SelfFileName:
                break
            frameCount += 1
        selfObj = frame.f_locals.get('self', None)
        if selfObj:
            timestr = f'{t.year}-{t.month:02}-{t.day:02} {t.hour:02}:{t.minute:02}:{t.second:02}.{t.microsecond // 1000:03} L{frame.f_lineno} {selfObj.__class__.__name__}.{frame.f_code.co_name}:'
        else:
            timestr = f'{t.year}-{t.month:02}-{t.day:02} {t.hour:02}:{t.minute:02}:{t.second:02}.{t.microsecond // 1000:03} L{frame.f_lineno} {frame.f_code.co_name}:'
    else:
        timestr = f'{t.year}-{t.month:02}-{t.day:02} {t.hour:02}:{t.minute:02}:{t.second:02}.{t.microsecond // 1000:03}:'
    print(timestr, *values, sep=sep, end=end)
    if flush and sys.stdout:
        sys.stdout.flush()


def millisecondsSinceEpoch() -> int:
    return int(time.time() * 1000)


def dateTimeFromMsEpoch(millisecondsSinceEpoch: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(millisecondsSinceEpoch / 1000)


def setConsoleTitle(title: str) -> None:
    # need colorama.init
    if sys.stdout:
        sys.stdout.write(f'\x1b]2;{title}\x07')


def getStrBetween(src: str, left: str, right: str = None, start: int = 0, end: int = None) -> Tuple[str, int]:
    '''return tuple (str, index), index is -1 if not found'''
    if left:
        s1start = src.find(left, start, end)
        if s1start >= 0:
            s1end = s1start + len(left)
            if right:
                s2start = src.find(right, s1end, end)
                if s2start >= 0:
                    return src[s1end:s2start], s1end
                else:
                    return '', -1
            else:
                return src[s1end:], s1end   #may be '', s1end
        else:
            return '', -1
    else:
        if right:
            s2start = src.find(right, end)
            if s2start >= 0:
                return src[:s2start], 0     #may be '', 0
            else:
                return '', -1
        else:
            return '', -1


def getFileText(path: str, encoding: str = 'utf-8', checkExist: bool = True) -> str:
    if checkExist and not os.path.exists(path):
        return ''
    with open(path, 'rt', encoding=encoding, errors='ignore') as fin:
        return fin.read()


def writeTextFile(path: str, text: str, encoding: str = 'utf-8'):
    with open(path, 'wt', encoding=encoding, errors='ignore') as fout:
        fout.write(text)


def appendTextFile(path: str, text: str, encoding: str = 'utf-8'):
    with open(path, 'a+', encoding=encoding, errors='ignore') as fout:
        fout.write(text)


def getFileBytes(path: str, checkExist: bool = True) -> bytes:
    if checkExist and not os.path.exists(path):
        return None
    with open(path, 'rb') as fin:
        return fin.read()


def writeBinaryFile(path: str, data: bytes):
    with open(path, 'wb') as fout:
        fout.write(data)


def appendBinaryFile(path: str, data: bytes):
    with open(path, 'ab+') as fout:
        fout.write(data)


def pickleLoad(path: str) -> Any:
    if os.path.exists(path):
        with open(path, 'rb') as fin:
            return pickle.load(fin)


def pickleDump(obj: Any, path: str):
    with open(path, 'wb') as fout:
        pickle.dump(obj, fout)


def jsonFromFile(path: str, encoding: str = 'utf-8') -> Dict:
    content = getFileText(path, encoding)
    return json.loads(content) if content else {}


def jsonToFile(jsonObj: Dict, path: str):
    jsonStr = json.dumps(jsonObj, indent=4, ensure_ascii=False, sort_keys=False)
    writeTextFile(path, jsonStr, encoding='utf-8')


TreeNode = Any


def walkTree(root, getChildren: Callable[[TreeNode], List[TreeNode]] = None,
             getFirstChild: Callable[[TreeNode], TreeNode] = None, getNextSibling: Callable[[TreeNode], TreeNode] = None,
             yieldCondition: Callable[[TreeNode, int], bool] = None, includeRoot: bool = False, maxDepth: int = 0xFFFFFFFF) -> Iterator:
    """
    Walk a tree not using recursive algorithm.
    root: a tree node.
    getChildren: Callable[[TreeNode], List[TreeNode]], function(treeNode: TreeNode) -> List[TreeNode] or Deque[TreeNode].
    getNextSibling: Callable[[TreeNode], TreeNode], function(treeNode: TreeNode) -> TreeNode.
    getNextSibling: Callable[[TreeNode], TreeNode], function(treeNode: TreeNode) -> TreeNode.
    yieldCondition: Callable[[TreeNode, int], bool], function(treeNode: TreeNode, depth: int) -> bool.
    includeRoot: bool, if True yield root first.
    maxDepth: int, enum depth.

    If getChildren is valid, ignore getFirstChild and getNextSibling,
        yield 3 items tuple: (treeNode, depth, remain children count in current depth).
    If getChildren is not valid, using getFirstChild and getNextSibling,
        yield 2 items tuple: (treeNode, depth).
    If yieldCondition is not None, only yield tree nodes that yieldCondition(treeNode: TreeNode, depth: int)->bool returns True.

    For example:
    def GetDirChildren(dir_):
        if os.path.isdir(dir_):
            return [os.path.join(dir_, it) for it in os.listdir(dir_)]
    for it, depth, leftCount in WalkTree('D:\\', getChildren= GetDirChildren):
        print(it, depth, leftCount)
    """
    if maxDepth <= 0:
        return
    depth = 0
    if getChildren:
        if includeRoot:
            if not yieldCondition or yieldCondition(root, 0):
                yield root, 0, 0
        children = getChildren(root)
        childList = [children]
        while depth >= 0:  # or while childList:
            lastItems = childList[-1]
            if lastItems:
                if not yieldCondition or yieldCondition(lastItems[0], depth + 1):
                    yield lastItems[0], depth + 1, len(lastItems) - 1
                if depth + 1 < maxDepth:
                    children = getChildren(lastItems[0])
                    if children:
                        depth += 1
                        childList.append(children)
                del lastItems[0]
            else:
                del childList[depth]
                depth -= 1
    elif getFirstChild and getNextSibling:
        if includeRoot:
            if not yieldCondition or yieldCondition(root, 0):
                yield root, 0
        child = getFirstChild(root)
        childList = [child]
        while depth >= 0:  # or while childList:
            lastItem = childList[-1]
            if lastItem:
                if not yieldCondition or yieldCondition(lastItem, depth + 1):
                    yield lastItem, depth + 1
                child = getNextSibling(lastItem)
                childList[depth] = child
                if depth + 1 < maxDepth:
                    child = getFirstChild(lastItem)
                    if child:
                        depth += 1
                        childList.append(child)
            else:
                del childList[depth]
                depth -= 1


def listDir(pathTuple: Tuple[str, str, bool, bool]) -> List[Tuple[str, str, bool, bool]]:
    '''returns a list of Tuple[filePath:str, fileName:str, isDir:bool, includeFiles:bool]'''
    filePath = pathTuple[0]
    isDir = pathTuple[2]
    includeFiles = pathTuple[3]
    if isDir:
        files = []
        files2 = []
        for it in os.listdir(filePath):
            childPath = os.path.join(filePath, it)
            if os.path.isdir(childPath):
                files.append((childPath, it, True, includeFiles))
            elif os.path.isfile(childPath):
                if includeFiles:
                    files2.append((childPath, it, False, includeFiles))
            elif os.path.islink(childPath):
                srcPath = os.readlink(childPath)
                if os.path.isdir(srcPath):
                    files.append((childPath, it, True, includeFiles))
                else:
                    if includeFiles:
                        files2.append((childPath, it, False, includeFiles))
        files.extend(files2)
        return files


def walkDir(absDir: str, maxDepth: int = 0xFFFFFFFF, includeFiles: bool = True) -> Iterator[Tuple[str, str, bool, int, int]]:
    for (filePath, fileName, isDir, includeFiles), depth, remainCount in walkTree(
            (absDir, '', True, includeFiles), getChildren=listDir, includeRoot=False, maxDepth=maxDepth):
        yield filePath, fileName, isDir, depth, remainCount


def copyFile(src: str, dst: str, log: bool = True) -> None:
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    else:
        if dst[-1] == '\\' or dst[-1] == '/':
            dirPath = dst
            dst = dirPath + os.path.basename(src)
        else:
            dirPath = os.path.dirname(dst)
        if dirPath and not os.path.exists(dirPath):
            os.makedirs(dirPath)
    shutil.copyfile(src, dst)
    if log:
        print(f'copy file: {src}\n        -> {dst}')


def copyDir(src: str, dst: str, log: bool = True) -> int:
    """return int, files count"""
    if src[-1] == os.path.sep:
        src = src[:-1]
    if dst[-1] != os.path.sep:
        dst = dst + os.sep
    srcLen = len(src)
    if not os.path.exists(dst):
        os.makedirs(dst)
    fileCount = 0
    for filePath, fileName, isDir, depth, remainCount in walkDir(src):
        relativeName = filePath[srcLen + 1:]
        dstPath = dst + relativeName
        if isDir:
            if not os.path.exists(dstPath):
                os.makedirs(dstPath)
                if log:
                    print(f'create dir: {dstPath}')
        else:
            shutil.copyfile(filePath, dstPath)  # dstPath's dir must exists, will over write dstPath if dstPath exists
            fileCount += 1
            if log:
                print(f'copy file {fileCount}: {dstPath}')


def renameFilesInDir(src: str, find: str, replace: str, log: bool = True) -> int:
    """return int, files count that are renamed"""
    fileCount = 0
    for filePath, fileName, isDir, depth, remainCount in walkDir(src):
        if not isDir:
            newFileName = fileName.replace(find, replace)
            if fileName != newFileName:
                newFilePath = filePath[:len(filePath) - len(fileName)] + newFileName
                if os.path.exists(newFilePath):
                    os.remove(newFilePath)
                os.rename(filePath, newFilePath)
                fileCount += 1
                if log:
                    print(f'{fileCount}: {filePath}\n  -> {newFilePath}, file renamed')


def walkZip(zipPath: str, getFileObjCondition: Callable[[zipfile.ZipInfo], bool] = None) -> Iterator[Tuple[bool, zipfile.ZipInfo, zipfile.ZipExtFile]]:
    """
    getFileObjCondition: getFileObjCondition(zipInfo:ZipInfo)->bool
    return tuple(isDir:bool, zipInfo:ZipInfo, fileObj:ZipExtFile)
    zipInfo.is_dir(), zipInfo.filename, ...
    """
    with zipfile.ZipFile(zipPath, 'r') as zin:
        for zipInfo in zin.infolist():
            if zipInfo.is_dir():
                yield True, zipInfo, None
            else:
                if getFileObjCondition and getFileObjCondition(zipInfo):
                    with zin.open(zipInfo.filename, 'r') as fin:
                        yield False, zipInfo, fin
                        # shutil.copyfileobj(fin, fout, 512000)  # avoid too much memory, default 1MB if pass 0 to 3rd parameter
                else:
                    yield False, zipInfo, None


def zipFile(srcPath: str, dstPath: str, nameInZip: str = None) -> None:
    '''if nameInZip is None, the dir tree in zip file is the same as srcPath'''
    with zipfile.ZipFile(dstPath, 'w', zipfile.ZIP_LZMA) as zf:
        if nameInZip:
            zf.writestr(nameInZip, getFileBytes(srcPath))
        else:
            zf.write(srcPath)


def zipBytesToFile(src: bytes, dstPath: str, nameInZip: str) -> None:
    with zipfile.ZipFile(dstPath, 'w', zipfile.ZIP_LZMA) as zf:
        zf.writestr(nameInZip, src)


def zipFileToBytes(srcPath: bytes, nameInZip: str = None) -> bytes:
    '''if nameInZip is None, the dir tree in zip file is the same as srcPath'''
    memFile = io.BytesIO()
    with zipfile.ZipFile(memFile, 'w', zipfile.ZIP_LZMA) as zf:
        if nameInZip:
            zf.writestr(nameInZip, getFileBytes(srcPath))
        else:
            zf.write(srcPath)
    memBytes = memFile.getvalue()
    return memBytes


def zipBytesToBytes(src: bytes, nameInZip: str) -> bytes:
    memFile = io.BytesIO()
    with zipfile.ZipFile(memFile, 'w', zipfile.ZIP_LZMA) as zf:
        zf.writestr(nameInZip, src)
    memBytes = memFile.getvalue()
    return memBytes


def extractOneFileInZip(zipPath: str, dstDir: str, fileEnd: str, log: bool = True) -> bool:
    """
    fileEnd: str.
    dstDir: str, should end with \\(not must).
    """
    if dstDir[-1] != os.sep:
        dstDir = dstDir + os.sep
    if not os.path.exists(dstDir):
        os.makedirs(dstDir)
    for isDir, zipInfo, zipFile in walkZip(zipPath, lambda zInfo: zInfo.filename.endswith(fileEnd)):
        if zipFile:
            dstPath = dstDir + os.path.basename(fileEnd)
            with open(dstPath, 'wb') as fout:
                shutil.copyfileobj(zipFile, fout)
            if log:
                print(f'copy file: {dstPath}')
            return True
    return False


def extractZip(zipPath: str, dstDir: str, subDirInZip: str = None, log: bool = True) -> int:
    """
    subDirInZip: str, if None, extrac all contents to dstDir, if not None, must not be end with / and can not use \\ in subDirInZip.
    dstDir: str, should end with \\(not must).
    returns int, files count.
    """
    if dstDir[-1] != os.sep:
        dstDir = dstDir + os.sep
    fileCount = 0
    if not subDirInZip:
        for isDir, zipInfo, zipFile in walkZip(zipPath, lambda zInfo: True):
            if isDir:
                dstPath = dstDir + zipInfo.filename
                if not os.path.exists(dstPath):
                    os.makedirs(dstPath)
                if log:
                    print(f'create dir: {dstPath}')
            else:
                dstPath = dstDir + zipInfo.filename
                with open(dstPath, 'wb') as fout:
                    shutil.copyfileobj(zipFile, fout)
                fileCount += 1
                if log:
                    print(f'extract file {fileCount}: {dstPath}')
        return fileCount

    def checkFunc(zipInfo: zipfile.ZipInfo) -> bool:
        return subDirInZip in zipInfo.filename

    foundDir = False
    for isDir, zipInfo, zipFile in walkZip(zipPath, checkFunc):
        if isDir:
            index = zipInfo.filename.find(subDirInZip)
            if not foundDir and index >= 0:
                foundDir = True
            if foundDir:
                if index < 0:
                    break
                createDir = dstDir + zipInfo.filename[index + len(subDirInZip) + 1:]
                if not os.path.exists(createDir):
                    os.makedirs(createDir)
                if log:
                    print(f'create dir: {createDir}')
        else:
            if zipFile:
                index = zipInfo.filename.find(subDirInZip)
                dstPath = dstDir + zipInfo.filename[index + len(subDirInZip) + 1:]
                with open(dstPath, 'wb') as fout:
                    shutil.copyfileobj(zipFile, fout)
                fileCount += 1
                if log:
                    print(f'extract file {fileCount}: {dstPath}')
            else:
                if foundDir:
                    break
    return fileCount


def getDpiScale() -> float:
    if sys.platform == 'win32':
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        dc = user32.GetDC(None)
        widthScale = gdi32.GetDeviceCaps(dc, 8)
        # heightScale = gdi32.GetDeviceCaps(dc, 10)
        width = gdi32.GetDeviceCaps(dc, 118)
        # height = gdi32.GetDeviceCaps(dc, 117)
        user32.ReleaseDC(None, dc)
        return width / widthScale
    return 1


# def getLocalIP() -> str:
    # ip = ''
    # try:
        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.connect(('8.8.8.8', 80))
        # ip = s.getsockname()[0]
    # finally:
        # s.close()
    # return ip


def fileSize2Str(sizeInBytes: int) -> str:
    if sizeInBytes >= 1073741824:  # 1024**3
        return f'{sizeInBytes/1073741824:.2f} GB'
    elif sizeInBytes >= 1048576:  # 1024**2
        return f'{sizeInBytes/1048576:.2f} MB'
    elif sizeInBytes >= 1024:
        return f'{sizeInBytes/1024:.2f} KB'
    elif sizeInBytes > 1:
        return f'{sizeInBytes} Bytes'
    else:
        return f'{sizeInBytes} Byte'


def getFileSizeStr(path: str) -> str:
    sizeInBytes = os.path.getsize(path)
    return fileSize2Str(sizeInBytes)


def prettyDict(dt: dict, indent: int = 2, indentStr: str = ' ', parentIndent: int = 0) -> str:
    strs = []
    strs.append('{')
    count = len(dt)
    index = 0
    for k, v in dt.items():
        curIndent = parentIndent + indent
        if isinstance(v, dict):
            strs.append(f'\n{indentStr * (curIndent)}{repr(k)}: {prettyDict(v, indent, indentStr, curIndent)}')
        else:
            strs.append(f'\n{indentStr * (curIndent)}{repr(k)}: {repr(v)}')
        index += 1
        if index < count:
            strs.append(',')
    strs.append('\n')
    strs.append(indentStr * parentIndent)
    strs.append('}')
    return ''.join(strs)

