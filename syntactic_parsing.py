import copy
import lexical_analyzer

# LR分析器实质上是一个带栈的确定有限自动机，其核心部分是一张分析表，包括两部分：
# （1）ACTION[s，a]动作表，规定当状态s面临输入符号a时，应采取什么动作（移进、归约、接受、 报错）
#       【也就是告诉我们当栈顶状态为s时，输入的符号是a时，我们应该采取什么操作：归约、移进还是报错】
# （2）GO[s，X]状态转换表规定了状态s面对文法符号X时，下一状态是什么。
#        【当归约完了后，要把规约后的非终结符压到栈里面的时候，跟新压入栈的这个非终结符所对应的状态是什么】
# 产生式
class Production:
    def __init__(self, left, right):
        self.left = left
        self.right = right


# LR(0)项目，即带圆点的产生式
# 每个项目的含义是：欲用产生式归约时，圆点前面的部分为已经识别了的句柄部分，圆点后面的部分为期望的后缀部分。
# left:产生式左部    right:右部    index:圆点坐标（在对应坐标字符的左侧）
class Item:
    def __init__(self, left, right, index):
        self.left = left
        self.right = right
        self.index = index

# 语法分析树的结点
class Node:
    def __init__(self, character, token=None):
        self.child = []
        self.character = character
        self.token = token

    def add_child(self, node):
        self.child.append(node)


# finished
# 打印树的所有结点到文件
def print_Node(node, write, h):
    for i in range(h):
        print("|\t", end="", file=write)
    print(node.character, file=write)
    for c in node.child:
        print_Node(c, write, h+1)


# finished
# 求两个FIRST或FOLLOW集X，Y的并集
# 若该并集比X大，则返回True，否则返回False
# 求FIRST集需要用到参数except_epsilon，指示是否需要去除{ε}
# F stands for the FIRST or FOLLOW set
# X and Y are both in (V U T)
def union_set(F, X, Y, flag_remove_epsilon):
    set_X = set(F[X])
    if Y == "ε":
        set_Y = set("ε")
    else:
        set_Y = set(F[Y])
    if flag_remove_epsilon:
        set_Y.discard("ε")
    size_origin = len(F[X])
    F[X] = list(set_X.union(set_Y))
    size_result = len(F[X])
    if size_result > size_origin:
        return True
    else:
        return False


# 求G的所有FIRST(s)，s∈(V U T)*，s = X1X2X3...Xn
# 如果之前没有记录过对应的FIRST(s)，就将其添加到FIRST集中
def get_FIRST_s(FIRST, s):
    # 如果s是单个非终结符或者终结符，则FIRST集中已经存在，直接返回即可
    if len(s) == 1:
        # α=ε的特殊情况，特殊处理
        if "ε" in s:
            FIRST["ε"] = ["ε"]
        return FIRST[s[0]]
    # 如果s是多个非终结符或终结符的集合，就开始运行算法求解FIRST(s)
    string_s = ""
    for X in s:
        string_s = string_s + X + " "
    string_s = string_s.strip()
    FIRST[string_s] = []

    flag_epsilon = False
    for X in s:
        flag_epsilon = False
        if "ε" in FIRST[X]:
            flag_epsilon = True
            union_set(FIRST, string_s, X, True)
        if not flag_epsilon:
            union_set(FIRST, string_s, X, True)
            break
    # 如果X1-Xn都能推出ε，就把ε也添加到FIRST中
    if flag_epsilon:
        union_set(FIRST, string_s, "ε", False)
    return FIRST[string_s]

#finished
# 对于文法G的任一符号串α=X1X2…Xn可按下列步骤构造其FIRST(α)集合：
# 1) 置FIRST(α)=φ
# 2) 将FIRST(X1)中的一切非ε符号加进FIRST(α)；
# 3) 若ε∈FIRST(X1)，将FIRST(X2)中的一切非ε符号加进FIRST(α)；
#    若ε∈FIRST(X1)和FIRST(X2)，将FIRST(X3)中的一切非ε符号加进FIRST(α)；依次类推。
#       //若该符号能推出ε则将下一个符号的FIRST集加入FIRST(α)，以此类推。
# 4)若对于一切1≤i≤n,ε∈FIRST(Xi)，则将ε符号加进FIRST(α)。
#       //若右侧符号串的每个符号都能推出ε，则α肯定能推出ε，所以将ε加进FIRST（α）。

