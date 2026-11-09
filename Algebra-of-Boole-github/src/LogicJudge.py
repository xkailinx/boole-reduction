# LogicJudge.py: This should be the inefficient version.
import sympy as sp
import time


def reducesymbol(string: str):
    idx = 0
    result = ""
    length = len(string)
    while(idx < length and string[idx] == ' '):
        idx += 1
    if(string[idx] >= '1' and string[idx] <= '9'):    
        while(idx < length and string[idx] >= '0' and string[idx] <= '9'):
            idx += 1
        if (int(string[idx-1])- 0 ) % 2 == 0:
            return "0"
        while (idx < length and string[idx] == ' '):
            idx += 1
    if (idx == length):                     
        return "1"
    while(idx < length):
        while(idx < length and (string[idx] == '*' or (string[idx] >= '0' and string[idx] <= '9'))):    
            idx += 1
        if (idx == length):
            return result
        tempchar = string[idx]
        if (tempchar == ' '):
            idx += 1
            continue
        result += tempchar
        idx += 1
    return result


def BooleReduce(string : str) -> str:
    varset = set()
    for s in string:
        if(s != ' ' and s != '+' and s != '*' and s != '(' and s != ')'):
            varset.add(s)
    sp.var(varset)
    parts = str(sp.expand(string)).split("+")
    res = set()     
    for partstr in parts:
        tempstr = reducesymbol(partstr)
        if (tempstr == "0"):
            continue
        if (tempstr in res):
            res.remove(tempstr)
            continue
        res.add(tempstr)
    resultlist = list(res)
    resultlist.sort()
    result = ""
    for val in resultlist:
        result += val 
        result += " + "
    return result[:-3]

def Boolstr2symstr(string : str) -> str:   
    def issymbol(c):
        return c!=' ' and c!='+' and c!='(' and c!=')'
    result = ""
    idx = 0
    length = len(string)
    while(idx < length):
        if (issymbol(string[idx])):
            result += string[idx]
            if idx < length -1 and (issymbol(string[idx+1]) or string[idx+1] == '('):    
                result += "*"
        elif string[idx] == ')':
            result += string[idx]
            if idx < length -1 and (issymbol(string[idx+1]) or string[idx+1] == '('):    
                result += "*"
        else:
            result += string[idx]
        idx += 1
    return result



def findrightsymbol(string : str, i : int):
    if string[i] == '(':
        j = i+1
        flag = 1
        while (j < len(string) and flag != 0):
            if (string[j] == ')'):
                flag -= 1
                if flag == 0:
                    break
            elif (string[j] == '('):
                flag += 1
            j += 1
        return j, string[i: j+1]
    else:
        j = i
        while (j < len(string) and string[j] != ' ' and string[j] != '~' and string[j] != '&' and string[j] != '|' and string[j] != ')' and string[j] != '(' and string[j] != '-'):
            j += 1
        return j-1, string[i: j]

def findleftsymbol(string : str, i : int):
    if string[i] == ')':
        j = i-1
        flag = 1
        while (j >= 0 and flag != 0):
            if (string[j] == '('):
                flag -= 1
                if flag == 0:
                    break
            elif (string[j] == ')'):
                flag += 1
            j -= 1
        return j, string[j : i+1]
    else:
        j = i
        while (j >= 0 and string[j] != ' ' and string[j] != '~' and string[j] != '&' and string[j] != '|' and string[j] != ')' and string[j] != '(' and string[j] != '-'):
            j -= 1
        return j+1, string[j+1: i+1]

def findlogicsymbol(string : str):
    i = 0
    while(i < len(string)):
        if (string[i] == '&' or string[i] == '~' or string[i] == '|' or string[i] == '-'):
            break
        i += 1
    return i

def Logic2algebra(string : str) -> str:
    stringtemp = string
    i = findlogicsymbol(stringtemp)
    while (i != len(stringtemp)):
        # print(i, stringtemp)
        if (stringtemp[i] == '&'):
            idxi = i+1
            idxj = i-1
            while(idxi < len(stringtemp) and stringtemp[idxi] == ' '):
                idxi += 1
            while(idxj >= 0 and stringtemp[idxj] == ' '):
                idxj -= 1
            rightj, strj = findrightsymbol(stringtemp, idxi)
            lefti, stri = findleftsymbol(stringtemp, idxj)
            strand = stri + strj
            string1 = stringtemp
            stringtemp = string1[0:lefti] + strand + string1[rightj+1:]

        elif (stringtemp[i] == '|'):
            idxi = i+1
            idxj = i-1
            while(idxi < len(stringtemp) and stringtemp[idxi] == ' '):
                idxi += 1
            while(idxj >= 0 and stringtemp[idxj] == ' '):
                idxj -= 1
            rightj, strj = findrightsymbol(stringtemp, idxi)
            lefti, stri = findleftsymbol(stringtemp, idxj)
            stror = "(" + stri + " + " + strj + " + "+ stri + strj + ")"
            string1 = stringtemp
            stringtemp = string1[0:lefti] + stror + string1[rightj+1:]
        elif (stringtemp[i] == '~'):
            idxi = i+1
            while(idxi < len(stringtemp) and stringtemp[idxi] == ' '):
                idxi += 1
            rightj, strj = findrightsymbol(stringtemp, idxi)
            strnot = "(1 + " + strj + ")"
            string1 = stringtemp
            stringtemp = string1[0:i] + strnot + string1[rightj+1:]
        else:
            idxi = i+3
            idxj = i-1
            while(idxi < len(stringtemp) and stringtemp[idxi] == ' '):
                idxi += 1
            while(idxj >= 0 and stringtemp[idxj] == ' '):
                idxj -= 1
            rightj, strj = findrightsymbol(stringtemp, idxi)
            lefti, stri = findleftsymbol(stringtemp, idxj)
            stror = "(1 + " + stri + " + " + stri + strj + ")"
            string1 = stringtemp
            stringtemp = string1[0:lefti] + stror + string1[rightj+1:] 
        i = findlogicsymbol(stringtemp)
    return stringtemp



def LogicJudge():
    string = input("Enter a logical expression containing only &、|、~、()、-->: ")
    #print("The entered logical expression is: ", string)

    # Measure time for converting to Boolean algebra
    start_time = time.time()
    # convert to Boolean algebra form
    logstr = Logic2algebra(string)

    #print("The logical expression converted to Boolean algebra is: ", logstr)

    symstr = Boolstr2symstr(logstr)

    # simplify using sympy's BooleReduce
    res = BooleReduce(symstr)
    #print("The result of the expression (1 means correct) is:", res)
    end_time = time.time()


    print(f"Time taken to simplify the expression: {end_time - start_time:.4f} seconds")


if __name__ == '__main__':
    LogicJudge()