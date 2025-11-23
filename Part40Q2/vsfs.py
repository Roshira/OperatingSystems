#!/usr/bin/env python3

import random
from optparse import OptionParser

# --- Class Definitions ---

class bitmap:
    def __init__(self, size):
        self.size = size
        self.bmap = []
        for i in range(size):
            self.bmap.append(0)

    def alloc(self):
        for i in range(len(self.bmap)):
            if self.bmap[i] == 0:
                self.bmap[i] = 1
                return i
        return -1

    def free(self, num):
        assert(self.bmap[num] == 1)
        self.bmap[num] = 0

    def markAllocated(self, num):
        self.bmap[num] = 1

    def dump(self):
        s = ""
        for i in range(len(self.bmap)):
            s += str(self.bmap[i])
        return s

class block:
    def __init__(self, ftype):
        assert(ftype == 'd' or ftype == 'f' or ftype == 'free')
        self.ftype = ftype
        # only for directories, properly a list of (name, inum) tuples
        self.dirUsed = 0
        self.maxDirSize = 10
        self.dirList = []
        # only for files, a string
        self.data = ""

    def dump(self):
        if self.ftype == 'free':
            return "[]"
        elif self.ftype == 'd':
            rc = ""
            for d in self.dirList:
                # d is (name, inum)
                short_name = d[0]
                if len(short_name) > 10:
                    short_name = short_name[0:10]
                rc += " (" + short_name + "," + str(d[1]) + ")"
            return "[" + rc + "]"
        else:
            return "[" + self.data + "]"

    def setType(self, ftype):
        assert(self.ftype == 'free')
        self.ftype = ftype

    def addData(self, data):
        assert(self.ftype == 'f')
        self.data = data

    def getNumEntries(self):
        assert(self.ftype == 'd')
        return self.dirUsed

    def getFreeEntry(self):
        assert(self.ftype == 'd')
        if self.dirUsed == self.maxDirSize:
            return -1
        return self.dirUsed

    def getEntry(self, num):
        assert(self.ftype == 'd')
        assert(num < self.dirUsed)
        return self.dirList[num]

    def addEntry(self, name, inum):
        assert(self.ftype == 'd')
        assert(self.dirUsed < self.maxDirSize)
        self.dirList.append((name, inum))
        self.dirUsed += 1

    def delEntry(self, name):
        assert(self.ftype == 'd')
        for i in range(len(self.dirList)):
            d = self.dirList[i]
            if d[0] == name:
                self.dirList.pop(i)
                self.dirUsed -= 1
                return d[1]
        return -1

    def entryExists(self, name):
        assert(self.ftype == 'd')
        for d in self.dirList:
            if d[0] == name:
                return True
        return False

    def free(self):
        assert(self.ftype != 'free')
        if self.ftype == 'd':
            # check for only dot, dotdot
            if self.dirUsed > 2:
                return -1
        self.ftype = 'free'
        self.dirList = []
        self.dirUsed = 0
        self.data = ""
        return 0

class inode:
    def __init__(self, ftype='free', addr=-1, refCnt=1):
        self.setAll(ftype, addr, refCnt)

    def setAll(self, ftype, addr, refCnt):
        assert(ftype == 'd' or ftype == 'f' or ftype == 'free')
        self.ftype  = ftype
        self.addr   = addr
        self.refCnt = refCnt

    def incRef(self):
        self.refCnt += 1

    def decRef(self):
        self.refCnt -= 1

    def getRef(self):
        return self.refCnt

    def setType(self, ftype):
        assert(ftype == 'd' or ftype == 'f' or ftype == 'free')
        self.ftype = ftype

    def setAddr(self, block):
        self.addr = block

    def getSize(self):
        if self.addr == -1:
            return 0
        else:
            return 1

    def getAddr(self):
        return self.addr

    def getType(self):
        return self.ftype

    def free(self):
        self.ftype = 'free'
        self.addr  = -1
        self.refCnt = 0

