"""
This file defines the core logic and structure of my program
"""

from LogicJudge import *

# Symbol class, which can represent sets/statements (premises) and conclusions, including p/~p

class SymBol():
    def __init__(self, arg = None):
        if isinstance(arg, str):
            self.name = arg 
        else: 
            pass 
    def setname(self, name:str):
        self.name = name
    def __str__(self):
        return self.name 
    
class DesymBol(SymBol):
    def __init__(self, arg=None):  
        if isinstance(arg, str):  
            super().__init__(arg)  
        elif isinstance(arg, SymBol):  
            self.name = arg.name  
        else:  
            super().__init__()  
    def __str__(self):
        return "(NOT " + self.name + ")"
    
# Proposition class, p-->q - the inputs must be instances of SymBol/DesymBol
class Proposition():
    def __init__(self, sym1=None, sym2=None):  
        if sym1 is not None and sym2 is not None:  
            self.Sym1 = sym1  
            self.Sym2 = sym2  
        else:  
            self.Sym1 = None  
            self.Sym2 = None  
    # Set relation between the two symbols: sym1 --> sym2
    def setpre(self, sym1:SymBol):
        self.Sym1 = sym1
    def setpost(self, sym2:SymBol):
        self.Sym2 = sym2 
    def __str__(self):
        return str(self.Sym1) + "-->" + str(self.Sym2)
# Relation class p&q / p|q
class Relation():
    def __init__(self, sym1=None, sym2=None, relation:str = "AND"):  
        if sym1 is not None and sym2 is not None:  
            self.Sym1 = sym1  
            self.Sym2 = sym2
            self.relation = relation
        else:  
            self.Sym1 = None  
            self.Sym2 = None  
            self.relation = relation
    def setSymbol1(self, sym1:SymBol):
        self.Sym1 = sym1
    def setSymbol2(self, sym2:SymBol):
        self.Sym2 = sym2 
    def setRelation(self, relation:str):
        self.relation = relation
    def __str__(self):
        if (self.relation.upper() == "AND"):
            return str(self.Sym1) + " AND " + str(self.Sym2)
        elif (self.relation.upper() == "OR"):
            return str(self.Sym1) + " OR " + str(self.Sym2)
        else:
            print("Non-compliant! Set relation and/or ")

     
class LogicalExperssion():
    def __init__(self) -> None:
        self.condition = []     # conditions of the logical expression
        self.conclusion = []    # conclusions to be judged
        # Real names are mappings to simplified or anonymized representations of those symbols to make logical expressions more manageable or easier to process
        self.realname2symbol = []   # convert a, b, c... into real names in logical expressions
        self.symbol2realname = {}   # convert real names in logical expressions back to a, b, c...
        pass
    def addcondition(self, condition):      # condition and conclusion must either be propositions or symbols
        self.condition.append(condition)
        if (isinstance(condition, SymBol)):
            if (condition.name in self.realname2symbol):
                pass 
            else:
                self.realname2symbol.append(condition.name)
                self.symbol2realname[condition.name] = chr(len(self.realname2symbol) - 1 + ord('a'))
        else:
            if (condition.Sym1.name in self.realname2symbol):
                pass 
            else:
                self.realname2symbol.append(condition.Sym1.name)
                self.symbol2realname[condition.Sym1.name] = chr(len(self.realname2symbol) - 1 + ord('a'))
            
            if (condition.Sym2.name in self.realname2symbol):
                pass 
            else:
                self.realname2symbol.append(condition.Sym2.name)
                self.symbol2realname[condition.Sym2.name] = chr(len(self.realname2symbol) - 1 + ord('a'))
        
    def addconclusion(self, conclusion):
        self.conclusion.append(conclusion)
    def __str__(self):              # visualize expression
        string = "("
        for i in range(len(self.condition)):
            string += "(" + str(self.condition[i]) + ")"
            if (i != len(self.condition) - 1):
                string += " AND "
        string += ")-->("
        for i in range(len(self.conclusion)):
            string += "(" + str(self.conclusion[i]) + ")"
            if (i != len(self.conclusion) - 1):
                string += " AND "
        string += ")"
        return string
    def getlogicExp(self):
        
        string = "("
        for i in range(len(self.condition)):
            if (isinstance(self.condition[i], SymBol)):
                string += "(" + str(self.condition[i]).replace(self.condition[i].name ,self.symbol2realname[self.condition[i].name]).replace("NOT", "~") + ")"
            else:
                string +=  "(" + str(self.condition[i]).replace(self.condition[i].Sym1.name ,self.symbol2realname[self.condition[i].Sym1.name]).\
                    replace("NOT", "~").replace("AND", "&").replace(self.condition[i].Sym2.name ,self.symbol2realname[self.condition[i].Sym2.name]) + ")"
            if (i != len(self.condition) - 1):
                string += " & "
        string += ")-->("
        
        for i in range(len(self.conclusion)):
            if (isinstance(self.conclusion[i], SymBol)):
                string += "(" + str(self.conclusion[i]).replace(self.conclusion[i].name ,self.symbol2realname[self.conclusion[i].name]).replace("NOT", "~") + ")"
            else:
                string +=  "(" + str(self.conclusion[i]).replace(self.conclusion[i].Sym1.name ,self.symbol2realname[self.conclusion[i].Sym1.name]).\
                    replace("NOT", "~").replace("AND", "&").replace(self.conclusion[i].Sym2.name ,self.symbol2realname[self.conclusion[i].Sym2.name]) + ")"
            if (i != len(self.conclusion) - 1):
                string += " & "
        string += ")"
        return string
    def LogicJudge(self):
        string = self.getlogicExp()
        # print("The logical expression corresponding to the original statement is: ", string)
        logstr = Logic2algebra(string)
        # print("The Boolean expression corresponding to the logical expression is: ",logstr)
        symstr = Boolstr2symstr(logstr)
        res = BooleReduce(symstr)
        # print("The result of the input expression (1 for correct, others for incorrect): ", res)
        if (res == "1"):
            return True
        else:
            return False
        
    # Convert natural language variables into simple variables
    # Abstract away the details of what the symbols represent, focusing purely on the logical relationships
    # Simplify notation and make algorithms more efficient (solve logical problems faster and with less complexity)
    def GetSymbolTrans(self):
        return self.symbol2realname
        
def main():
    A = SymBol("People")
    B = SymBol("Die")
    C = SymBol("Socrates")

    condition1 = Proposition(A, B)
    condition2 = Proposition(C, A)

    conculusion = Proposition(C, B)
    LogicExp = LogicalExperssion()
    LogicExp.addcondition(condition1)
    LogicExp.addcondition(condition2)
    LogicExp.addconclusion(conculusion)

    print("The original statement is: ", LogicExp)
    print("Convert the original statement into a logical expression:",LogicExp.getlogicExp())
    print("The corresponding relationship between original language and logical expression symbols is:", LogicExp.GetSymbolTrans())
    print("The judgment result is:", LogicExp.LogicJudge())

if __name__ == '__main__':
    main()