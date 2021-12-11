# 解释:
# 读入：0_source_code.txt
# 输出：1_tokens.txt

# 词法分析器的生成器较难控制细节，这里采用手工编码实现法
# 通过词法规则的描述，画出相关的有穷状态自动机
# 最后逐个字符读出预处理后的源代码

# 分析基本语句(包括：函数定义，变量说明，赋值，循环，分支)
# 处理，关键词、运算符、界符、数字、字符串、标识符、非法标识符

def lex(source_filename):

    # 关键词
    keywords = ['if', 'else', 'while', 'return', 'int', 'float', 'double', 'true', 'false']

    # 运算符
    operators = [
        # 算术运算符
        '+', '-', '*', '/',
        # 关系运算符
        '==', '!=', '>', '<', '>=', '<=',
        # 逻辑运算符
        '&&', '||', '!',
        # 赋值运算符
        '='
    ]
    # 分界符
    delimiters = ['{', '}', '(', ')', ',', ';']
    # 用tokens列表存储读到的单词
    tokens = []
    # 打开源文件
    fp_read = open(source_filename, 'r')
    # 按行读取文本文件
    lines = fp_read.readlines()
    # to save the number of lines
    length = len(lines)
    # 预处理:删去不影响语义的制表符/换行符/空格
    for i in range(length):
        # to delete redundant tab
        lines[i] = lines[i].replace('\t', ' ')
        # to delete redundant LF
        lines[i] = lines[i].replace('\n', '')
        # to delete redundant space
        lines[i] = lines[i].strip()
    # 'row' stands for the index of lines
    # 'i' stands for the index of characters for each line
    row = 0
    while row < len(lines):
        # read the row th line of source_file
        line = lines[row]
        i = 0

        while i < len(line):
            # Space
            # 当前字符为空格，跳过该字符
            if line[i] == ' ':
                i += 1
                continue

            # Single-line Comments
            # 当前字符为单行注释，跳过该行
            if line[i] == '/' and line[i + 1] == '/':
                break

            # Multi-line Comments
            # 当前字符为多行注释，记录注释行数并跳过这些行
            if line[i] == '/' and line[i + 1] == '*':
                index = line.find('*/')
                # if didn't find the end of comments, goto next line
                while index == -1:
                    row += 1
                    line = lines[row]
                    index = line.find('*/')
                # if have found the end of the comments, continue to
                # read the rest of characters
                i = index + 2
                continue

            # Delimiters
            # 当前字符在分界符集中
            if line[i] in delimiters:
                tokens.append([line[i], "DELIMITER"])
                i += 1
                continue

            # 先判断多符号运算符再判断单符号运算符，避免提取的是前缀
            # multi-character operators
            # 多符号运算符
            if i<len(line)-1 and line[i] + line[i + 1] in operators:
                temp = line[i] + line[i + 1]
                i += 2
                tokens.append([temp, "OPERATOR"])
                continue

            # single-character operators
            # 当前字符在运算符集中
            if line[i] in operators:
                tokens.append([line[i], "OPERATOR"])
                i += 1
                continue

            # number (including int and float)
            # 当前字符为数字（包括整数和浮点数）
            if line[i].isdigit():
                temp = ""
                # 读取一个由若干个数字或点组成的串
                while line[i].isdigit() or line[i] == '.':
                    temp += line[i]
                    i += 1
                    # reach the end of line
                    if i > len(line) - 1:
                        break

                # 防止几种非法情况的出现：
                # 1. 数字开头的标识符
                # 2. 有多个点的非法浮点数

                if (i > len(line) - 1) or (line[i] in operators) or (line[i] in delimiters) or line[i] == ' ':

                    # 浮点数
                    if temp.find('.') != -1:
                        # 有多个点的浮点数非法
                        index = temp.find('.')
                        if temp[index:].find('.') > 0:
                            tokens.append([temp, "ERROR"])
                            print('lexical analysis found error.')
                        else:
                            tokens.append([temp, "FLOAT"])

                    else:
                        tokens.append([temp, "INT"])
                # numbers can only be followed by operators, delimiters or space.
                else:
                    tokens.append([temp, "ERROR"])
                    print('lexical analysis found error.')
                continue

            # when there is a ' or ", the following characters could be STRING
            if line[i] == '\"' or line[i] == '\'':
                mark = line[i]
                temp = ""
                i += 1
                # trying to match another mark
                while line[i] != mark:
                    temp += line[i]
                    i += 1
                    # when it reaches the end of line, rollback and make decision
                    if i == len(line):
                        i -= 1
                        break
                # if it finds another mark
                if line[i] == mark:
                    tokens.append([temp, "STRING"])
                    tokens.append([line[i], "DELIMITER"])

                # 为了简单起见，表达式不允许跨行存在
                # 没找到另一端
                else:
                    tokens.append([temp, "ERROR"])
                    print('lexical analysis found error.')
                i += 1
                continue

            # 当前字符为关键词或标识符
            # 先获取该关键词或标识符
            temp = ""
            while (i <= len(line) - 1) \
                    and (line[i] != ' ') \
                    and (line[i] not in operators) \
                    and (line[i] not in delimiters):
                temp += line[i]
                i += 1
            # 再判断
            i -= 1

            # if 在关键词集中
            if temp in keywords:
                tokens.append([temp, "KEYWORDS"])

            # 可能是标识符, 判断是否非法
            elif not temp[0].isalpha():
                tokens.append([temp, "ERROR"])
                print('lexical analysis found error.')
            else:
                tokens.append([temp, "IDENTIFIER"])

            i += 1
        row += 1
    # write the sequence of tokens into text file
    result_filename = '1_tokens.txt'
    write = open(result_filename, 'w', encoding='UTF-8')
    for t in tokens:
        print('(%s, %s)' % (str(t[0]), str(t[1])), file=write)
    print("Successfully got the sequence of tokens，lexical analysis has been finished.")

    return tokens


def main():
    # 读入源代码文件作为字符流
    source_filename = '0_source_code.txt'
    # 获得对应单词序列并打印
    tokens = lex(source_filename)
    print(tokens)

# if __name__ == '__main__':
#     main()