# 求G的所有FIRST(X)，X∈(V U T)
def get_FIRST(G):
    # 用字典存储FIRST集，相当于一个Hash Table，提高查询效率，同时方便输出展示
    FIRST = {}

    # 去掉S'
    temp_V = set(G['V'])
    temp_V.discard(G['S'] + "'")

    for X in temp_V:
        FIRST[X] = []

    # for t, FIRST[t]=t
    for X in G['T']:
        FIRST[X] = [X]

    # step 1: if X -> t or X -> ε, append it to FIRST[X]
    for production in G['P']:
        X = production.left
        if ("ε" in production.right) and ("ε" not in FIRST[X]):
            FIRST[X].append("ε")
        if production.right[0] in G['T']:
            FIRST[X].append(production.right[0])

    # step 2: 对于右部所有非终结符Y，循环增加其FIRST集
    flag_set_change = True
    while flag_set_change:
        flag_set_change = False
        for production in G['P']:
            X = production.left
            Y = production.right
            # if (X->Y...∈P and Y∈V) then FIRST(X) ∪= (FIRST(Y)-{ε})
            if Y[0] in G['V']:
                flag_set_change = union_set(FIRST, X, Y[0], flag_remove_epsilon=True)

            # if (X->Y_1...Y_n∈P and Y_1...Y_{i-1}->ε) then for k=2 to i do (FIRST(X) ∪= (FIRST(Y_k)-{ε}))
            if len(Y) == 1:
                continue
            # 产生式右部全部都是非终结符
            else:
                flag_epsilon = False
                # 把Y的非终结符里能推导出ε的FIRST集去掉ε
                # 添加到FIRST(X)中
                for y in Y:
                    flag_epsilon = False
                    if "ε" in FIRST[y]:
                        flag_epsilon = True
                        flag_set_change = union_set(FIRST, X, Y[0], flag_remove_epsilon=True)

                    # 如果当前这个非终结符推不出ε
                    if not flag_epsilon:
                        # 若之后还有终结符，就再来最后一次，否则停止循环
                        flag_set_change = union_set(FIRST, X, Y[0], flag_remove_epsilon=True)
                        break

                # 如果右部每一个非终结符都能推出ε，FIRST(X)可以包含ε
                if flag_epsilon:
                    if union_set(FIRST, X, "ε", False):
                        flag_set_change = True
    return FIRST

#finished
# 1. 对于文法的开始符号S，置#于FOLLOW(S) 中;
# 2. 若Ａ→αBβ是一个产生式,则把(FIRST(β)-{ε})加至FOLLOW(B)中;
#    若β=>*ε (即ε in FIRST(β))，则把FOLLOW(A)加至FOLLOW(B)中。
#       //若B有可能是最后一个符号，则把FOLLOW(A)加至FOLLOW(B)中，否则把(FIRST(β)- {ε})加至FOLLOW(B)中。
# 反复使用上述规则，直到所求FOLLOW集不再增大为止。
# 注意: 在FOLLOW集合中无ε。
# 求G的所有FOLLOW(X)，X∈(V U T)
def get_FOLLOW(G):
    filename = '5_FIRST_and_FOLLOW.txt'
    write = open(filename, 'w', encoding='UTF-8')

    # 先获取FIRST集，并输出到文本文件
    FIRST = get_FIRST(G)
    print("FIRST:", file=write)
    keys = FIRST.keys()
    for k in keys:
        print(str(k) + ": " + str(FIRST[k]), file=write)

    # 初始化
    # 用字典存储FOLLOW集
    FOLLOW = {}
    # 去掉S'
    temp_V = set(G['V'])
    temp_V.discard(G['S'] + "'")
    for X in temp_V:
        FOLLOW[X] = []
    # 最后一步归约我们希望S后跟着$
    FOLLOW[G['S']].append("$")

    # A -> αBβ
    flag_set_change = True
    while flag_set_change:
        flag_set_change = False
        for production in G['P']:
            A = production.left
            Y = production.right
            for i in range(0, len(Y)):
                B = Y[i]
                # 如果B不是非终结符，则跳过直到找到非终结符
                if B not in G['V']:
                    continue
                # 判断B后面是否还有β
                if i == len(Y) - 1:
                    flag_set_change = union_set(FOLLOW, B, A, False)
                else:
                    beta = Y[i+1:]
                    FIRST_beta = get_FIRST_s(FIRST, beta)
                    # 若β=>*ε (即ε∈FIRST(β))，则把FOLLOW(A)加至FOLLOW(B)中。
                    #       //若B有可能是最后一个符号，则把FOLLOW(A)加至FOLLOW(B)中，否则把(FIRST(β)- {ε})加至FOLLOW(B)中。
                    # 反复使用上述规则，直到所求FOLLOW集不再增大为止。
                    # 如果ε∈FIRST(β)
                    if "ε" in FIRST_beta:
                        flag_set_change = union_set(FOLLOW, B, A, False)

                    set_B = set(FOLLOW[B])
                    set_beta = set(FIRST_beta)
                    set_beta.discard("ε")
                    size_og = len(FOLLOW[B])
                    FOLLOW[B] = list(set_B.union(set_beta))
                    size_res = len(FOLLOW[B])
                    if size_og < size_res:
                        flag_set_change = True
    # 输出FOLLOW至文件
    print("\nFOLLOW:", file=write)
    keys = FOLLOW.keys()
    for k in keys:
        print(str(k) + ": " + str(FOLLOW[k]), file=write)

    return FOLLOW