class fs:
    def __init__(self, numInodes, numData):
        self.numInodes = numInodes
        self.numData   = numData
        
        self.ibitmap = bitmap(self.numInodes)
        self.inodes  = []
        for i in range(self.numInodes):
            self.inodes.append(inode())

        self.dbitmap = bitmap(self.numData)
        self.data    = []
        for i in range(self.numData):
            self.data.append(block('free'))

        # root inode
        self.ibitmap.markAllocated(0)
        self.inodes[0].setAll('d', 0, 2)
        self.dbitmap.markAllocated(0)
        self.data[0].setType('d')
        self.data[0].addEntry('.', 0)
        self.data[0].addEntry('..', 0)

        self.files = [] # list of filenames

    def dump(self):
        print('inode bitmap ', self.ibitmap.dump())
        print('inodes       ', end='')
        for i in range(0,self.numInodes):
            ftype = self.inodes[i].getType()
            if ftype == 'free':
                print('[]', end='')
            else:
                print(f'[{ftype} a:{self.inodes[i].getAddr()} r:{self.inodes[i].getRef()}]', end='')
        print('')
        print('data bitmap  ', self.dbitmap.dump())
        print('data         ', end='')
        for i in range(self.numData):
            print(self.data[i].dump(), end='')
        print('')

    def makeName(self):
        p = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        return random.choice(p)

    def inodeAlloc(self):
        return self.ibitmap.alloc()

    def inodeFree(self, num):
        self.ibitmap.free(num)
        self.inodes[num].free()

    def dataAlloc(self):
        return self.dbitmap.alloc()

    def dataFree(self, num):
        self.dbitmap.free(num)
        self.data[num].free()

    def getParent(self, name):
        # assumes only one level of directory
        # thus, all files/directories are in root directory
        return 0

    def deleteFile(self, tfile):
        # 1. Look up file in parent directory
        # 2. Free inode
        # 3. Free data block (if any)
        # 4. Remove from parent directory
        
        parentInum = self.getParent(tfile)
        parentDataBlock = self.inodes[parentInum].getAddr()
        
        # Does file exist in parent?
        if not self.data[parentDataBlock].entryExists(tfile):
            print(f'Error: cannot delete file {tfile} (does not exist)')
            return -1

        # Find inumber
        inum = self.data[parentDataBlock].delEntry(tfile)
        
        # Check reference count
        if self.inodes[inum].getType() == 'd':
            # special case: cannot delete directory if it is not empty
            # BUT: in this simple FS, we only have one level, so only check . and ..
            dblock = self.inodes[inum].getAddr()
            if self.data[dblock].getNumEntries() > 2:
                print(f'Error: cannot delete directory {tfile} (not empty)')
                # Add entry back to parent (undo)
                self.data[parentDataBlock].addEntry(tfile, inum)
                return -1

        # Decrement ref count
        self.inodes[inum].decRef()
        if self.inodes[inum].getRef() == 0:
            # Free data block if allocated
            dblock = self.inodes[inum].getAddr()
            if dblock != -1:
                self.dataFree(dblock)
            # Free inode
            self.inodeFree(inum)
        return 0

    def createLink(self, target, newfile, parent):
        # 1. Lookup target file
        parentInum = self.getParent(target)
        parentDataBlock = self.inodes[parentInum].getAddr()
        if not self.data[parentDataBlock].entryExists(target):
            # print('Error: cannot link to file (does not exist)')
            return -1
        
        # Find inumber of target
        # (This is inefficient, but simple)
        # In real FS, we would just do a lookup
        # Here we have to search the parent directory list
        # Since we just checked existence, we know it is there.
        # But wait, entryExists doesn't return inum.
        # So we have to do it again or scan manually.
        # Actually, let's just cheat and scan.
        targetInum = -1
        for i in range(self.data[parentDataBlock].getNumEntries()):
             e = self.data[parentDataBlock].getEntry(i)
             if e[0] == target:
                 targetInum = e[1]
                 break
        
        if self.inodes[targetInum].getType() == 'd':
            # cannot hard link to directory
            return -1

        # 2. Check if newfile already exists
        if self.data[parentDataBlock].entryExists(newfile):
            return -1

        # 3. Increment ref count of target inode
        self.inodes[targetInum].incRef()

        # 4. Add entry to parent directory
        self.data[parentDataBlock].addEntry(newfile, targetInum)
        return 0

    def createFile(self, parent, newfile, ftype):
        # 1. Allocate inode
        inum = self.inodeAlloc()
        if inum == -1:
            return -1
        
        # 2. If directory, allocate data block
        dblock = -1
        if ftype == 'd':
            dblock = self.dataAlloc()
            if dblock == -1:
                self.inodeFree(inum)
                return -1
            self.data[dblock].setType('d')
            self.data[dblock].addEntry('.', inum)
            self.data[dblock].addEntry('..', parent)
        
        # 3. Update inode
        self.inodes[inum].setAll(ftype, dblock, 1)

        # 4. Add to parent directory
        parentDataBlock = self.inodes[parent].getAddr()
        if self.data[parentDataBlock].getFreeEntry() == -1:
            # Parent directory full
            self.inodeFree(inum)
            if dblock != -1:
                self.dataFree(dblock)
            return -1
            
        self.data[parentDataBlock].addEntry(newfile, inum)
        return 0

    def writeFile(self, tfile, data):
        parentInum = self.getParent(tfile)
        parentDataBlock = self.inodes[parentInum].getAddr()
        
        if not self.data[parentDataBlock].entryExists(tfile):
            return -1
        
        # Find inum
        targetInum = -1
        for i in range(self.data[parentDataBlock].getNumEntries()):
             e = self.data[parentDataBlock].getEntry(i)
             if e[0] == tfile:
                 targetInum = e[1]
                 break
        
        if self.inodes[targetInum].getType() == 'd':
            return -1

        # Check if data block already allocated
        dblock = self.inodes[targetInum].getAddr()
        if dblock == -1:
            dblock = self.dataAlloc()
            if dblock == -1:
                return -1
            self.inodes[targetInum].setAddr(dblock)
            self.data[dblock].setType('f')

        self.data[dblock].addData(data)
        return 0

    def run(self, numRequests):
        # initial state
        self.dump()
        for i in range(numRequests):
            # random decision
            if len(self.files) > 0:
                op = random.random()
            else:
                op = 0.0 # force create if empty

            if op < 0.5:
                # create
                f = self.makeName()
                # 50% chance of file or dir
                if random.random() < 0.5:
                    print(f'mkdir("/{f}");')
                    if self.createFile(0, f, 'd') == -1:
                        print('mkdir failed: No space/inodes or dir full')
                    else:
                        self.files.append(f)
                else:
                    print(f'creat("/{f}");')
                    if self.createFile(0, f, 'f') == -1:
                        print('creat failed: No space/inodes or dir full')
                    else:
                        self.files.append(f)
            elif op < 0.7:
                # write
                if len(self.files) > 0:
                    f = random.choice(self.files)
                    print(f'fd=open("/{f}", O_WRONLY|O_APPEND); write(fd, buf, BLOCKSIZE); close(fd);')
                    if self.writeFile(f, "a") == -1:
                         print('write failed')
            elif op < 0.8:
                # delete
                if len(self.files) > 0:
                    f = random.choice(self.files)
                    print(f'unlink("/{f}");')
                    if self.deleteFile(f) == -1:
                        print('unlink failed')
                    else:
                        self.files.remove(f)
            else:
                 # link
                 if len(self.files) > 0:
                     target = random.choice(self.files)
                     newfile = self.makeName()
                     print(f'link("/{target}", "/{newfile}");')
                     if self.createLink(target, newfile, 0) == -1:
                         print('link failed')
                     else:
                         self.files.append(newfile)
            
            self.dump()

