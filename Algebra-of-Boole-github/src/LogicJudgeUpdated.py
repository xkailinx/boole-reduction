#################UPDATED!!! 
# LogicJudgeUpdated.py: This should be the efficient version.
"""
This file focuses on the specific implementation of the logic evaluation and simplification process.
It provides the functions for transforming logical expressions into a Boole expression and simplifying
them into their minimal forms (such as using sympy for Algebra of Boole simplification).
Purpose: evaluate truth/validity of logical expressions by transforming them into Algebra of Boole and simplifying them
"""
import sympy as sp
import time

from sympy.abc import _clash
set(_clash)
# Simplify an individual expression, such as (A**2 * B**3 --> AB)
def reducesymbol(string: str):
    idx = 0
    result = ""
    length = len(string)
    while(idx < length and string[idx] == ' '):
        idx += 1
    if(string[idx] >= '1' and string[idx] <= '9'):   # coefficient before
        while(idx < length and string[idx] >= '0' and string[idx] <= '9'):
            idx += 1
        if (int(string[idx-1])- 0 ) % 2 == 0:
            return "0"
        while (idx < length and string[idx] == ' '):
            idx += 1
    if (idx == length):                   # this segment is just a number
        return "1"
    while(idx < length):
        while(idx < length and (string[idx] == '*' or (string[idx] >= '0' and string[idx] <= '9'))):   # remove numbers
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

# Simplify sympy expression 
def BooleReduce(string : str) -> str:
    # varset = set()
    # for s in string:
    #     if(s != ' ' and s != '+' and s != '*' and s != '(' and s != ')'):
    #         varset.add(s)
    # sp.var(varset)
    # parts = str(sp.expand(string)).split("+")
    expr = sp.sympify(string, _clash)
    parts = str(sp.expand(expr)).split("+")
    
    res = set()    # save fianl result
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

def Boolstr2symstr(string : str) -> str:  # convert Boole expression to sympy expression
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


# Start from the right of the symbol to find the first complete logical expression, string[i] is not empty
# Return the rightmost position of the logical expression and the entire expression
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

# Return the position of the logical symbol in the string
def findlogicsymbol(string : str):
    i = 0
    while(i < len(string)):
        if (string[i] == '&' or string[i] == '~' or string[i] == '|' or string[i] == '-'):
            break
        i += 1
    return i

# Convert the logical expression to Boole expression
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



def cut_string_with_parentheses(input_string: str, nMinimum: int) -> list:
    """
    Cuts a long string with parentheses into smaller substrings at valid parentheses points.
    Each substring has a minimum length of nMinimum.

    Args:
        input_string (str): The input string containing parentheses.
        nMinimum (int): The minimum length of each substring.

    Returns:
        list: An array of smaller substrings.
    """
    result = []  # To store the resulting substrings
    start = 0    # Start index of the current substring
    balance = 0  # Tracks the balance of parentheses
    n = len(input_string)

    for i in range(n):
        if input_string[i] == '(':
            balance += 1
        elif input_string[i] == ')':
            balance -= 1

        # Check if the current position is a valid cutting point
        if balance == 0 and (i - start + 1) >= nMinimum:
            # Add the substring to the result
            result.append(input_string[start:i + 1])
            start = i + 1  # Move the start index to the next character

    #print("n, start and n-start", n, start, n-start)
    # Add the remaining part of the string if it meets the minimum length requirement
    if start < n: #and (n - start) >= nMinimum:
        result.append(input_string[start:])

    return result


nMinimum= 50


def LogicReduction():
    string = input("Enter logic expression with &、|、~、()、-->: ")
    logstr = Logic2algebra(string)
    
    #logstr = input("Algebra of Boole Expression: ")
    #print("Logical expression converted to the Boole expression:", logstr)
        
    program_start_time = time.time()
    logstr_array = cut_string_with_parentheses(logstr, nMinimum)
    #print("Partitioned strings", logstr_array)
    iterated_str = ""
    iterated_res = ""
   
    #print("iterated string", iterated_str)

    for i in range(len(logstr_array)):
        #print("logstr_array", i , logstr_array[i])
        if ( i == 0 ):
            iterated_str = iterated_str + logstr_array[i]
        else:
            iterated_str = "(" + iterated_res + ")" + logstr_array[i]
        
        #print("iterated string", iterated_str)
        start_time = time.time()
        symstr = Boolstr2symstr(iterated_str)
        end_time = time.time()
        elapsed_time = end_time - start_time
        #print(f"The boolstr to symbolic time is {elapsed_time:.4f} seconds")
        
        start_time = time.time()
        iterated_res = BooleReduce(symstr)
        end_time = time.time()
        elapsed_time = end_time - start_time
        #print(f"The reduciton time is {elapsed_time:.4f} seconds")
    #print("The reduced Boole expression: ", iterated_res)
    program_end_time = time.time()
    elapsed_time = program_end_time - program_start_time
    print(f"The elapsed time is {elapsed_time:.4f} seconds")
    
    
def BooleReduction():
          
       program_start_time = time.time()
       logstr = input("Enter Algebra of Boole expression: ")
        
       # print("time taken to convert to algebra", end_time - start_time)
       
       start_time = time.time()
       symstr = Boolstr2symstr(logstr)
       end_time = time.time()
       elapsed_time = end_time - start_time
       #print(f"The boolstr to symbolic time is {elapsed_time:.4f} seconds")
        
       start_time = time.time()
       res = BooleReduce(symstr)
       end_time = time.time()
       elapsed_time = end_time - start_time
       #print(f"The reduction time is {elapsed_time:.4f} seconds")
        
       print("The reduced Boole expression): ", res)
          
       program_end_time = time.time()
       elapsed_time = program_end_time - program_start_time
       print(f"The elapsed time is {elapsed_time:.4f} seconds")
        

if __name__ == '__main__':
    LogicReduction()