# finished
# 判断某个LR(0)项目是否在某个项目集中
def item_in_set(item, set):
    for i in set:
        if item.left == i.left and item.right == i.right and item.index == i.index:
            return True
    return False

# finished
#CLOSURE(I)是这样定义的：
#   首先I的项目都属于CLOSURE(I)；
#   如果A->α• Bβ,则左部为B的每个产生式中的形如B->·γ项目，也属于CLOSURE(I)；
# 求I的闭包
# PS:圆点在坐标对应字符左侧
def get_closure(G, I):
    J = copy.copy(I)
    for item in J:
        # 圆点到末尾，换下一个项目.
        if item.index >= len(item.right):
            continue
        B = item.right[item.index]
        if B in G['V']:
            for production in G['P']:
                if production.left == B:
                    temp = Item(production.left, production.right, 0)
                    if not item_in_set(temp, J):
                        J.append(temp)
    return J


# finished
# 项目集的转移函数
# 求出项目集I关于非终结符X的后继项目集
# GO(G,I，X)＝CLOSURE(J)
# 其中：I为包含某一项目的状态。X为一文法符号，X∈(V ∪ T)，
# J＝{任何形如 A→αX·β 的项目| A→α·Xβ属于I}
def GO(G, I, X):
    J = []
    for item in I:
        # 圆点到末尾，换下一个项目
        if item.index >= len(item.right):
            continue
        B = item.right[item.index]
        if B == X:
            if X in G['V'] or X in G['T']:
                J.append(Item(item.left, item.right, item.index + 1))
    return get_closure(G, J)

# 判断两个LR(0)项目集是否相等
def item_equal(a, b):
    if a.left == b.left and a.right == b.right and a.index == b.index:
        return True
    return False

# 判断两个项目集是否相等
def set_equal(A, B):
    n1 = len(A)
    n2 = len(B)
    if n1 != n2:
        return False
    for i in range(n1):
        if not item_equal(A[i], B[i]):
            return False
    return True

