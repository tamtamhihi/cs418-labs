from distutils.filelist import findall
import sys
import os
import re
import pprint

""" 
TODO
This function takes in a filename along with the file object (actually
a StringIO object at submission time) and
scans its contents against regex patterns. It returns a list of
(filename, type, value) tuples where type is either an 'e' or a 'p'
for e-mail or phone, and value is the formatted phone number or e-mail.
The canonical formats are:
     (name, 'p', '###-###-#####')
     (name, 'e', 'someone@something')
If the numbers you submit are formatted differently they will not
match the gold answers

NOTE: ***don't change this interface***, as it will be called directly by
the submit script

NOTE: You shouldn't need to worry about this, but just so you know, the
'f' parameter below will be of type StringIO at submission time. So, make
sure you check the StringIO interface if you do anything really tricky,
though StringIO should support most everything.
"""

def extract_email(name, line):
    res = []
    # Normal email
    email_pattern = r'[\w.+-]+[\s]*(?:@|&#x40;|\(at\))[\s]*[\w-]{2,}\.[\w.-]{2,}'
    matches = re.findall(email_pattern, line)
    for m in matches:
        email = m.replace(' ', '').replace('&#x40;', '@').replace('(at)', '@')
        if email[-1] == '.':
            email = email[:-1]
        res.append((name,'e',email))
    # Word by word email: at/where, dot/dom
    email_pattern = r'[\w.+-]+ (?:at|where) [\w-]{2,} (?:dot|dom|dt) [ \w.-]{2,}'
    matches = re.findall(email_pattern, line, re.I)
    for m in matches:
        email = m.replace(' at ', ' @ ').replace(' AT ', ' @ ')
        email = email.replace(' where ', ' @ ').replace(' WHERE ', ' @ ')
        email = email.replace(' dot ', ' . ').replace(' DOT ', ' . ')
        email = email.replace(' dom ', ' . ').replace(' DOM ', ' . ')
        email = email.replace(' dt ', ' . ').replace(' DT ', ' . ')
        email = email.split('@')
        ws = email[0].replace(' ', '')
        domains = list(email[1].split())
        domain = domains[0]
        i = 1
        while i < len(domains):
            if domains[i] == '.' and i+1 < len(domains):
                domain += '.' + domains[i+1]
                i += 2
            else: break
        email = ws + '@' + domain
        res.append((name,'e',email))
    # Word by word: at but no dot
    email_pattern = r'[\w.+-]+ (?:at|where) [\w.-]{2,}(?:[;.][\w;.-]{2,})+'
    matches = re.findall(email_pattern, line, re.I)
    for m in matches:
        email = m.replace(' at ', ' @ ').replace(' AT ', ' @ ')
        email = email.replace(' where ', ' @ ').replace(' WHERE ', ' @ ')
        email = email.replace(';', '.').replace(' ', '')
        res.append((name,'e',email))
    # Obfuscate email
    email_pattern = r"obfuscate\('[\w+.-]+','[\w+.-]+'\)"
    matches = re.findall(email_pattern, line, re.I)
    for m in matches:
        m = m[9:]
        email = m.replace('(', '').replace(')', '').replace("'", '')
        email = email.split(',')
        email = email[1] + '@' + email[0]
        res.append((name,'e',email))
    # Followed by email
    email_pattern = r'([\w+.-]+)\s\(followed by [&ldquo;"]+@([\w.-]+)'
    matches = re.findall(email_pattern, line)
    for m in matches:
        email = m[0] + '@' + m[1]
        res.append((name,'e',email))
    return res

def extract_phone(name, line):
    res = []
    # Normal phone
    phone_pattern = r'[0-9]{3}(?:-|&thinsp;| )[0-9]{3}(?:-|&thinsp;| )[0-9]{4}'
    matches = re.findall(phone_pattern, line)
    for m in matches:
        phone = m.replace(' ', '-').replace('&thinsp;', '-')
        res.append((name,'p',phone))
    # Parentheses phone
    phone_pattern = r'\([0-9]{3}\)[ ]*[0-9]{3}-[0-9]{4}'
    matches = re.findall(phone_pattern, line)
    for m in matches:
        phone = m.replace('(', '').replace(')', '').replace(' ', '')
        phone = phone[:3] + '-' + phone[3:]
        res.append((name,'p',phone))
    return res

def sufprocess_emails(emails):
    ofc_emails = []
    for name, type, email in emails:
        ws, _ = email.split('@')
        if 'server' in ws.lower():
            continue
        email = email.replace(' ', '').replace('-', '')
        if email[-1] == '.':
            email = email[:-1]
        ofc_emails.append((name, type, email))
    return ofc_emails

def process_file(name, f):
    # note that debug info should be printed to stderr
    # sys.stderr.write('[process_file]\tprocessing file: %s\n' % (path))
    res = []
    for line in f:
        emails = extract_email(name, line)
        phones = extract_phone(name, line)
        res.extend(sufprocess_emails(emails))
        res.extend(phones)
    return res

"""
You should not need to edit this function, nor should you alter
its interface as it will be called directly by the submit script
"""
def process_dir(data_path):
    # get candidates
    guess_list = []
    for fname in os.listdir(data_path):
        if fname[0] == '.':
            continue
        path = os.path.join(data_path,fname)
        f = open(path,'r')
        f_guesses = process_file(fname, f)
        guess_list.extend(f_guesses)
    return guess_list

"""
You should not need to edit this function.
Given a path to a tsv file of gold e-mails and phone numbers
this function returns a list of tuples of the canonical form:
(filename, type, value)
"""
def get_gold(gold_path):
    # get gold answers
    gold_list = []
    f_gold = open(gold_path,'r')
    for line in f_gold:
        gold_list.append(tuple(line.strip().split('\t')))
    return gold_list

"""
You should not need to edit this function.
Given a list of guessed contacts and gold contacts, this function
computes the intersection and set differences, to compute the true
positives, false positives and false negatives.  Importantly, it
converts all of the values to lower case before comparing
"""
def score(guess_list, gold_list):
    guess_list = [(fname, _type, value.lower()) for (fname, _type, value) in guess_list]
    gold_list = [(fname, _type, value.lower()) for (fname, _type, value) in gold_list]
    guess_set = set(guess_list)
    gold_set = set(gold_list)

    tp = guess_set.intersection(gold_set)
    fp = guess_set - gold_set
    fn = gold_set - guess_set

    pp = pprint.PrettyPrinter()
    #print 'Guesses (%d): ' % len(guess_set)
    #pp.pprint(guess_set)
    #print 'Gold (%d): ' % len(gold_set)
    #pp.pprint(gold_set)
    print 'True Positives (%d): ' % len(tp)
    pp.pprint(tp)
    print 'False Positives (%d): ' % len(fp)
    pp.pprint(fp)
    print 'False Negatives (%d): ' % len(fn)
    pp.pprint(fn)
    print 'Summary: tp=%d, fp=%d, fn=%d' % (len(tp),len(fp),len(fn))

"""
You should not need to edit this function.
It takes in the string path to the data directory and the
gold file
"""
def main(data_path, gold_path):
    guess_list = process_dir(data_path)
    gold_list =  get_gold(gold_path)
    score(guess_list, gold_list)

"""
commandline interface takes a directory name and gold file.
It then processes each file within that directory and extracts any
matching e-mails or phone numbers and compares them to the gold file
"""
if __name__ == '__main__':
    if (len(sys.argv) != 3):
        print 'usage:\tSpamLord.py <data_dir> <gold_file>'
        sys.exit(0)
    main(sys.argv[1],sys.argv[2])