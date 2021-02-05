import argparse

def ParseKey(memoryReadFile):
    key = "0x"
    with open(memoryReadFile, 'r') as fp:
        for line in fp:
            lineArray = line.strip('\n').split(" ")
            for segmentNum in range(1, len(lineArray)):
                key = key + lineArray[segmentNum].replace("0x", "")
    return key

if __name__ == "__main__":
    CLIParser = argparse.ArgumentParser()
    CLIParser.add_argument("-i", "--input", help = "key file output by terminal", default = "resources/memoryRead.txt")
    CLIParser.add_argument("-o", "--output", help = "file to store parsed key", default = "resources/key.txt")
    args = CLIParser.parse_args()
    key = ParseKey(args.input)
    
    with open(args.output, 'w') as fp:
        fp.write(key)

# python3 utils/KeyParser.py -i resources/memoryRead.txt -o resources/key.txt