# 每个项目集对应一个DFA状态，它们的全体称为这个文法的项目集规范族
# 用闭包函数（CLOSURE）来求DFA一个状态的项目集
# I是拓广文法G的任意项目集：
# CLOSURE(I)是这样定义的：
#   首先I的项目都属于CLOSURE(I)；
#   如果A->α• Bβ,则左部为B的每个产生式中的形如B->·γ项目，也属于CLOSURE(I)；也就是找到对应确定状态自动机的所有边
# 输入文法G'，计算LR(0)项目集规范族C
def get_LR0_collection(G):
    C = []
    I = []
    I.append(Item(G['P'][0].left, G['P'][0].right, 0))
    C.append(get_closure(G, I))
    # everything in V or in T
    V_or_T = G['V'] + G['T']
    for I in C:
        for X in V_or_T:
            J = GO(G, I, X)
            # 如果J不为空集
            if len(J) > 0:
                # 判断J是否在C中
                flag = True
                for K in C:
                    if set_equal(J, K):
                        flag = False
                # 如果J不在C中，则将其添加到C中
                if flag:
                    C.append(J)

    # 输出LR0项目集规范族到文件
    filename = '4_Canonical_Collection_of_LR(0)_items.txt'
    write = open(filename, 'w', encoding='UTF-8')
    for i in range(len(C)):
        print("I(" + str(i) + "):", file=write)
        for item in C[i]:
            right = ""
            for i in range(0, len(item.right)):
                if i == item.index:
                    right += ". "
                right += item.right[i] + " "
            if item.index >= len(item.right):
                right += "."
            print(item.left + " -> " + right, file=write)
        print("", file=write)

    return C


# 令每个项目集Ik的下标k作为分析器的状态
# ACTION 表项和 GOTO表项可按如下方法构造：
#   若项目A ->α • aβ属于 Ik 且 GO (Ik, a)= Ij, 期望字符a 为终结符，则置ACTION[k, a] =sj (j表示新状态Ij);
#       如果圆点不在项目k最后且圆点后的期待字符a为终结符，则ACTION[k, a] =sj (j表示新状态Ij)；
#   若项目A ->α •属于Ik, 那么对任何终结符a, 置ACTION[k, a]=rj；其中，假定A->α为文法G 的第j个产生式；【对k到a进行归约】
#       如果圆点不在项目k最后且圆点后的期待字符A为非终结符，则GOTO(k, A)=j (j表示文法中第j个产生式)；
#   若项目S’ ->S • 属于Ik, 则置ACTION[k, #]为“acc”;【单词处理完毕】
#       如果圆点在项目k最后且k不是S’ ->S，那么对所有终结符a，ACTION[k, a]=rj (j表示文法中第j个产生式)；
#   若项目A ->α • Aβ属于 Ik，且GO (Ik, A)= Ij,期望字符 A为非终结符，则置GOTO(k, A)=j (j表示文法中第j个产生式);
#       如果圆点在项目k最后且k是S’ ->S，则ACTION[k, #]为“acc”;
# 分析表中凡不能用上述规则填入信息的空白格均置上“出错标志”

