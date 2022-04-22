#from nltk.metrics import edit_distance
import os
import sys

"""
19125033 - Nguyen Ngoc Bang Tam
"""
def costmatrix(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0 for _ in range(n+1)] for _ in range(m+1)]
    for i in range(m):
        dp[i+1][0] = i+1
    for j in range(n):
        dp[0][j+1] = j+1
    for i in range(m):
        for j in range(n):
            dp[i+1][j+1] = min(dp[i+1][j], dp[i][j+1]) + 1
            if s1[i] == s2[j]:
                dp[i+1][j+1] = min(dp[i+1][j+1], dp[i][j])
            else:
                dp[i+1][j+1] = min(dp[i+1][j+1], dp[i][j] + 2)
    return dp

def backtrace(s1, s2, dp):
    m, n = len(s1), len(s2)
    operations = []
    i = m-1
    j = n-1
    while i >= 0:
        if dp[i+1][j+1] == dp[i+1][j] + 1: # insert a new character to s1
            operations.append('insertion')
            j -= 1
        elif dp[i+1][j+1] == dp[i][j+1] + 1: # delete a character from s1
            operations.append('deletion')
            i -= 1
        elif dp[i+1][j+1] == dp[i][j]: # match
            operations.append('match')
            i -= 1
            j -= 1
        else:
            operations.append('substitution')
            i -= 1
            j -= 1
    print()
    operations.reverse()
    print(operations)

def levenshtein(str1, str2):
    m, n = len(str1), len(str2)
    dp = costmatrix(str1, str2)
    backtrace(str1, str2, dp)
    return dp[m][n]

"""
You should not need to edit this function.
"""
def process_dir(data_path):
    # get candidates
    lst_input = []
    for filename in os.listdir(data_path):
        if filename.endswith('.txt'):
            lst_input.append(filename)
    return lst_input

"""
You should not need to edit this function.
"""
def main(data_path, gold_path):
    lst_input = process_dir(data_path)
    match = 0
    lev_gold = {}
    with open(os.path.join(gold_path, 'gold'), 'r') as fg:
        for line in fg:
            file, lev_g = line.replace('\n', '').split(' ')
            lev_gold.setdefault(file, lev_g)
    for file in lst_input:
        with open(os.path.join(data_path,file), 'r') as f:
            lines = f.readlines()
            str1, str2 = lines[0].split('\n')[0], lines[1].split('\n')[0]
            #guess levenshtein
            lev = levenshtein(str1, str2)
            #nltk levenshtein
            #lev_gold = levenshtein1(str1, str2)
            print file,' Your levenshtein:', lev, ' levenshtein:', lev_gold[file]
            if lev==int(lev_gold[file]): match += 1
    print 'Total match = ', match

"""
commandline interface takes a directory name and gold file.
It then processes each file within that directory and extracts any
matching e-mails or phone numbers and compares them to the gold file
"""
if __name__ == '__main__':
    if (len(sys.argv) != 3):
        print 'usage:\tlevenshtein.py <data_dir> <gold_dir>'
        sys.exit(0)
    main(sys.argv[1], sys.argv[2])
