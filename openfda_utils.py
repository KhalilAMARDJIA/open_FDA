import string
import glob
import re

def stop_char(word):
    word = repr(word)
    allowed = string.ascii_letters + " " + string.digits + "."+ "-" + ","
    word = re.sub('[^%s]' % allowed, '', word)
    return word

def relevant_file(db_file, ext):

    json_file = glob.glob(f'*{db_file}{ext}')

    if len(json_file) != 1:
        raise ValueError(
            f'several {db_file}{ext} files are present in the directory choose only one!')
    else:
        filename = json_file[0]
        return filename
