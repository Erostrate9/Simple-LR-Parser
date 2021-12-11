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
                tokens.append([line[i], "分界符"])
                i += 1
                continue

            # 多符号运算符
            if line[i] + line[i + 1] in operators:
                temp = line[i] + line[i + 1]
                i += 2
                tokens.append([temp, "运算符"])
                continue

            # 当前字符在运算符集中
            if line[i] in operators:
                tokens.append([line[i], "运算符"])
                i += 1
                continue
            # 当前字符为数字（包括整数和浮点数）
            if line[i].isdigit():
                temp = ""
                # 多个数字
                while line[i].isdigit() or line[i] == '.':
                    temp += line[i]
                    # print("temp = " + temp)
                    i += 1
                    if i > len(line) - 1:
                        break

                # 防止有以数字开头的标识符等非法
                if line[i].isdigit() or line[i] in operators or line[i] in delimiters or line[i] == ' ':

                    # 浮点数
                    if temp.find('.') != -1:
                        # 防止有多个点的非法浮点数
                        index = temp.find('.')
                        if temp[index:].find('.') > 0:
                            # print('(%s, %s, error)' % (str(row), temp), file=fp_write)
                            tokens.append([temp, "错误"])
                        else:
                            # print('(%s, %s, float)' % (str(row), temp), file=fp_write)

                            tokens.append([temp, "浮点数"])

                    else:
                        # print('(%s, %s, integer)' % (str(row), temp), file=fp_write)

                        tokens.append([temp, "整数"])

                else:
                    # print('(%s, %s, error)' % (str(row), temp), file=fp_write)
                    tokens.append([temp, "错误"])

                continue
            # 当前字符为字符串
            if line[i] == '\"' or line[i] == '\'':
                # print("line[i] == '\"' or line[i] == '\''")
                # print('(%s, %s, delimiters)' % (str(row), line[i]), file=fp_write)
                mark = line[i]
                # print('mark = ' + mark)
                temp = ""
                i += 1
                while line[i] != mark:
                    temp += line[i]
                    # print("temp = " + temp)
                    i += 1
                    if i == len(line):
                        i -= 1
                        print("break = " + temp)
                        break
                # print("temp = " + temp + " line[i] = "+line[i])

                # 找到了另一端
                if line[i] == mark:
                    # print('(%s, %s, string)' % (str(row), temp), file=fp_write)
                    # print('(%s, %s, delimiters)' % (str(row), line[i]), file=fp_write)

                    tokens.append([temp, "字符串"])
                    tokens.append([line[i], "界符"])

                # 没找到另一端
                else:
                    # print('(%s, %s, error)' % (str(row), temp), file=fp_write)
                    tokens.append([temp, "错误"])
                i += 1
                continue

            # 当前字符为关键词或标识符
            # 先获取该关键词或标识符
            temp = ""
            while True:
                if i > len(line) - 1 or line[i] == ' ' or line[i] in operators or line[i] in delimiters:
                    break
                else:
                    temp += line[i]
                i += 1
            i -= 1
            # print("temp = " + str(temp))
            # print("after line[i] = " + line[i])
            # 再判断
            # 当前字符在关键词集中
            if temp in keywords:
                # print('(%s, %s, keywords)' % (str(row), temp), file=fp_write)

                tokens.append([temp, "关键词"])

            # 当前字符可能是标识符（额外判断是否非法）
            else:
                if not temp[0].isalpha():
                    # print('(%s, %s, error)' % (str(row), temp), file=fp_write)
                    tokens.append([temp, "错误"])
                else:
                    # print('(%s, %s, identifier)' % (str(row), temp), file=fp_write)
                    tokens.append([temp, "标识符"])

            i += 1
        row += 1

    result_filename = '1_tokens.txt'
    write = open(result_filename, 'w', encoding='UTF-8')
    for t in tokens:
        print('(%s, %s)' % (str(t[0]), str(t[1])), file=write)
    print("已获取tokens序列，词法分析部分结束")

    return tokens


def main():
    # 读入源代码文件作为字符流
    source_filename = '0_source_code.txt'
    # 获得对应单词序列并打印
    tokens = lex(source_filename)
    print(tokens)

# if __name__ == '__main__':
#     main()