# 构造SLR(1)分析表的方法:
# 1、把G扩广成G’
# 2、对G’构造：得到LR(0)项目集规范族C；活前缀识别自动机的状态转换函数GO
# 3、使用C和GOTO，构造SLR分析表：构造action和goto子表：
#   若项目A ->α • aβ属于 Ik 且 GO (Ik, a)= Ij,期望字符a为终结符，则置ACTION[k, a] =sj (j表示新状态Ij);
#   若项目A ->α • Aβ属于 Ik，且GOTO (Ik, A)= Ij,期望字符 A为非终结符，则置GOTO(k, A)=j (j表示文法中第j个产生式);
#   若项目A ->α •属于Ik, 那么对任何终结符a，当满足a属于follow(A)时， 置ACTION[k, a]=rj；其中，假定A->α为文法G 的第j个产生式；
#   若项目S’ ->S • 属于Ik, 则置ACTION[k, #]=“acc”;
#   分析表中凡不能用上述规则填入信息的空白格均置上“出错标志”
# 输入文法G，获取SLR(1)分析表
def get_SLR1_table(G):
    # 输入的G是非拓广文法，先求FOLLOW集
    FOLLOW = get_FOLLOW(G)

    # 拓展文法G生成拓广文法G‘
    G['P'].insert(0, Production(G['S'] + "'", [G['S']]))
    G['V'].insert(0, G['S'] + "'")
    # 输入文法G'，得到LR(0)项目集规范族C
    C = get_LR0_collection(G)

    # action和goto表的初始化, row is a dic
    n = len(C)
    row = {}
    for t in G['T']:
        row[t] = ""
    row["$"] = ""
    action = []
    for i in range(n):
        action.append(copy.copy(row))

    temp_V = set(G['V'])
    temp_V.discard(G['S'] + "'")
    row = {}
    for v in temp_V:
        row[v] = ""
    goto = []
    for i in range(n):
        goto.append(copy.copy(row))

    for k in range(n):
        I = C[k]
        for item in I:
            # 圆点不在右部表达式的最右侧，即还不需要归约
            if item.index < len(item.right):
                character = item.right[item.index]
                # 找出满足GO(I, character)=C[j]的j
                for j in range(n):
                    if set_equal(GO(G, I, character), C[j]):
                        # 如果character是终结符
                        if character in G['T']:
                            # 在action表里添加状态转移以及当前符号压入栈的提示
                            action[k][character] = "S" + str(j)
                        # 如果是非终结符
                        else:
                            # 在goto表里添加状态转移提示
                            goto[k][character] = str(j)
                        break
            # 圆点在右部表达式的最右侧，即需要归约
            else:
                # 如果该表达式是S'->S，则在action表里添加acc
                if item.left == G['S'] + "'":
                    action[k]["$"] = "acc"
                    continue
                # 否则，找到P中对应的产生式序号
                m = len(G['P'])
                for j in range(1, m):
                    if G['P'][j].left == item.left and G['P'][j].right == item.right:
                        FOLLOW_A = FOLLOW[item.left]
                        for t in G['T']:
                            if t in FOLLOW_A:
                                action[k][t] = "r" + str(j)
                        if "$" in FOLLOW_A:
                            action[k]["$"] = "r" + str(j)
                        break

    # 输出action和goto表到文件
    filename = '6_SLR(1)_Parsing_Table.txt'
    write = open(filename, 'w', encoding='UTF-8')
    print("action:", file=write)
    print("[", end='', file=write)
    i = 0
    T = G['T']
    for t in T:
        print(str(i) + ": " + str(t), end=", ", file=write)
        i += 1
    print("#]", file=write)
    i = 0
    for row in action:
        print(str(i) + str(row), file=write)
        i += 1

    print("", file=write)
    print("goto:", file=write)
    V = G['V']
    for i in range(1, len(V)):
        print(str(V[i]), end="  ", file=write)
    i = 0
    for row in goto:
        print(str(i) + str(row), file=write)
        i += 1

    return action, goto



# action：s shift 移进符号入栈 状态入栈；
#       r reduce 归约，状态出栈 符号出栈，归约后入栈，查goto表
# goto: 新状态入栈
# 输入文法G、SLR(1)的action与goto分析表、词法分析得到的token串，输出LR分析结果以及对应的语法分析树至文件
def LR_parser(G, action, goto, tokens):
    filename = '7_LR_parser_Analysis.txt'
    write = open(filename, 'w', encoding='UTF-8')

    # 结点栈
    stack_node = []

    # 状态栈
    stack_state = [0]
    # 符号栈
    stack_character = ["$"]
    # 输入缓冲区
    buffer = []
    for t in tokens:
        if t[1] == "IDENTIFIER":
            buffer.append("id")

        elif t[1] == "FLOAT" or t[1] == "INT":
            buffer.append("digit")
        else:
            buffer.append(str(t[0]))
    buffer.append("$")
    # print("buffer = " + str(buffer))
    # 用于记录输入缓冲区当前下标的变量
    ip = 0
    while True:
        print("", file=write)
        print("State stack: " + str(stack_state), file=write)
        print("Value stack: " + str(stack_character), file=write)
        if ip >= len(buffer):
            break

        # 获得栈顶状态S以及ip指向的符号a
        S = stack_state[len(stack_state)-1]
        a = buffer[ip]

        print("Input buffer: ", end="", file=write)
        input = buffer[ip:]
        for c in input:
            print(c, end=" ", file=write)
        print("", file=write)

        # 获取SLR(1)分析表中对应的字符串
        string = action[S][a]
        print("SLR(1) table: " + string, file=write)
        print("action: ", end="", file=write)
        # 出错
        if string == '':
            print("SLR(1) parsing FAILED.")
            print("Parsing failed.", file=write)
            return
        # 需要转移至状态i，并且把a压入栈中
        elif string[0] == 'S':
            i = int(string[1:])
            print("Shift state: %s，input character: %s" % (str(i), a), file=write)
            stack_character.append(a)
            stack_state.append(i)

            stack_node.append(Node(a, tokens[ip]))  # 结点入栈
            ip = ip + 1

        # 需要根据G中第k条产生式归约，两个栈各弹出n个符号，最后再查询goto表将新的状态压入状态栈
        elif string[0] == 'r':
            k = int(string[1:])
            n = len(G['P'][k].right)
            print("Reduce with No.%s production: " % str(k) + str(G['P'][k].right) + " -> " + G['P'][k].left, end="", file=write)
            A = G['P'][k].left

            # 归约以后弹出n个符号
            stack_state = stack_state[0: len(stack_state)-n]
            stack_character = stack_character[0: len(stack_character)-n]

            # 查询goto表，将新的状态压入状态栈
            S = stack_state[len(stack_state) - 1]
            stack_state.append(int(goto[S][A]))
            print(", push state %s into state stack" % str(goto[S][A]), file=write)
            stack_character.append(A)

            # 结点栈弹出n个结点，并生成它们的父结点，再将父结点压入栈
            child_nodes = stack_node[len(stack_node) - n:]
            stack_node = stack_node[0: len(stack_node) - n]
            father = Node(A)
            for c in child_nodes:
                father.add_child(c)
            stack_node.append(father)

        # 分析成功
        elif string == "acc":
            print("Successfully finished SLR(1) parsing，syntactic parser finished work.")
            print("Parsing succeeded.", file=write)

            filename = '8_Parse_Tree.txt'
            write = open(filename, 'w', encoding='UTF-8')
            root = stack_node[0]
            print_Node(stack_node[0], write, 0)
            return root