# --- Main ---

parser = OptionParser()
parser.add_option("-s", "--seed", dest="seed", help="random seed", default=0, type="int")
parser.add_option("-i", "--numInodes", dest="numInodes", help="number of inodes in file system", default=8, type="int")
parser.add_option("-d", "--numData", dest="numData", help="number of data blocks in file system", default=8, type="int")
parser.add_option("-n", "--numRequests", dest="numRequests", help="number of requests to simulate", default=10, type="int")
parser.add_option("-r", "--reverse", dest="reverse", help="instead of printing state, print ops", default=False, action="store_true")
parser.add_option("-c", "--compute", dest="compute", help="compute answers for me", default=False, action="store_true")

(options, args) = parser.parse_args()

random.seed(options.seed)

s = fs(options.numInodes, options.numData)

# Reverse mode: we print operations, user guesses state
if options.reverse:
    # We need to buffer output because we want to print operation FIRST,
    # then wait for user (or just print blank lines), then print state if -c is on.
    
    # Actually, the problem logic is: 
    # Print Op
    # If -c: Print State
    # Else: Print nothing (user fills in)
    pass

# Standard mode: print state, user guesses op
# BUT the logic inside s.run() prints op THEN state immediately.
# Let's adjust s.run logic or just run it?
# The standard vsfs.py from OSTEP just runs and prints everything if not controlled differently.
# However, for the homework, usually it hides something.

# Let's override the run loop here to match the specific "quiz" style if needed, 
# but the standard tool usually just dumps everything and you use your eyes to hide parts,
# OR it has specific logic.
# Looking at the standard vsfs.py, it prints everything.
# The user's job is to look at State 0 -> State 1 and deduce the op (Standard)
# OR look at Op -> deduce State (Reverse).

