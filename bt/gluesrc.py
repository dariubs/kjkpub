# A script to glue multiple C/C++ source file together to create
# one file for compilation
# Similar to (and based on) sqlite's amalgamation tcl script (tool/mksqlite3c.tcl)
# Files to glue must be described in gluesrcdef.py file which needs the following:
"""
file_out = "out.cpp"
root_dir = r"c:\src" # or set to None

# source_files and header_files is an array of tuples
# each tuple starts with directory that has the files (relative to root_dir
# if root_dir is set) followed by a list of 
source_files = [
   (r"dir1", "file1.cpp", "file2.cpp", "file3.cpp")
  ,(r"dir2", "file1.cpp", "file2.cpp")
]
header_files = [
   (r"dir1", "inc1.h", "inc2.h")
  ,(r"dir2", "inc1.h", "inc2.h", "inc3.h")
]
"""

import sys, os, os.path, string, re
try:
    import gluesrcdef
except:
    print "You need to create gluesrcdef.py which describes which source/header files to glue together"
    sys.exit(1)

include_re = r'#\s?include\s?["<"]([^">]+)[">]'
include_rec = re.compile(include_re)

def convert_path_name(name):
    if os.name is "nt":
        return name.replace(r"/", "\\")
    return name

def include_from_line(line):
    global include_rec
    m = include_rec.search(line)
    if m:
        inc = convert_path_name(m.group(1))
        return inc
    return None

def build_src_info():
    sources = {}
    try:
        src_files = gluesrcdef.source_files
    except:
        print "Error in gluesrcdef.py: source_files not defines"
        sys.exit(1)
    for src_dir_info in src_files:
        dir = src_dir_info[0]
        files = src_dir_info[1:]
        if gluesrcdef.root_dir:
            dir = os.path.join(gluesrcdef.root_dir, dir)
        if not os.path.exists(dir):
            print "Error in src_files in gluesrcdef.py. Dir '%s' doesn't exist" % dir
            sys.exit(1)
        for file in files:
            file_path = os.path.join(dir, file)
            if not os.path.exists(file_path):
                print "Error in src_files in gluesrcdef.py. File '%s' doesn't exist" % file_path
            assert file_path not in sources
            sources[file_path] = 1 # number doesn't matter
    return sources


class HeadersInfo:
    (SEEN, NOT_SEEN) = range(2)
    def __init__(self):
        self.headers = {}
    def add_dir(self, hdr_dir_info):
        dir = hdr_dir_info[0]
        files = hdr_dir_info[1:]
        if gluesrcdef.root_dir:
            dir = os.path.join(gluesrcdef.root_dir, dir)
        if not os.path.exists(dir):
            print "Error in header_files in gluesrcdef.py. Dir '%s' doesn't exist" % dir
            sys.exit(1)
        for file in files:
            file = convert_path_name(file)
            file_path = os.path.join(dir, file)
            if not os.path.exists(file_path):
                print "Error in header_files in gluesrcdef.py. File '%s' doesn't exist" % file_path
            assert file_path not in self.headers
            self.headers[file] = [file_path, NOT_SEEN]
    def known(self, header_name):
        file = convert_path_name(header_name)
        return self in self.headers

def build_hdr_info():
    try:
        header_files = gluesrcdef.header_files
    except:
        print "Error in gluesrcdef.py: header_files not defines"
        sys.exit(1)
    hdr_info = HeadersInfo()
    for hdr_dir_info in header_files:
        hdr_info.add_dir(hdr_dir_info)
    return hdr_info

def section_comment(text):
    text = " %s " % text
    text = text.center(74, '*')
    return "/*%s*/\n" % text

def include_path_from_name(include_name):
    return include_name

def known_include(include_name):
    return False

# TODO: better name than GlueMaker. SourceCombinator?
class GlueMaker:
    def __init__(self, out_file_path):
        self.out_file_path = out_file_path
        self.fo = None
        self.seen_headers = {}

    def get_fo(self):
        if not self.fo:
            self.fo = open(self.out_file_path, "wb")
        return self.fo

    def finish(self):
        assert self.fo
        self.fo.close()

    def writeln(self,txt):
        fo = self.get_fo()
        fo.write(txt + "\n")

    def write(self,txt):
        fo = self.get_fo()
        fo.write(txt)

    def copy_file(self,file_path):
        self.writeln(section_comment("Begin file '%s'" % file_path))
        for line in file(file_path):
            include_name = include_from_line(line)
            if known_include(include_name) and not seen_include(include_name):
                include_path = include_path_from_name(include_name)
                self.writeln(section_comment("Include %s in the middle of %s" % (include_name, file_path)))
                self.copy_file(include_path)
                self.writeln(section_comment("Continuing where we left off in %s" % file_path))
            else:
                self.write(line)
        self.writeln(section_comment("End of     '%s'" % file_path))

def main():
    try:
        file_out = gluesrcdef.file_out
    except:
        print "Error in gluesrcdef.py - file_out is not defined"
        sys.exit(1)
    sources = build_src_info()
    maker = GlueMaker(file_out)
    for file in sources.keys():
        maker.copy_file(file)
    maker.finish()

if __name__ == "__main__":
	main()