# finished
# 读取表达式，自动生成集合V,T,P,S; 并且自动生成文法G=(V, T, P, S)
# V:非终结符,   T:终结符/ε,    P:产生式   S:开始符号
# 输入的表达式必须满足:1.开始符号S是第一条表达式的左部 2.单词用空格隔开 3.出现在左侧的都是非终结符V (CFG)
def get_G(filename):
    # filename是表达式所在文件名,按行读入
    fp_read = open(filename, 'r', encoding='UTF-8')
    lines = fp_read.readlines()

    # 生成的文法G写入文本文件
    result_filename = '3_CFG.txt'
    write = open(result_filename, 'w', encoding='UTF-8')

    # V:非终结符,   T:终结符/ε,    P:产生式
    V = []
    T = []
    P = []

    # Production
    print("P : ", file=write)
    length = len(lines)
    for i in range(length):
        # delete \n
        lines[i] = lines[i].replace('\n', '')
        if not lines[i]:
            continue
        # remove comments which are sentences including with '#'
        if "#" in lines[i]:
            continue

        print(lines[i], file=write)
        p = lines[i].index("->")
        # left part is a single word which is before '->'
        left = lines[i][0:p-1]
        # right part consists of multiple words split with space
        right = lines[i][p+3:]
        right = right.split(" ")

        P.append(Production(left, right))

        # V consists of every left part of P
        if left not in V:
            V.append(left)
    # T consists of words in right parts which are not in V or T
    for i in range(len(P)):
        right = P[i].right
        for c in right:
            if (c not in V) and (c not in T) and (c != 'ε'):
                T.append(c)
    # S is the first Production's left part
    S = P[0].left

    print("", file=write)
    print("V : ", end="", file=write)
    for v in V:
        print(str(v), end="  ", file=write)
    print("", file=write)
    print("T : ", end="", file=write)
    for t in T:
        print(str(t), end="  ", file=write)
    print("", file=write)
    print("S : " + str(S), file=write)

    # 用字典存储G
    G = {'V': V, 'T': T, 'P': P, 'S': S}
    return G


def main():
    source_code_name='0_source_code.txt'
    # invoke lexer to get the sequence of tokens
    tokens = lexical_analyzer.lex(source_code_name)

    # to get the grammar G.
    product_filename = "2_Product.txt"
    G = get_G(product_filename)

    # to get the SLR(1) parsing table
    action, goto = get_SLR1_table(G)

    # using simple LR parser with  G and SLR(1) parsing tables to analyze tokens
    LR_parser(G, action, goto, tokens)


if __name__ == '__main__':
    main()