# Let's modify the run loop slightly to handle -r and -c properly as per OSTEP description.
# In the original vsfs.py, the logic is embedded.

# Re-implementing a cleaner run loop for the "Quiz" mode:

if options.reverse:
    # Show OP, hide STATE (unless -c)
    print("Initial state")
    s.dump()
    print("")
    
    for i in range(options.numRequests):
        # Pick op
        if len(s.files) > 0:
            op = random.random()
        else:
            op = 0.0 # force create

        op_desc = ""
        success = False
        
        if op < 0.5: # create
            f = s.makeName()
            if random.random() < 0.5:
                op_desc = f'mkdir("/{f}");'
                if s.createFile(0, f, 'd') != -1:
                    s.files.append(f)
                    success = True
                else:
                    op_desc += " [failed]"
            else:
                op_desc = f'creat("/{f}");'
                if s.createFile(0, f, 'f') != -1:
                    s.files.append(f)
                    success = True
                else:
                    op_desc += " [failed]"
        elif op < 0.7: # write
            if len(s.files) > 0:
                f = random.choice(s.files)
                op_desc = f'fd=open("/{f}", O_WRONLY|O_APPEND); write(fd, buf, BLOCKSIZE); close(fd);'
                if s.writeFile(f, "a") != -1:
                    success = True
                else:
                    op_desc += " [failed]"
        elif op < 0.8: # delete
            if len(s.files) > 0:
                f = random.choice(s.files)
                op_desc = f'unlink("/{f}");'
                if s.deleteFile(f) != -1:
                    s.files.remove(f)
                    success = True
                else:
                    op_desc += " [failed]"
        else: # link
            if len(s.files) > 0:
                target = random.choice(s.files)
                newfile = s.makeName()
                op_desc = f'link("/{target}", "/{newfile}");'
                if s.createLink(target, newfile, 0) != -1:
                    s.files.append(newfile)
                    success = True
                else:
                    op_desc += " [failed]"

        # Print Op
        print(op_desc)
        
        # If compute, print result state
        if options.compute:
            s.dump()
        else:
            print("  State? (Use -c to see the answer)")
        print("")

else:
    # Standard Mode: Show STATE, hide OP (unless -c)
    # Actually standard mode usually prints everything.
    # But usually for the homework "guess the op", it prints the states and hides the op?
    # No, typically vsfs.py prints everything and you just cover one part.
    # BUT, to match the behavior of OSTEP scripts:
    # If -c is NOT supplied, it might hide the op?
    # Actually, in standard OSTEP scripts, usually it prints the "Job" and you have to guess.
    # Here:
    # Standard: Prints "State 0", "State 1"... User guesses what happened between.
    
    # Let's simulate that:
    print("Initial state")
    s.dump()
    print("")

    for i in range(options.numRequests):
        # We need to perform the op silently first, then print the transition
        old_ibitmap = s.ibitmap.dump()
        # deep copy is hard here, but we just need to track the op string
        
        if len(s.files) > 0:
            op = random.random()
        else:
            op = 0.0

        op_desc = ""
        
        if op < 0.5: # create
            f = s.makeName()
            if random.random() < 0.5:
                op_str = f'mkdir("/{f}");'
                if s.createFile(0, f, 'd') != -1:
                    s.files.append(f)
                else:
                    op_str += " [failed]"
            else:
                op_str = f'creat("/{f}");'
                if s.createFile(0, f, 'f') != -1:
                    s.files.append(f)
                else:
                    op_str += " [failed]"
        elif op < 0.7: # write
            if len(s.files) > 0:
                f = random.choice(s.files)
                op_str = f'fd=open("/{f}", O_WRONLY|O_APPEND); write(fd, buf, BLOCKSIZE); close(fd);'
                if s.writeFile(f, "a") == -1:
                    op_str += " [failed]"
        elif op < 0.8: # delete
            if len(s.files) > 0:
                f = random.choice(s.files)
                op_str = f'unlink("/{f}");'
                if s.deleteFile(f) != -1:
                    s.files.remove(f)
                else:
                     op_str += " [failed]"
        else: # link
            if len(s.files) > 0:
                target = random.choice(s.files)
                newfile = s.makeName()
                op_str = f'link("/{target}", "/{newfile}");'
                if s.createLink(target, newfile, 0) != -1:
                    s.files.append(newfile)
                else:
                    op_str += " [failed]"

        if options.compute:
            print(op_str)
        else:
            print("Which operation took place?")
        
        s.dump()
        print("")
